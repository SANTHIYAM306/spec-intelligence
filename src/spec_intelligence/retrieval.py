"""Hybrid lexical + optional semantic retrieval with reciprocal-rank fusion.

The lexical path is dependency-free. Dense retrieval is enabled when sentence-transformers
is installed and a local model is available; model download/network access is not required
by the core package.
"""
from __future__ import annotations
import math, re
from functools import lru_cache
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9_.#:/-]+")
STOPWORDS = {"a", "an", "the", "is", "are", "was", "were", "what", "which", "where", "when", "who", "how", "does", "do", "did", "of", "in", "on", "to", "for", "and", "or", "with", "about", "from", "this", "that", "it", "be", "as", "by", "may", "can", "could", "should", "would", "i", "me", "my", "please", "tell", "explain"}

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS]

def _idf(term: str, documents: list[list[str]]) -> float:
    df = sum(term in set(doc) for doc in documents)
    return math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))

def lexical_search(query: str, records: list[dict[str, Any]], k: int = 10) -> list[dict[str, Any]]:
    """BM25-style lexical search; favors exact protocol identifiers."""
    if k < 1: raise ValueError("k must be >= 1")
    q = tokenize(query)
    if not q or not records: return []
    docs = [tokenize(str(r.get("text", ""))) for r in records]
    avg = sum(map(len, docs)) / max(1, len(docs))
    hits = []
    for record, terms in zip(records, docs):
        counts = Counter(terms); length = len(terms); score = 0.0
        for term in q:
            f = counts[term]
            if f:
                score += _idf(term, docs) * f * 2.5 / (f + 1.5 * (1 - .75 + .75 * length / max(1, avg)))
        raw = str(record.get("text", "")).lower()
        for term in q:
            if len(term) >= 5 and term in raw: score += .75
        if score > 0: hits.append({**record, "lexical_score": round(score, 5)})
    hits.sort(key=lambda x: (x["lexical_score"], str(x.get("element_id", ""))), reverse=True)
    return hits[:k]

@lru_cache(maxsize=2)
def _load_encoder(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError('Dense search needs optional dependencies: pip install -e ".[dense]"') from exc
    return SentenceTransformer(model_name)

@lru_cache(maxsize=2)
def _encode_corpus(model_name: str, texts: tuple[str, ...]):
    """Cache embeddings for an unchanged ordered corpus within the current process."""
    return _load_encoder(model_name).encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)

def dense_search(query: str, records: list[dict[str, Any]], k: int = 10,
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> list[dict[str, Any]]:
    """Local sentence-transformers cosine retrieval with process-local model/vector caching."""
    if not records: return []
    model = _load_encoder(model_name)
    texts = tuple(str(r.get("text", "")) for r in records)
    vectors = _encode_corpus(model_name, texts)
    qvec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
    scores = vectors @ qvec
    ranked = sorted(zip(records, scores.tolist()), key=lambda x: x[1], reverse=True)[:k]
    return [{**r, "dense_score": round(float(s), 5)} for r, s in ranked]

def reciprocal_rank_fusion(*rankings: list[dict[str, Any]], k: int = 10, rrf_constant: int = 60) -> list[dict[str, Any]]:
    """Fuse independent ranked lists by canonical element ID using RRF."""
    if k < 1: raise ValueError("k must be >= 1")
    merged: dict[str, dict[str, Any]] = {}
    scores: Counter[str] = Counter()
    for ranking in rankings:
        seen = set()
        for rank, item in enumerate(ranking, start=1):
            key = str(item.get("element_id") or item.get("doc_id", "") + ":" + str(item.get("page", "")) + ":" + str(item.get("text", "")[:80]))
            if key in seen: continue
            seen.add(key)
            scores[key] += 1.0 / (rrf_constant + rank)
            merged.setdefault(key, dict(item))
    result = []
    for key, item in merged.items():
        item["rrf_score"] = round(scores[key], 7); result.append(item)
    result.sort(key=lambda x: x["rrf_score"], reverse=True)
    return result[:k]

@lru_cache(maxsize=1)
def _load_reranker(model_name: str):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)

def search(query: str, records: list[dict[str, Any]], k: int = 5,
           mode: str = "hybrid", dense_model: str = "sentence-transformers/all-MiniLM-L6-v2",
           filters: dict[str, Any] | None = None, rerank: bool = False) -> list[dict[str, Any]]:
    """Search lexical/dense/hybrid with metadata filters and optional cross-encoder reranking."""
    if k < 1:
        raise ValueError("k must be >= 1")
    if mode not in {"lexical", "dense", "hybrid"}:
        raise ValueError("mode must be lexical, dense, or hybrid")
    filters = filters or {}
    candidates = [r for r in records if all(
        (r.get(key) == value if not isinstance(value, list) else r.get(key) in value)
        for key, value in filters.items())]
    lexical = lexical_search(query, candidates, max(k * 3, k))
    if mode == "lexical":
        results = [{**x, "score": x["lexical_score"], "retrieval_mode": "lexical"} for x in lexical]
    else:
        try:
            dense = dense_search(query, candidates, max(k * 3, k), dense_model)
        except RuntimeError:
            if mode == "dense":
                raise
            # Do not imply dense retrieval ran; optionally rerank lexical candidates if asked.
            results = [{**x, "score": x["lexical_score"], "retrieval_mode": "lexical_fallback"} for x in lexical]
            if not rerank:
                return results[:k]
        else:
            if mode == "dense":
                results = [{**x, "score": x["dense_score"], "retrieval_mode": "dense"} for x in dense]
            else:
                fused = reciprocal_rank_fusion(lexical, dense, k=max(k * 3, k))
                results = [{**x, "score": x["rrf_score"], "retrieval_mode": "hybrid"} for x in fused]
    if rerank and results:
        try:
            reranker = _load_reranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
            scores = reranker.predict([(query, str(x.get("text", ""))) for x in results])
            results = [{**item, "reranker_score": float(score), "score": float(score),
                        "retrieval_mode": item.get("retrieval_mode", mode) + "+cross-encoder"}
                       for item, score in zip(results, scores)]
            results.sort(key=lambda x: x["score"], reverse=True)
        except ImportError as exc:
            raise RuntimeError('Reranking needs sentence-transformers: pip install -e ".[dense]"') from exc
    return results[:k]
