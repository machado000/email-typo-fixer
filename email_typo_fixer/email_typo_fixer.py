

import os
import rapidfuzz
import re
import logging

from functools import lru_cache
from publicsuffixlist import PublicSuffixList
from . import logger as package_logger


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

    def __init__(self, max_distance: int = 2, domain_typos: dict[str, str] | None = None,
                 logger: logging.Logger | None = None) -> None:
        """
        Initialize the EmailTypoFixer.

        Args:
            max_distance: Maximum allowed distance for typo correction.
            typo_domains: Optional dictionary of domain typo corrections.
            logger: Optional logger instance.
        """
        self.logger = logger or package_logger
        self.logger.addHandler(logging.NullHandler())
        self.max_distance = max_distance
        self.psl = None
        self.valid_suffixes = None
        self.domain_typos = domain_typos or {
            'gamil': 'gmail',
            'gmial': 'gmail',
            'gnail': 'gmail',
            'gmaill': 'gmail',
            'hotmal': 'hotmail',
            'hotmial': 'hotmail',
            'homtail': 'hotmail',
            'hotmaill': 'hotmail',
            'outlok': 'outlook',
            'outllok': 'outlook',
            'outlokk': 'outlook',
            'oul': 'uol',
            'uoll': 'uol',
            'uoo': 'uol',
            'yaho': 'yahoo',
            'yahho': 'yahoo',
        }
        self._init_psl_and_suffixes()

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
            best_match = None
            best_distance = max_distance + 1

            for suffix in self.valid_suffixes:
                dist = rapidfuzz.distance.Levenshtein.distance(ext_candidate, suffix)
                if dist < best_distance:
                    best_distance = dist
                    best_match = suffix

            if best_match and best_distance <= max_distance:
                domain_fixed = '.'.join(parts[:-i] + [best_match])
                self.logger.info(f"Fixed extension typo: '{ext_candidate}' -> '{best_match}' in domain '{domain}'")

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

    def normalize(self, email: str) -> str:
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

        Raises:
            ValueError: If the email cannot be normalized or is invalid.
        """
        if not isinstance(email, str):
            msg = f"Email must be a string: {email}"
            self.logger.error(msg)
            raise ValueError(msg)

        # Lowercase and strip
        email = email.strip().lower()

        # Remove spaces and invalid characters (allow a-z, 0-9, @, ., _, -, +)
        email = re.sub(r'[^a-z0-9@._\-+]', '', email)

        # Replace consecutive dots with a single dot
        email = re.sub(r'\.+', '.', email)

        # Replace consecutive '@' with a single '@'
        email = re.sub(r'@+', '@', email)

        # Check for @ and at least one . after @
        if '@' not in email or email.count('@') != 1:
            msg = f"Invalid email, missing or too many '@': {email}"
            self.logger.warning(msg)
            raise ValueError(msg)

        # Extract local, domain, extension, and country parts
        local, domain = email.split('@', 1)
        if not local or not domain:
            msg = f"Invalid email, missing local or domain part: {email}"
            self.logger.warning(msg)
            raise ValueError(msg)

        # Ensure at least one . in domain
        if '.' not in domain:
            msg = f"Invalid email, missing '.' in domain: {email}"
            self.logger.warning(msg)
            raise ValueError(msg)

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
                self.logger.info(f"Fixed domain typo: '{domain_name}' -> '{new_domain_name}'")
            domain_name = new_domain_name

        # Recombine
        domain = f"{domain_name}.{extension}" if extension else domain_name
        fixed_email = f"{local}@{domain}"

        # Final validation
        email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_regex, fixed_email):
            msg = f"Invalid email after fix: {fixed_email}"
            self.logger.warning(msg)
            raise ValueError(msg)

        return fixed_email


# For backward compatibility: function interface

_default_normalizer = EmailTypoFixer()


def normalize_email(email: str) -> str:
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
    return _default_normalizer.normalize(email)


# Public API
__all__ = ["EmailTypoFixer", "normalize_email"]
