"""
RecruitBot — PII Anonymization Service (Sprint 0.3)

AI Firewall: Strips personally identifiable information before
sending candidate data to external LLM APIs.

This ensures compliance with DPDP Act data minimization requirements.
Only anonymized semantic content reaches the model.

Usage:
    from app.services.anonymizer import Anonymizer
    clean_text = Anonymizer.anonymize(raw_resume_text)
"""

import re
from typing import Dict, Tuple


class Anonymizer:
    """
    Strips PII from text before sending to LLM APIs.
    Currently pattern-based. Can be upgraded to NER-based detection later.
    """

    # ── PII Patterns ──
    PATTERNS = {
        "email": re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        "phone_indian": re.compile(
            r'(?:\+91[\s-]?)?(?:\d{5}[\s-]?\d{5}|\d{10}|\d{3}[\s-]?\d{3}[\s-]?\d{4})'
        ),
        "aadhaar": re.compile(
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        ),
        "pan": re.compile(
            r'\b[A-Z]{5}\d{4}[A-Z]\b'
        ),
        "url": re.compile(
            r'https?://\S+'
        ),
    }

    # ── Replacement tokens ──
    REPLACEMENTS = {
        "email": "[EMAIL_REDACTED]",
        "phone_indian": "[PHONE_REDACTED]",
        "aadhaar": "[AADHAAR_REDACTED]",
        "pan": "[PAN_REDACTED]",
        "url": "[URL_REDACTED]",
    }

    @classmethod
    def anonymize(cls, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Remove PII from text. Returns (anonymized_text, redaction_counts).

        Example:
            clean, counts = Anonymizer.anonymize("Contact me at john@gmail.com or +91 98765 43210")
            # clean = "Contact me at [EMAIL_REDACTED] or [PHONE_REDACTED]"
            # counts = {"email": 1, "phone_indian": 1}
        """
        redaction_counts = {}
        anonymized = text

        for pii_type, pattern in cls.PATTERNS.items():
            matches = pattern.findall(anonymized)
            if matches:
                redaction_counts[pii_type] = len(matches)
                anonymized = pattern.sub(cls.REPLACEMENTS[pii_type], anonymized)

        return anonymized, redaction_counts

    @classmethod
    def is_clean(cls, text: str) -> bool:
        """Check if text contains any detectable PII."""
        for pattern in cls.PATTERNS.values():
            if pattern.search(text):
                return False
        return True
