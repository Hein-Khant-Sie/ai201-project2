"""
Milestone 5 — Generation (RAG answer with guaranteed source attribution)
BMCC Professor Reviews RAG project.

ask(question):
  1. retrieve(question, k=5)  — from Milestone 4 (retrieval.py)
  2. build a context block from the retrieved chunks
  3. call Groq (llama-3.3-70b-versatile) instructed to answer ONLY from context
  4. programmatically append a Sources section (not LLM-dependent)
  5. return {answer, sources, retrieved_chunks}

GROQ_API_KEY is loaded from .env via python-dotenv.
"""

import os

from dotenv import load_dotenv
from groq import Groq

from retrieval import retrieve, TOP_K

# --- Configuration -----------------------------------------------------------

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
INSUFFICIENT = (
    "I don't have enough information in the provided documents to answer that."
)

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about BMCC professors "
    "based ONLY on the student-review context provided to you.\n"
    "Rules:\n"
    "1. Use ONLY the information in the CONTEXT below. Do not use outside "
    "knowledge or make assumptions.\n"
    "2. If the context does not contain enough information to answer the "
    f'question, reply with exactly: "{INSUFFICIENT}"\n'
    "3. When you name a professor, base it on what the reviews actually say.\n"
    "4. Be concise and factual."
)

_client: Groq | None = None


def _get_client() -> Groq:
    """Create the Groq client once, using GROQ_API_KEY from the environment."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Copy .env.example to .env and add your "
                "key (get one free at https://console.groq.com)."
            )
        _client = Groq(api_key=api_key)
    return _client


# --- Context + prompt assembly ----------------------------------------------

def _build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the LLM."""
    blocks = []
    for h in hits:
        header = f"[Source {h['rank']}: {h['source']}, chunk #{h['chunk_number']}]"
        blocks.append(f"{header}\n{h['text']}")
    return "\n\n".join(blocks)


def _format_sources(hits: list[dict]) -> str:
    """Build the Sources section programmatically (independent of the LLM)."""
    lines = ["Sources:"]
    for h in hits:
        lines.append(
            f"  [{h['rank']}] {h['source']} (chunk #{h['chunk_number']}, "
            f"distance={h['distance']:.4f})"
        )
    return "\n".join(lines)


# --- Public API --------------------------------------------------------------

def ask(question: str, k: int = TOP_K) -> dict:
    """Answer `question` using only retrieved review context.

    Returns:
        {
          "answer": str,            # LLM answer + appended Sources section
          "sources": str,           # the programmatic Sources block
          "retrieved_chunks": list  # raw retrieve() hits (rank/distance/etc.)
        }
    """
    hits = retrieve(question, k=k)
    sources = _format_sources(hits)

    if not hits:
        return {
            "answer": f"{INSUFFICIENT}\n\n{sources}",
            "sources": sources,
            "retrieved_chunks": hits,
        }

    context = _build_context(hits)
    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the context above."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    llm_answer = response.choices[0].message.content.strip()

    # Source attribution is guaranteed here — appended regardless of the LLM.
    full_answer = f"{llm_answer}\n\n{sources}"

    return {
        "answer": full_answer,
        "sources": sources,
        "retrieved_chunks": hits,
    }


# --- CLI test ----------------------------------------------------------------

TEST_QUESTIONS = [
    "Which professor gives detailed feedback?",
    "Which professor has a heavy workload?",
    "Which professor is supportive and accessible outside class?",
    "What do the documents say about campus dining?",
]


def main() -> None:
    for q in TEST_QUESTIONS:
        print("=" * 78)
        print(f"Q: {q}")
        print("=" * 78)
        result = ask(q)
        print(result["answer"])
        print()


if __name__ == "__main__":
    main()
