import json
from datetime import date
from pathlib import Path
from typing import Any

from app.rag.normalization import normalize_transcript_text
from app.rag.types import TranscriptDocument


def _as_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _document_from_mapping(data: dict[str, Any], source_path: Path) -> TranscriptDocument | None:
    text = data.get("text") or data.get("transcript") or data.get("content") or data.get("chunk_text")
    if not isinstance(text, str) or not text.strip():
        return None
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else data
    slug = str(
        metadata.get("episode_slug")
        or metadata.get("episode")
        or source_path.parent.name
    )
    return TranscriptDocument(
        episode_slug=slug,
        text=normalize_transcript_text(text),
        guest=metadata.get("guest"),
        title=metadata.get("title") or metadata.get("episode_title"),
        youtube_url=metadata.get("youtube_url") or metadata.get("source_url") or metadata.get("url"),
        publish_date=_as_date(metadata.get("publish_date") or metadata.get("published_at")),
        source_path=str(source_path),
    )


def load_transcript_file(path: Path) -> list[TranscriptDocument]:
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl"}:
        if suffix == ".jsonl":
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = payload if isinstance(payload, list) else [payload]
        return [doc for record in records if isinstance(record, dict) if (doc := _document_from_mapping(record, path))]
    if suffix in {".md", ".markdown", ".txt"}:
        raw_text = path.read_text(encoding="utf-8")
        metadata: dict[str, str] = {}
        if raw_text.startswith("---\n"):
            _, front_matter, raw_text = raw_text.split("---\n", 2)
            for line in front_matter.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip().lower()] = value.strip().strip('"\'')
        text = normalize_transcript_text(raw_text)
        if not text:
            return []
        return [
            TranscriptDocument(
                episode_slug=metadata.get("episode_slug") or metadata.get("episode") or path.parent.name,
                text=text,
                guest=metadata.get("guest"),
                title=metadata.get("title"),
                youtube_url=metadata.get("youtube_url") or metadata.get("source_url") or metadata.get("url"),
                publish_date=_as_date(metadata.get("publish_date") or metadata.get("published_at")),
                source_path=str(path),
            )
        ]
    return []


def load_corpus(corpus_path: Path) -> list[TranscriptDocument]:
    paths = [corpus_path] if corpus_path.is_file() else sorted(
        path for path in corpus_path.rglob("*") if path.is_file()
    )
    documents = [doc for path in paths for doc in load_transcript_file(path)]
    return sorted(documents, key=lambda doc: (doc.episode_slug, doc.source_path or ""))
