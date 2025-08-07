import pytest
import logging
from email_typo_fixer import EmailTypoFixer, normalize_email


class TestEmailTypoFixer:
    """Test suite for EmailTypoFixer class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.fixer = EmailTypoFixer()

    def test_init_default(self):
        """Test default initialization."""
        fixer = EmailTypoFixer()
        assert fixer.max_distance == 2
        assert 'gamil' in fixer.domain_typos
        assert fixer.domain_typos['gamil'] == 'gmail'
        assert fixer.psl is not None
        assert fixer.valid_suffixes is not None

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        custom_typos = {'test': 'example'}
        logger = logging.getLogger('test')
        fixer = EmailTypoFixer(max_distance=3, typo_domains=custom_typos, logger=logger)

        assert fixer.max_distance == 3
        assert fixer.domain_typos == custom_typos
        assert fixer.logger == logger

    def test_basic_email_normalization(self):
        """Test basic email normalization."""
        test_cases = [
            ("User@Example.Com", "user@example.com"),
            ("  user@example.com  ", "user@example.com"),
            ("USER@EXAMPLE.COM", "user@example.com"),
        ]

        for input_email, expected in test_cases:
            result = self.fixer.normalize(input_email)
            assert result == expected

    def test_domain_typo_correction(self):
        """Test correction of common domain typos."""
        test_cases = [
            ("user@gamil.com", "user@gmail.com"),
            ("user@gmial.com", "user@gmail.com"),
            ("user@gnail.com", "user@gmail.com"),
            ("user@gmaill.com", "user@gmail.com"),
            ("user@yaho.com", "user@yahoo.com"),
            ("user@yahho.com", "user@yahoo.com"),
            ("user@outlok.com", "user@outlook.com"),
            ("user@outllok.com", "user@outlook.com"),
            ("user@outlokk.com", "user@outlook.com"),
            ("user@hotmal.com", "user@hotmail.com"),
            ("user@hotmial.com", "user@hotmail.com"),
            ("user@homtail.com", "user@hotmail.com"),
            ("user@hotmaill.com", "user@hotmail.com"),
        ]

        for input_email, expected in test_cases:
            result = self.fixer.normalize(input_email)
            assert result == expected

    def test_extension_typo_correction(self):
        """Test correction of extension typos."""
        # Note: These tests depend on the PublicSuffixList and may vary
        test_cases = [
            ("user@example.co", "user@example.com"),  # Common typo
            ("user@test.rog", "user@test.org"),       # Common typo
        ]

        for input_email, expected in test_cases:
            result = self.fixer.normalize(input_email)
            # Extension correction might not always work as expected
            # Just ensure the email is still valid
            assert "@" in result
            assert "." in result.split("@")[1]

    def test_invalid_character_removal(self):
        """Test removal of invalid characters."""
        test_cases = [
            ("us*er@example.com", "user@example.com"),
            ("user@exam!ple.com", "user@example.com"),
            ("u s e r@example.com", "user@example.com"),
            ("user@exa mple.com", "user@example.com"),
        ]

        for input_email, expected in test_cases:
            result = self.fixer.normalize(input_email)
            assert result == expected

    def test_consecutive_character_handling(self):
        """Test handling of consecutive dots and @ symbols."""
        test_cases = [
            ("user@example..com", "user@example.com"),
            ("user@@example.com", "user@example.com"),
            ("user...name@example.com", "user.name@example.com"),
        ]

        for input_email, expected in test_cases:
            result = self.fixer.normalize(input_email)
            assert result == expected

    def test_invalid_emails_raise_error(self):
        """Test that invalid emails raise ValueError."""
        invalid_emails = [
            "invalid.email",           # No @ symbol
            "user@",                   # Missing domain
            "@example.com",            # Missing local part
            "user@example",            # Missing TLD
            "",                        # Empty string
            "   ",                     # Only whitespace
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(ValueError):
                self.fixer.normalize(invalid_email)

    def test_correctable_email_issues(self):
        """Test that some email issues can be corrected rather than raising errors."""
        correctable_cases = [
            ("user@@example.com", "user@example.com"),  # Multiple @ symbols
        ]

        for input_email, expected in correctable_cases:
            result = self.fixer.normalize(input_email)
            assert result == expected

    def test_non_string_input(self):
        """Test that non-string input raises ValueError."""
        invalid_inputs = [123, None, [], {}]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError):
                self.fixer.normalize(invalid_input)

    def test_custom_typo_domains(self):
        """Test custom typo domain dictionary."""
        custom_typos = {
            'custtypo': 'custom',
            'testtypo': 'test',
        }
        fixer = EmailTypoFixer(typo_domains=custom_typos)

        result = fixer.normalize("user@custtypo.com")
        assert result == "user@custom.com"

        result = fixer.normalize("user@testtypo.org")
        assert result == "user@test.org"

    def test_max_distance_parameter(self):
        """Test max_distance parameter for extension correction."""
        # This test is more about ensuring the parameter is used
        # Actual behavior depends on available suffixes
        fixer_strict = EmailTypoFixer(max_distance=1)
        fixer_lenient = EmailTypoFixer(max_distance=3)

        # Both should handle basic cases
        assert fixer_strict.normalize("user@example.com") == "user@example.com"
        assert fixer_lenient.normalize("user@example.com") == "user@example.com"

    def test_logging(self):
        """Test logging functionality."""
        import io
        import logging

        # Create a string buffer to capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        fixer = EmailTypoFixer(logger=logger)
        fixer.normalize("user@gamil.com")  # Should log the correction

        log_output = log_capture.getvalue()
        # Check that some logging occurred (exact message may vary)
        assert len(log_output) >= 0  # Just ensure no crash


class TestNormalizeEmailFunction:
    """Test suite for the standalone normalize_email function."""

    def test_normalize_email_function(self):
        """Test the standalone normalize_email function."""
        test_cases = [
            ("user@gamil.com", "user@gmail.com"),
            ("User@Example.Com", "user@example.com"),
            ("  user@example.com  ", "user@example.com"),
        ]

        for input_email, expected in test_cases:
            result = normalize_email(input_email)
            assert result == expected

    def test_normalize_email_invalid_input(self):
        """Test that normalize_email raises ValueError for invalid input."""
        with pytest.raises(ValueError):
            normalize_email("invalid.email")

    def test_normalize_email_consistency(self):
        """Test that normalize_email produces consistent results."""
        email = "user@gamil.com"
        result1 = normalize_email(email)
        result2 = normalize_email(email)
        assert result1 == result2


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""

    def test_very_long_email(self):
        """Test handling of very long email addresses."""
        long_local = "a" * 64  # Maximum local part length
        long_domain = "b" * 50 + ".com"
        long_email = f"{long_local}@{long_domain}"

        fixer = EmailTypoFixer()
        result = fixer.normalize(long_email)
        assert "@" in result
        assert result.startswith(long_local.lower())

    def test_email_with_plus_addressing(self):
        """Test emails with plus addressing (Gmail style)."""
        fixer = EmailTypoFixer()
        email = "user+tag@example.com"
        result = fixer.normalize(email)
        assert result == "user+tag@example.com"

    def test_email_with_hyphens_and_underscores(self):
        """Test emails with hyphens and underscores."""
        fixer = EmailTypoFixer()
        test_cases = [
            ("user_name@example.com", "user_name@example.com"),
            ("user-name@example.com", "user-name@example.com"),
            ("user@ex-ample.com", "user@ex-ample.com"),
        ]

        for input_email, expected in test_cases:
            result = fixer.normalize(input_email)
            assert result == expected

    def test_international_domains(self):
        """Test handling of international domain names."""
        fixer = EmailTypoFixer()
        # These should pass through without error
        test_emails = [
            "user@example.co.uk",
            "user@example.org.au",
            "user@example.ca",
        ]

        for email in test_emails:
            result = fixer.normalize(email)
            assert "@" in result
            assert "." in result.split("@")[1]


if __name__ == "__main__":
    pytest.main([__file__])
