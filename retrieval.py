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


# --- Retrieval ---------------------------------------------------------------

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k most relevant chunks for `query`.

    Each result: {rank, distance, source, chunk_number, text}.
    """
    collection = build_index()
    model = get_model()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    hits = []
    for rank, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0],
            results["distances"][0]),
        start=1,
    ):
        hits.append({
            "rank": rank,
            "distance": dist,
            "source": meta["source"],
            "chunk_number": meta["chunk_number"],
            "text": doc,
        })
    return hits


def print_results(query: str, hits: list[dict]) -> None:
    """Pretty-print retrieval results for a single query."""
    print("=" * 78)
    print(f"QUERY: {query}")
    print("=" * 78)
    for h in hits:
        print(f"\n[Rank {h['rank']}] distance={h['distance']:.4f}  "
              f"source={h['source']}  chunk #{h['chunk_number']}")
        print("-" * 78)
        print(h["text"])
    print()


# --- Demo / verification -----------------------------------------------------

TEST_QUERIES = [
    "Which professor is described as giving detailed feedback?",
    "Which professor has a heavy workload?",
    "Which professor is described as supportive and accessible outside class?",
]


def main() -> None:
    build_index()
    for query in TEST_QUERIES:
        print_results(query, retrieve(query, k=TOP_K))


if __name__ == "__main__":
    main()
