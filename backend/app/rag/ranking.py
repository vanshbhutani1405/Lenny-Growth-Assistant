from collections import defaultdict

from app.rag.types import RetrievedChunk


def combine_results(
    semantic: list[RetrievedChunk],
    keyword: list[RetrievedChunk],
    *,
    semantic_weight: float = 0.65,
    keyword_weight: float = 0.35,
) -> list[RetrievedChunk]:
    """Weighted score fusion with deterministic tie-breaking by chunk ID."""
    if semantic_weight < 0 or keyword_weight < 0 or semantic_weight + keyword_weight <= 0:
        raise ValueError("ranking weights must be non-negative and not both zero")
    by_id: dict[str, RetrievedChunk] = {}
    scores: defaultdict[str, dict[str, float]] = defaultdict(dict)
    for item in semantic:
        by_id[item.id] = item
        scores[item.id]["semantic"] = item.semantic_score or 0.0
    for item in keyword:
        by_id[item.id] = item
        scores[item.id]["keyword"] = item.keyword_score or 0.0

    results: list[RetrievedChunk] = []
    for chunk_id, item in by_id.items():
        parts = scores[chunk_id]
        semantic_score = parts.get("semantic")
        keyword_score = parts.get("keyword")
        final_score = semantic_weight * (semantic_score or 0.0) + keyword_weight * (keyword_score or 0.0)
        sources = tuple(source for source, present in (("semantic", semantic_score is not None), ("keyword", keyword_score is not None)) if present)
        results.append(
            RetrievedChunk(
                id=item.id,
                episode_slug=item.episode_slug,
                chunk_text=item.chunk_text,
                chunk_index=item.chunk_index,
                guest=item.guest,
                title=item.title,
                youtube_url=item.youtube_url,
                publish_date=item.publish_date,
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                relevance_score=final_score,
                retrieval_sources=sources,
            )
        )
    return sorted(results, key=lambda item: (-item.relevance_score, item.id))
