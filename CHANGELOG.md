# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-08-07

### Changed
- Major: Now parses the official `public_suffix_list.dat` file at runtime for suffix validation (no hardcoded or private attributes)
- Python 3.10+ required
- Production-ready: API and behavior are stable

### Added
- More robust and future-proof suffix handling
- Improved README and documentation
- Example for custom typo dictionary and logging

### Fixed
- Lint and test discovery issues


## [Unreleased]

## [0.1.0] - 2025-08-07

### Added
- Initial release of email-typo-fixer
- `EmailTypoFixer` class for configurable email correction
- `normalize_email` function for simple email correction
- Support for common domain typos (gmail, yahoo, outlook, hotmail variants)
- Extension typo correction using PublicSuffixList and Levenshtein distance
- Email normalization (lowercase, invalid character removal, etc.)
- Comprehensive test suite with pytest
- Type hints and mypy support
- Logging support for debugging and monitoring
- Documentation and examples

### Features
- Configurable maximum edit distance for extension corrections
- Custom typo domain dictionary support
- Robust error handling with descriptive error messages
- Support for emails with plus addressing, hyphens, and underscores
- Handles consecutive dots and @ symbols
- International domain support

### Dependencies
- python-Levenshtein >= 0.25.0 for string distance calculations
- publicsuffixlist >= 0.10.0 for domain validation
- Python 3.8+ support
