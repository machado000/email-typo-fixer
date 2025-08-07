import rapidfuzz
import re
import logging

from functools import lru_cache
from publicsuffixlist import PublicSuffixList


class EmailTypoFixer:
    def __init__(self, max_distance=2, typo_domains=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        self.max_distance = max_distance
        self.psl = None
        self.valid_suffixes = None
        self.domain_typos = typo_domains or {
            'gamil': 'gmail',
            'gmial': 'gmail',
            'gnail': 'gmail',
            'gmaill': 'gmail',
            'yaho': 'yahoo',
            'yahho': 'yahoo',
            'outlok': 'outlook',
            'outllok': 'outlook',
            'outlokk': 'outlook',
            'hotmal': 'hotmail',
            'hotmial': 'hotmail',
            'homtail': 'hotmail',
            'hotmaill': 'hotmail',
        }
        self._init_psl_and_suffixes()

    def _init_psl_and_suffixes(self):
        if self.psl is None:
            try:
                self.psl = PublicSuffixList()
            except Exception as e:
                self.logger.error(f"Failed to initialize PublicSuffixList: {e}")
                raise ValueError("Could not initialize public suffix list")
        if self.valid_suffixes is None:
            # Use a predefined list of common valid suffixes since _suffixlist is not available
            self.valid_suffixes = {
                'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'co', 'info', 'biz',
                'name', 'museum', 'us', 'uk', 'ca', 'de', 'jp', 'fr', 'au', 'in',
                'br', 'cn', 'ru', 'it', 'es', 'mx', 'nl', 'se', 'no', 'dk',
                'io', 'ai', 'me', 'ly', 'cc', 'tv', 'fm', 'to', 'co.uk', 'org.uk',
                'ac.uk', 'com.au', 'org.au', 'edu.au', 'gov.au', 'com.br', 'org.br',
                'edu.br', 'gov.br', 'co.jp', 'or.jp', 'ne.jp', 'go.jp', 'co.in',
                'org.in', 'edu.in', 'gov.in', 'com.cn', 'org.cn', 'edu.cn', 'gov.cn'
            }

    @lru_cache(maxsize=4096)
    def _fix_extension_typo_cached(self, domain, max_distance):
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

    def fix_extension_typo(self, domain):
        return self._fix_extension_typo_cached(domain, self.max_distance)

    def normalize(self, email: str) -> str:
        """
        Normalize and fix common issues in an email address string.
        - Lowercase
        - Remove invalid characters
        - Ensure a single '@' and at least one '.' after @
        - Use module `PublicSuffixList` and  `Levenshtein` to fix extension typos
        - Raise ValueError if cannot be fixed
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
    - Lowercase
    - Remove invalid characters
    - Ensure single '@' and at least one '.' after '@'
    - Use rapidfuzz and publicsuffixlist to fix common extension typos
    - Fix commom domain typos
    - Raise ValueError if cannot be fixed
    """
    return _default_normalizer.normalize(email)


# Public API
__all__ = ["EmailTypoFixer", "normalize_email"]
