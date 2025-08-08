

import logging

from .email_typo_fixer import EmailTypoFixer, normalize_email
from typing import Optional


def setup_logging(level: int = logging.INFO, format_string: Optional[str] = None) -> None:
    """
    Setup logging configuration for the package.

    Args:
        level: Logging level (default: logging.INFO)
        format_string: Custom format string for log messages. If None, uses default format.

    Example:
        >>> setup_logging(level=logging.DEBUG)
        >>> setup_logging(format_string='%(asctime)s - %(levelname)s - %(message)s')
    """
    if format_string is None:
        format_string = '%(levelname)s - %(message)s'

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[logging.StreamHandler()]
    )


__all__ = ["EmailTypoFixer", "normalize_email", "setup_logging"]
