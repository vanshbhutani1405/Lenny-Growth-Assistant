from dataclasses import dataclass
import re

from app.rag.normalization import normalize_transcript_text


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    text: str


_WORD_RE = re.compile(r"\S+")


def chunk_transcript(
    text: str,
    *,
    chunk_size_words: int = 400,
    overlap_words: int = 60,
) -> list[TextChunk]:
    """Create deterministic overlapping word chunks with bounded overlap."""
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive")
    if overlap_words < 0 or overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be >= 0 and smaller than chunk_size_words")

    words = _WORD_RE.findall(normalize_transcript_text(text))
    if not words:
        return []

    step = chunk_size_words - overlap_words
    chunks: list[TextChunk] = []
    for index, start in enumerate(range(0, len(words), step)):
        chunk_words = words[start : start + chunk_size_words]
        if not chunk_words:
            break
        # Do not emit a tiny trailing fragment; fold it into the preceding chunk.
        if len(chunk_words) < max(20, overlap_words) and chunks:
            previous = chunks[-1]
            chunks[-1] = TextChunk(previous.index, " ".join(words[start - overlap_words :]))
            break
        chunks.append(TextChunk(index, " ".join(chunk_words)))
        if start + chunk_size_words >= len(words):
            break
    return chunks
