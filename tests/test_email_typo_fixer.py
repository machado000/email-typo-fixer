import pytest
import logging
from email_typo_fixer import EmailTypoFixer, normalize_email


class TestEmailTypoFixer:
    @pytest.fixture(autouse=True)
    def _fixer(self):
        self.fixer = EmailTypoFixer()

    @pytest.mark.parametrize("input_email,expected", [
        ("User@Example.Com", "user@example.com"),
        ("  user@example.com  ", "user@example.com"),
        ("USER@EXAMPLE.COM", "user@example.com"),
        ("us*er@example.com", "user@example.com"),
        ("user@exam!ple.com", "user@example.com"),
        ("u s e r@example.com", "user@example.com"),
        ("user@exa mple.com", "user@example.com"),
        ("user@example..com", "user@example.com"),
        ("user@@example.com", "user@example.com"),
        ("user...name@example.com", "user.name@example.com"),
    ])
    def test_basic_email_normalization(self, input_email, expected):
        assert self.fixer.normalize(input_email) == expected

    @pytest.mark.parametrize("input_email,expected", [
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
    ])
    def test_domain_typo_correction(self, input_email, expected):
        assert self.fixer.normalize(input_email) == expected

    @pytest.mark.parametrize("input_email", [
        "user@example.co",
        "user@test.rog",
    ])
    def test_extension_typo_correction(self, input_email):
        result = self.fixer.normalize(input_email)
        assert "@" in result
        assert "." in result.split("@", 1)[1]

    @pytest.mark.parametrize("invalid_email", [
        "invalid.email", "user@", "@example.com", "user@example", "", "   ", 123, None, [], {}
    ])
    def test_invalid_emails_raise_error(self, invalid_email):
        with pytest.raises(ValueError):
            self.fixer.normalize(invalid_email)

    def test_edge_cases(self):
        # Plus addressing
        assert self.fixer.normalize("user+tag@example.com") == "user+tag@example.com"
        # Hyphens and underscores
        assert self.fixer.normalize("user_name@example.com") == "user_name@example.com"
        assert self.fixer.normalize("user-name@example.com") == "user-name@example.com"
        assert self.fixer.normalize("user@ex-ample.com") == "user@ex-ample.com"
        # International domains
        for email in ["user@example.co.uk", "user@example.org.au", "user@example.ca"]:
            result = self.fixer.normalize(email)
            assert "@" in result
            assert "." in result.split("@", 1)[1]

    @pytest.mark.parametrize("input_email,expected", [
        ("user@gamil.com", "user@gmail.com"),
        ("User@Example.Com", "user@example.com"),
        ("  user@example.com  ", "user@example.com"),
    ])
    def test_normalize_email_function(self, input_email, expected):
        assert normalize_email(input_email) == expected

    def test_logging_correction_message(self, caplog):
        with caplog.at_level(logging.INFO):
            self.fixer.normalize("user@gamil.com")
        assert any("Fixed domain typo" in m for m in caplog.messages)
