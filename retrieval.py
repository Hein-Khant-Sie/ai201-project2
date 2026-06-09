"""
Milestone 4 — Embedding and Retrieval
BMCC Professor Reviews RAG project.

This module:
  1. Loads chunks.json (produced by Milestone 3 / chunking.py)
  2. Loads the SentenceTransformer("all-MiniLM-L6-v2") embedding model
  3. Embeds every chunk's text
  4. Stores the embeddings in ChromaDB
  5. Stores metadata per chunk (source filename + chunk number)
  6. Exposes retrieve(query, k=5) for semantic search
  7. Prints query, rank, distance, source, chunk number, and chunk text

No Groq / LLM generation / Gradio yet — those are Milestone 5.
"""

import json
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# --- Configuration (from planning.md → Retrieval Approach) ------------------

PROJECT_DIR = Path(__file__).parent
CHUNKS_PATH = PROJECT_DIR / "chunks.json"
CHROMA_DIR = PROJECT_DIR / "chroma_db"

EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "professor_reviews"
TOP_K = 5

# We fetch more candidates than we return, rerank them with lightweight lexical
# signals, then de-duplicate by source before keeping the final TOP_K.
FETCH_K = 15
MAX_PER_SOURCE = 2          # cap chunks from one source in the final results
BOOST_PER_TERM = 0.06       # similarity bonus per matched positive phrase
PENALTY_PER_TERM = 0.08     # similarity penalty per matched negative phrase
OVERLAP_PER_WORD = 0.02     # bonus per overlapping (non-stopword) query word

# Lazily-initialized singletons so we load the model / build the index once.
_model: SentenceTransformer | None = None
_collection = None


# --- Setup -------------------------------------------------------------------

def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    """Load chunk records {text, source, chunk_number} from chunks.json."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path.name} not found. Run chunking.py (Milestone 3) first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def get_model() -> SentenceTransformer:
    """Load (once) the all-MiniLM-L6-v2 sentence embedding model."""
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBED_MODEL} ...")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def build_index():
    """Embed all chunks and (re)build the ChromaDB collection.

    The collection is rebuilt fresh each run so it always reflects the current
    chunks.json. Cosine distance is used so scores are easy to interpret
    (0 = identical, larger = less similar).
    """
    global _collection
    if _collection is not None:
        return _collection

    records = load_chunks()
    model = get_model()

    texts = [r["text"] for r in records]
    print(f"Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Drop any prior version so re-runs don't accumulate stale chunks.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[f"{r['source']}::chunk{r['chunk_number']}" for r in records],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {"source": r["source"], "chunk_number": r["chunk_number"]}
            for r in records
        ],
    )
    print(f"Stored {collection.count()} chunks in ChromaDB ({CHROMA_DIR.name}/)\n")

    _collection = collection
    return collection


# --- Reranking ---------------------------------------------------------------

# Topic-specific lexical signals. When a query is about workload, embeddings
# alone under-weight chunks that literally describe heavy reading/writing, so we
# boost those and penalize chunks describing an easy/light course.
WORKLOAD_BOOST = [
    "heavy workload", "lots of homework", "lots of work", "workload",
    "reading", "writing", "essays", "essay", "assignments", "assignment",
    "projects", "project", "papers", "homework",
]
WORKLOAD_PENALTY = [
    "not much work", "easy", "manageable", "light", "straightforward",
    "little work", "no homework",
]

# Query terms ignored when computing lexical overlap.
_STOPWORDS = {
    "which", "what", "who", "whom", "professor", "professors", "described",
    "describe", "most", "frequently", "as", "is", "are", "the", "a", "an",
    "of", "to", "and", "in", "with", "do", "does", "say", "about", "having",
    "has", "have", "that", "this", "they", "students", "student", "review",
    "reviews", "providing", "provide", "assigning", "assign", "their",
}


def _topic_terms(query: str) -> tuple[list[str], list[str]]:
    """Pick (boost, penalty) phrase lists appropriate for `query`.

    Currently only workload questions get a dedicated lexicon; other queries
    rely on plain query-word overlap.
    """
    q = query.lower()
    if any(w in q for w in (
        "workload", "work", "homework", "assignment", "busy", "heavy",
        "load", "reading", "writing", "essay",
    )):
        return WORKLOAD_BOOST, WORKLOAD_PENALTY
    return [], []


def _query_words(query: str) -> set[str]:
    """Content words from the query, used for lexical-overlap scoring."""
    return {
        w for w in re.findall(r"[a-z]+", query.lower())
        if len(w) > 3 and w not in _STOPWORDS
    }


def _rerank(query: str, hits: list[dict]) -> list[dict]:
    """Score each hit as cosine similarity plus lexical boosts/penalties.

    Adds `base_similarity` (1 - cosine distance, higher = closer) and `score`
    (the reranked value, higher = better) to every hit, sorted by `score`.
    """
    boost_terms, penalty_terms = _topic_terms(query)
    qwords = _query_words(query)

    for h in hits:
        text = h["text"].lower()
        base = 1.0 - h["distance"]          # cosine similarity (higher better)
        score = base
        score += BOOST_PER_TERM * sum(1 for t in boost_terms if t in text)
        score -= PENALTY_PER_TERM * sum(1 for t in penalty_terms if t in text)
        score += OVERLAP_PER_WORD * sum(1 for w in qwords if w in text)
        h["base_similarity"] = base
        h["score"] = score

    return sorted(hits, key=lambda h: h["score"], reverse=True)


def _select_diverse(hits: list[dict], k: int,
                    max_per_source: int = MAX_PER_SOURCE) -> list[dict]:
    """Take the top-k reranked hits while capping chunks per source.

    Reduces near-duplicate chunks from a single professor's file crowding out
    other relevant professors. Falls back to the leftovers if capping leaves
    fewer than k hits.
    """
    selected, overflow = [], []
    per_source: dict[str, int] = {}
    for h in hits:
        src = h["source"]
        if per_source.get(src, 0) < max_per_source:
            selected.append(h)
            per_source[src] = per_source.get(src, 0) + 1
        else:
            overflow.append(h)
        if len(selected) == k:
            break

    if len(selected) < k:
        selected.extend(overflow[: k - len(selected)])
    return selected[:k]


# --- Retrieval ---------------------------------------------------------------

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k most relevant chunks for `query`.

    Fetches FETCH_K candidates, reranks them with lexical boosts/penalties, and
    de-duplicates by source before keeping `k`. Each result:
    {rank, distance, base_similarity, score, source, chunk_number, text}.
    """
    collection = build_index()
    model = get_model()

    fetch_k = max(k, FETCH_K)
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=fetch_k)

    candidates = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0],
        results["distances"][0],
    ):
        candidates.append({
            "distance": dist,
            "source": meta["source"],
            "chunk_number": meta["chunk_number"],
            "text": doc,
        })

    reranked = _rerank(query, candidates)
    hits = _select_diverse(reranked, k)

    for rank, h in enumerate(hits, start=1):
        h["rank"] = rank
    return hits


def print_results(query: str, hits: list[dict]) -> None:
    """Pretty-print retrieval results for a single query."""
    print("=" * 78)
    print(f"QUERY: {query}")
    print("=" * 78)
    for h in hits:
        print(f"\n[Rank {h['rank']}] distance={h['distance']:.4f}  "
              f"score={h['score']:.4f}  "
              f"source={h['source']}  chunk #{h['chunk_number']}")
        print("-" * 78)
        print(h["text"])
    print()


# --- Demo / verification -----------------------------------------------------

TEST_QUERIES = [
    "Which professor is described as assigning the heaviest workload?",
    "Which professor is described as providing detailed feedback?",
    "Which professor is most frequently described as helpful and supportive?",
]


def main() -> None:
    build_index()
    for query in TEST_QUERIES:
        print_results(query, retrieve(query, k=TOP_K))


if __name__ == "__main__":
    main()
