import os
import re
import logging

from functools import lru_cache
from publicsuffixlist import PublicSuffixList
from rapidfuzz.distance import DamerauLevenshtein
from typing import Optional


class EmailTypoFixer:
    """
    A class to normalize and fix common typos in email addresses.
    TLD (Top-Level Domain) suffixes are validated against a Public Suffix List,
    and common domain typos are corrected using a `domain_typos` dictionary.

    This includes:
    - Lowercasing
    - Removing invalid characters
    - Ensuring a single '@' and at least one '.' after '@'
    - Fixing TLD (Top-Level Domain) typos
    - Fixing common domain name typos

    Attributes:
        max_distance: Maximum allowed distance for typo correction.
        psl: Instance of PublicSuffixList or None.
        valid_suffixes: Set of valid public suffixes or None.
        domain_typos: Mapping of common domain names (not suffixes) typos to corrections.
        logger: Logger instance.
    """

    def __init__(self, max_distance: int = 1, domain_typos: dict[str, str] | None = None,
                 common_tlds: list[str] | None = None, logger: logging.Logger | None = None) -> None:
        """
        Initialize the EmailTypoFixer.

        Args:
            max_distance: Maximum allowed distance for typo correction.
            typo_domains: Optional dictionary of domain typo corrections.
            common_tlds: Optional list of common TLDs to prefer in case of tie.
            logger: Optional logger instance.
        """
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(f"{__name__}.EmailTypoFixer")
            self.logger.addHandler(logging.NullHandler())
        self.max_distance = max_distance
        self.psl = None
        self.valid_suffixes = None
        self.domain_typos = domain_typos or {
            'gamil': 'gmail',
            'gmial': 'gmail',
            'gnail': 'gmail',
            'gmaill': 'gmail',
            'gmaul': 'gmail',
            'hotmal': 'hotmail',
            'hotmial': 'hotmail',
            'hotmsil': 'hotmail',
            'homtail': 'hotmail',
            'hotmaill': 'hotmail',
            'outlok': 'outlook',
            'outllok': 'outlook',
            'outlokk': 'outlook',
            'oul': 'uol',
            'uoll': 'uol',
            'uoo': 'uol',
            'yahho': 'yahoo',
            'yaho': 'yahoo',
            'yahoo': 'yahoo',
        }

        self.common_tlds = common_tlds or [
            "com", "net", "org", "edu", "gov", "mil", "br",
            "com.br", "net.br", "org.br", "edu.br", "gov.br", "mil.br"
        ]
        self.provider_domain_corrections = {
            'gmail.com.br': 'gmail.com',
            'uol.com': 'uol.com.br',
            # add more as needed
        }

    def _init_psl_and_suffixes(self) -> None:
        """
        Initialize the PublicSuffixList and fetch valid suffixes by parsing the .dat file.
        """
        if self.psl is None:
            try:
                self.psl = PublicSuffixList()
            except Exception as e:
                self.logger.error(f"Failed to initialize PublicSuffixList: {e}")
                raise ValueError("Could not initialize public suffix list")

        # Find the .dat file in the installed package
        try:
            import publicsuffixlist
            dat_path = os.path.join(os.path.dirname(publicsuffixlist.__file__), "public_suffix_list.dat")
            suffixes = set()
            with open(dat_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    # Remove wildcards and exceptions
                    if line.startswith("!"):
                        line = line[1:]
                    if line.startswith("*."):
                        line = line[2:]
                    suffixes.add(line)
            self.valid_suffixes = suffixes
        except Exception as e:
            self.logger.error(f"Failed to parse public_suffix_list.dat: {e}")
            raise ValueError("Could not parse public suffix list file")

    @lru_cache(maxsize=4096)
    def _fix_extension_typo_cached(self, domain: str, max_distance: int) -> str:
        # Ensure suffixes are initialized
        if self.valid_suffixes is None:
            self._init_psl_and_suffixes()
        """
        Fix typos in the domain extension using Levenshtein distance against PublicSuffixList.

        Args:
            domain: The domain part of the email.
            max_distance: Maximum allowed distance for typo correction.

        Returns:
            The domain with corrected extension if a close match is found.
        """
        assert self.valid_suffixes is not None, "valid_suffixes must be initialized"

        for i in range(1, min(4, len(domain.split('.')))):
            parts = domain.rsplit('.', i)

            if len(parts) < 2:
                continue
            ext_candidate = '.'.join(parts[-i:])
            best_matches = []
            best_distance = max_distance + 1

            for suffix in self.valid_suffixes:
                dist = DamerauLevenshtein.distance(ext_candidate, suffix)
                if dist < best_distance:
                    best_distance = dist
                    best_matches = [suffix]
                elif dist == best_distance:
                    best_matches.append(suffix)

            if best_matches and best_distance <= max_distance:
                # Prefer a common TLD if available
                preferred = None
                for tld in self.common_tlds:
                    if tld in best_matches:
                        preferred = tld
                        break
                best_match = preferred if preferred is not None else best_matches[0]
                domain_fixed = '.'.join(parts[:-i] + [best_match])
                if ext_candidate != best_match:
                    self.logger.debug(f"Fixed extension typo: '{ext_candidate}' -> '{best_match}' in domain '{domain}'")
                return domain_fixed

        return domain

    def fix_extension_typo(self, domain: str) -> str:
        """
        Public method to fix typos in the domain extension or TLD (Top-Level Domain).
        Fix typos in the domain extension using Levenshtein distance against PublicSuffixList.

        Args:
            domain: The domain name part of the email.

        Returns:
            The domain with corrected extension if a close match is found.
        """
        return self._fix_extension_typo_cached(domain, self.max_distance)

    def normalize(self, email: str, fix_tld_co: Optional[bool] = True) -> str:
        """
        Normalize and fix common issues in an email address string.

        This includes:
            - Lowercasing
            - Removing invalid characters
            - Ensuring a single '@' and at least one '.' after '@'
            - Fixing extension typos using PublicSuffixList and Levenshtein distance
            - Fixing common domain typos using default domain_typos dictitonary

        Args:
            email: The email address to normalize.

        Returns:
            The normalized and corrected email address.
            The original email if it cannot be fixed.

        Raises:
            ValueError: If the email is not a string.
            ValueError: If the PublicSuffixList cannot be initialized or parsed.
        """

        if not isinstance(email, str):
            msg = f"Email must be a string: {email}"
            self.logger.error(msg)
            raise ValueError(msg)

        # If the string contains known separators (e.g., ' e ', ' / '), split and take the first part
        # This is before any normalization, to avoid breaking the separator
        for sep in [";", ",", "/", " e ", " and "]:
            if sep in email:
                email = email.split(sep, 1)[0]
                break

        # Lowercase and strip
        email = email.strip().lower()

        # Remove spaces and invalid characters (allow a-z, 0-9, @, ., _, -, +)
        email = re.sub(r'[^a-z0-9@._\-+]', '', email)

        # Replace consecutive dots with a single dot
        email = re.sub(r'\.+', '.', email)

        # Replace consecutive '@' with a single '@'
        email = re.sub(r'@+', '@', email)

        # Fix double '@gmail.com@gmail.com' typo
        email = email.replace('@gmail.com@gmail.com', '@gmail.com')

        # Check for @ and at least one . after @
        if '@' not in email or email.count('@') != 1:
            msg = f"Invalid email, missing or too many '@': {email}"
            self.logger.debug(msg)
            return email  # Return the original email if it cannot be fixed

        # Extract local, domain, extension, and country parts
        local, domain = email.split('@', 1)
        if not local or not domain:
            msg = f"Invalid email, missing local or domain part: {email}"
            self.logger.debug(msg)
            return email  # Return the original email if it cannot be fixed

        # Ensure at least one . in domain
        if '.' not in domain:
            self.logger.debug(f"Invalid email, missing '.' in domain: {email}; defaulting to '.com.br'")
            domain = domain + '.com.br'  # Default to .com.br if no dot is present

        # Optionally skip TLD correction for .co domains if requested
        if domain.endswith('.co') and not fix_tld_co:
            pass
        else:
            # Fix extension typos using Damerau-Levenshtein distance against all valid public suffixes
            domain = self.fix_extension_typo(domain)

        # Use publicsuffixlist to split domain into domain_name and extension (public suffix)
        public_suffix = ''

        # Call publicsuffixlist with error handling
        assert self.psl is not None, "psl must be initialized"
        try:
            public_suffix = self.psl.publicsuffix(domain)
        except Exception as e:
            self.logger.error(f"Error using publicsuffixlist: {e}")

        if public_suffix and domain.endswith(public_suffix):
            # Remove the public suffix from the end to get the domain_name
            domain_name = domain[:-(len(public_suffix) + 1)]  # +1 for the dot
            extension = public_suffix
            if not domain_name:
                # e.g. gmail.com, domain_name would be empty
                domain_name = domain[:-len(public_suffix)-1] if len(domain) > len(public_suffix)+1 else ''
        else:
            domain_name = domain
            extension = ''

        # Fix domain_name typos using regex
        for typo, correct in self.domain_typos.items():
            # Replace only if typo is a full word (domain part)
            pattern = r'\b' + re.escape(typo) + r'\b'
            new_domain_name = re.sub(pattern, correct, domain_name)
            if new_domain_name != domain_name:
                self.logger.debug(f"Fixed domain typo: '{domain_name}' -> '{new_domain_name}'")
            domain_name = new_domain_name

        # Recombine
        domain = f"{domain_name}.{extension}" if extension else domain_name

        # Correct common provider domains (e.g., gmail.com.br -> gmail.com)

        if domain in self.provider_domain_corrections:
            domain = self.provider_domain_corrections[domain]

        fixed_email = f"{local}@{domain}"

        # Final validation
        email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_regex, fixed_email):
            msg = f"Invalid email after fix: {fixed_email}"
            self.logger.debug(msg)
            return email  # Return the original email if it cannot be fixed

        return fixed_email


# For backward compatibility: function interface

_default_normalizer = EmailTypoFixer()


def normalize_email(email: str, fix_tld_co: Optional[bool] = True) -> str:
    """
    Normalize and fix common issues in an email address string.

    This is a convenience function that uses a default EmailTypoFixer instance.

    Args:
        email: The email address to normalize.

    Returns:
        The normalized and corrected email address.

    Raises:
        ValueError: If the email cannot be normalized or is invalid.
    """
    return _default_normalizer.normalize(email, fix_tld_co)


# Public API
__all__ = ["EmailTypoFixer", "normalize_email"]
