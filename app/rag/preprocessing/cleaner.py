import re
import unicodedata
import hashlib


class TextCleaner:
    # Patterns commonly used in prompt injection attempts within external documents
    SUSPICIOUS_INJECTION_PATTERNS = [
        re.compile(r'(?i)(ignore\s+all\s+(previous|above)\s+instructions)', re.IGNORECASE),
        re.compile(r'(?i)(system\s*prompt\s*override)', re.IGNORECASE),
        re.compile(r'(?i)(you\s+are\s+now\s+a\s+different\s+ai)', re.IGNORECASE),
        re.compile(r'(?i)(disregard\s+(the\s+)?(above|previous)\s+rules)', re.IGNORECASE),
    ]

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""

        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)

        # Replace non-printable ASCII/control characters except newlines and tabs
        text = "".join(ch for ch in text if ch in ("\n", "\t", "\r") or unicodedata.category(ch)[0] != "C")

        # Replace carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse excessive newlines (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Collapse horizontal whitespace
        text = re.sub(r'[ \t]{2,}', ' ', text)

        # Defang active prompt injection attempts inside document text
        for pattern in cls.SUSPICIOUS_INJECTION_PATTERNS:
            text = pattern.sub(r'[Document Excerpt Note: potential instruction override removed]', text)

        return text.strip()

    @staticmethod
    def chunk_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()
