"""Security log filter for sensitive data redaction.

Interceps logging records and automatically redacts passwords, JWT tokens,
Bearer headers, authorization credentials, and API secrets.
"""

from __future__ import annotations

import logging
import re

_SENSITIVE_PATTERNS = [
    re.compile(r'(password["\':\s=]+)[^\s"\'&,]+', re.IGNORECASE),
    re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r'(token["\':\s=]+)[^\s"\'&,]+', re.IGNORECASE),
    re.compile(r'(secret["\':\s=]+)[^\s"\'&,]+', re.IGNORECASE),
    re.compile(r'(api[_\-]?key["\':\s=]+)[^\s"\'&,]+', re.IGNORECASE),
]


class SensitiveDataRedactor(logging.Filter):
    """Logging filter that redacts credentials, secrets, and auth tokens from log output."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in _SENSITIVE_PATTERNS:
                record.msg = pattern.sub(r"\1[REDACTED]", record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(self._redact_arg(arg) for arg in record.args)
            elif isinstance(record.args, dict):
                record.args = {k: self._redact_arg(v) for k, v in record.args.items()}
        return True

    @staticmethod
    def _redact_arg(arg: object) -> object:
        if isinstance(arg, str):
            for pattern in _SENSITIVE_PATTERNS:
                arg = pattern.sub(r"\1[REDACTED]", arg)
        return arg


def configure_security_logging() -> None:
    """Attach the sensitive data redactor filter to the root and app loggers."""
    redactor = SensitiveDataRedactor()
    logging.getLogger().addFilter(redactor)
    logging.getLogger("uvicorn").addFilter(redactor)
    logging.getLogger("uvicorn.access").addFilter(redactor)
    logging.getLogger("app").addFilter(redactor)
