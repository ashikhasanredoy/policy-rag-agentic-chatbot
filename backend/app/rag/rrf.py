from typing import List, Dict, Any

def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Combines multiple ranked lists (e.g. Qdrant dense search and BM25 sparse search)
    using Reciprocal Rank Fusion (RRF).
    Each item in ranked_lists is expected to be a dict with keys 'text', 'metadata', and optional 'score'.
    """
    rrf_scores = {}
    doc_map = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list, start=1):
            chunk_id = doc.get("metadata", {}).get("chunk_id")
            if not chunk_id:
                # Fallback key on content hash
                chunk_id = str(hash(doc.get("text", "")))

            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = 0.0
                doc_map[chunk_id] = doc

            # Standard RRF formula: 1 / (k + rank)
            rrf_scores[chunk_id] += 1.0 / (k + rank)

    # Sort documents by accumulated RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

    results = []
    for chunk_id, score in sorted_items[:top_n]:
        item = doc_map[chunk_id].copy()
        item["rrf_score"] = float(score)
        results.append(item)

    return results
