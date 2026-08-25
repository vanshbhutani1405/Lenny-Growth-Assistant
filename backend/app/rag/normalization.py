import re
import unicodedata


_MULTISPACE = re.compile(r"[ \t]+")
_MANY_NEWLINES = re.compile(r"\n{3,}")


def normalize_transcript_text(text: str) -> str:
    """Normalize formatting while retaining words, punctuation, and paragraph boundaries."""
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00a0", " ")
    lines = [_MULTISPACE.sub(" ", line).strip() for line in normalized.split("\n")]
    normalized = _MANY_NEWLINES.sub("\n\n", "\n".join(lines))
    return normalized.strip()
