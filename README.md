# Email Typo Fixer

[![Python Support](https://img.shields.io/pypi/pyversions/email-typo-fixer.svg)](https://pypi.org/project/email-typo-fixer/)
[![PyPI version](https://img.shields.io/pypi/v/email-typo-fixer)](https://pypi.org/project/email-typo-fixer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Issues](https://img.shields.io/github/issues/machado000/email-typo-fixer)](https://github.com/machado000/email-typo-fixer/issues)

A Python library to automatically detect and fix common typos in email addresses using intelligent algorithms and domain knowledge.

## Features

- **Email Normalization**: Lowercases, strips, and removes invalid characters
- **Extension Validation**: Validates and corrects TLDs using the official [PublicSuffixList](https://pypi.org/project/publicsuffixlist/) (parses `.dat` file directly)
- **Smart Typo Detection**: Uses Levenshtein distance to detect and correct TLD and domain name typos
- **Domain Correction**: Fixes common domain typos (e.g., `gamil.com` → `gmail.com`)
- **Configurable**: Custom typo dictionary and distance thresholds
- **Logging Support**: Built-in logging for debugging and monitoring


## Installation

```bash
pip install email-typo-fixer
```

## Quick Start

```python
from email_typo_fixer import normalize_email, EmailTypoFixer

# Simple function interface
corrected_email = normalize_email("user@gamil.com")
print(corrected_email)  # user@gmail.com

# Class interface for more control
fixer = EmailTypoFixer(max_distance=1)
corrected_email = fixer.normalize("user@yaho.com")
print(corrected_email)  # user@yahoo.com
```


## Limitations

### TLD '.co' False Positives

By default, the library may correct emails ending in `.co` (such as `user@example.co`) to `.com` if the Levenshtein distance is within the allowed threshold. This can lead to false positives, especially for valid `.co` domains (e.g., Colombian domains or legitimate `.co` TLDs).

**How to control this behavior:**

- The `normalize` method and the `normalize_email` function accept an optional parameter `fix_tld_co: bool` (default: `True`).
- If you want to prevent `.co` domains from being auto-corrected to `.com`, call:

```python
from email_typo_fixer import normalize_email

normalize_email("user@example.co", fix_tld_co=False)  # Will NOT change .co to .com
```

Or, with the class:

```python
fixer = EmailTypoFixer()
fixer.normalize("user@example.co", fix_tld_co=False)
```

This gives you control to avoid unwanted corrections for `.co` domains.


## Usage Examples

### Basic Email Correction

```python
from email_typo_fixer import normalize_email

# Fix common domain typos
normalize_email("john.doe@gamil.com")     # → john.doe@gmail.com
normalize_email("jane@yaho.com")         # → jane@yahoo.com
normalize_email("user@outlok.com")       # → user@outlook.com
normalize_email("test@hotmal.com")       # → test@hotmail.com

# Fix extension typos (using up-to-date public suffix list)
normalize_email("user@example.co")       # → user@example.com
normalize_email("user@site.rog")         # → user@site.org
```

### Robust Suffix Handling

This library parses the official `public_suffix_list.dat` file at runtime, ensuring all TLDs and public suffixes are always up to date. No hardcoded suffixes are used.

### Advanced Usage with Custom Configuration

```python
from email_typo_fixer import EmailTypoFixer
import logging

# Create a custom logger
logger = logging.getLogger("email_fixer")
logger.setLevel(logging.INFO)

# Custom typo dictionary
custom_typos = {
    'companytypo': 'company',
    'orgtypo': 'org',
}

# Initialize with custom settings
fixer = EmailTypoFixer(
    max_distance=2,           # Allow more distant corrections
    typo_domains=custom_typos, # Use custom typo dictionary
    logger=logger             # Use custom logger
)

# Fix emails with custom rules
corrected = fixer.normalize("user@companytypo.com")
print(corrected)  # user@company.com
```

### Email Validation and Normalization

```python
from email_typo_fixer import EmailTypoFixer

fixer = EmailTypoFixer()

try:
    # Normalize and validate
    email = fixer.normalize("  USER@EXAMPLE.COM  ")
    print(email)  # user@example.com
    
    # Remove invalid characters
    email = fixer.normalize("us*er@exam!ple.com")
    print(email)  # user@example.com
    
except ValueError as e:
    print(f"Invalid email: {e}")
```

## API Reference

### `normalize_email(email: str) -> str`

Simple function interface for email normalization.

**Parameters:**
- `email` (str): The email address to normalize

**Returns:**
- `str`: The corrected and normalized email address

**Raises:**
- `ValueError`: If the email cannot be fixed or is invalid

### `EmailTypoFixer`

Main class for email typo correction with customizable options.

#### `__init__(max_distance=1, typo_domains=None, logger=None)`

**Parameters:**
- `max_distance` (int): Maximum Levenshtein distance for extension corrections (default: 1)
- `typo_domains` (dict): Custom dictionary of domain typos to corrections
- `logger` (logging.Logger): Custom logger instance

#### `normalize(email: str) -> str`

Normalize and fix typos in an email address.

**Parameters:**
- `email` (str): The email address to normalize

**Returns:**
- `str`: The corrected and normalized email address

**Raises:**
- `ValueError`: If the email cannot be fixed or is invalid

## Default Typo Corrections

The library includes built-in corrections for common email provider typos:

| Typo | Correction |
|------|------------|
| gamil | gmail |
| gmial | gmail |
| gnail | gmail |
| gmaill | gmail |
| yaho | yahoo |
| yahho | yahoo |
| outlok | outlook |
| outllok | outlook |
| outlokk | outlook |
| hotmal | hotmail |
| hotmial | hotmail |
| homtail | hotmail |
| hotmaill | hotmail |

## Error Handling

The library raises `ValueError` exceptions for emails that cannot be corrected:

```python
from email_typo_fixer import normalize_email

try:
    normalize_email("invalid.email")  # Missing @ symbol
except ValueError as e:
    print(f"Cannot fix email: {e}")

try:
    normalize_email("user@")  # Missing domain
except ValueError as e:
    print(f"Cannot fix email: {e}")
```

## Requirements

- Python 3.11+
- RapidFuzz  >= 3.13.0
- publicsuffixlist >= 1.0.2

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/email-typo-fixer.git
cd email-typo-fixer

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Running Tests

```bash
# Run tests with coverage
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_email_typo_fixer.py
```

### Code Quality

```bash
# Lint with flake8
poetry run flake8 email_typo_fixer tests

# Type checking with mypy
poetry run mypy email_typo_fixer
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgments

- Uses the [Levenshtein](https://github.com/maxbachmann/Levenshtein) and [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) libraries for string distance calculations
- Uses [publicsuffixlist](https://github.com/ko-zu/psl) for TLD (Top Level Domain) validation
- Inspired by various email validation libraries in the Python ecosystem
