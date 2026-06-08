"""
Milestone 3 — Document Ingestion and Chunking
BMCC Professor Reviews RAG project.

This module:
  1. Loads all .txt files from documents/
  2. Cleans the text (whitespace, HTML artifacts, boilerplate, empty lines)
  3. Splits each document into paragraph-based chunks
     (target ~800 chars, ~150 char overlap)
  4. Returns chunks with metadata (source filename + chunk number)
  5. Prints one cleaned-document preview
  6. Prints 5 representative chunks
  7. Prints the total number of chunks

No embeddings, vector store, LLM, or UI yet — those come in later milestones.
"""

import html
import json
import re
from pathlib import Path

# --- Configuration (from planning.md → Chunking Strategy) -------------------

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHUNKS_OUTPUT = Path(__file__).parent / "chunks.json"

TARGET_CHUNK_SIZE = 800   # characters
CHUNK_OVERLAP = 150       # characters

# Lines that are pure RateMyProfessors UI boilerplate and carry no review
# content. Matched case-insensitively against whole (stripped) lines.
BOILERPLATE_LINES = {
    "helpful",
    "not helpful",
    "rate this professor",
    "rate professor",
    "would take again",
    "thumbs up",
    "thumbs down",
    "report",
    "share",
    "all reviews",
    "quality",
    "difficulty",
    "awful",
    "average",
    "awesome",
}

# Inline boilerplate phrases to strip wherever they appear in a line.
BOILERPLATE_PHRASES = [
    "Textbook Used",
    "Would Take Again",
    "Grade Received",
    "For Credit",
    "Attendance Mandatory",
    "Online Class",
]


# --- Cleaning ----------------------------------------------------------------

def clean_text(raw: str) -> str:
    """Normalize a raw document into clean, readable paragraphs.

    Removes HTML tags/entities, collapses runs of whitespace, drops empty and
    boilerplate lines, and de-duplicates consecutive repeated lines. Paragraph
    boundaries (blank lines) are preserved so chunking can respect them.
    """
    # Decode HTML entities (&amp; &nbsp; &#39; etc.) then strip HTML tags.
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize newlines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines = []
    prev_line = None
    for line in text.split("\n"):
        # Collapse internal runs of whitespace to single spaces.
        line = re.sub(r"[ \t\f\v]+", " ", line).strip()

        # Remove inline boilerplate phrases.
        for phrase in BOILERPLATE_PHRASES:
            line = re.sub(re.escape(phrase), "", line, flags=re.IGNORECASE).strip()

        # Drop pure-boilerplate lines.
        if line.lower() in BOILERPLATE_LINES:
            continue

        # Keep blank lines as paragraph separators, but don't stack them.
        if line == "":
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            prev_line = None
            continue

        # Skip consecutive duplicate lines (repeated boilerplate).
        if line == prev_line:
            continue

        cleaned_lines.append(line)
        prev_line = line

    # Collapse 3+ blank lines into a single paragraph break and trim ends.
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


# --- Chunking ----------------------------------------------------------------

def _word_safe_tail(text: str, max_chars: int) -> str:
    """Return up to `max_chars` from the end of `text`, snapped to a word
    boundary so the overlap doesn't start mid-word."""
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    # Drop a leading partial word if we cut in the middle of one.
    space = tail.find(" ")
    if space != -1:
        tail = tail[space + 1:]
    return tail.strip()


def _window_split(paragraph: str, target_size: int, overlap: int) -> list[str]:
    """Sliding-window split for a single paragraph longer than target_size.

    Each window is up to target_size chars and snaps to the nearest word
    boundary; consecutive windows share `overlap` chars of context.
    """
    chunks = []
    start = 0
    n = len(paragraph)
    while start < n:
        end = min(start + target_size, n)
        # Snap end back to a word boundary (unless we're at the very end).
        if end < n:
            space = paragraph.rfind(" ", start, end)
            if space != -1 and space > start:
                end = space
        chunks.append(paragraph[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def chunk_text(text: str, target_size: int = TARGET_CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split cleaned text into paragraph-based chunks.

    Paragraphs (blank-line separated) are greedily packed until adding the
    next would exceed `target_size`. Each new chunk begins with a ~`overlap`
    char tail of the previous chunk so context near boundaries is preserved.
    Paragraphs longer than `target_size` on their own are window-split.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # An oversized paragraph can't fit in one chunk — flush, then window it.
        if len(para) > target_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_window_split(para, target_size, overlap))
            continue

        if current and len(current) + len(para) + 2 > target_size:
            # Emit the current chunk and seed the next one with an overlap tail.
            chunks.append(current.strip())
            tail = _word_safe_tail(current, overlap)
            current = f"{tail}\n\n{para}" if tail else para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


# --- Ingestion pipeline ------------------------------------------------------

def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> dict[str, str]:
    """Load every .txt file in `documents_dir` as {filename: raw_text}."""
    docs = {}
    for path in sorted(documents_dir.glob("*.txt")):
        docs[path.name] = path.read_text(encoding="utf-8", errors="replace")
    return docs


def build_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """Run the full ingest → clean → chunk pipeline.

    Returns a list of chunk records, each:
        {"text": str, "source": filename, "chunk_number": int}
    `chunk_number` restarts at 1 within each source document.
    """
    raw_docs = load_documents(documents_dir)
    records = []
    for source, raw in raw_docs.items():
        cleaned = clean_text(raw)
        for i, chunk in enumerate(chunk_text(cleaned), start=1):
            records.append({
                "text": chunk,
                "source": source,
                "chunk_number": i,
            })
    return records


def save_chunks(records: list[dict], output_path: Path = CHUNKS_OUTPUT) -> None:
    """Persist chunk records to a JSON file for later milestones."""
    output_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# --- Demo / verification -----------------------------------------------------

def main() -> None:
    raw_docs = load_documents()

    if not raw_docs:
        print(f"No .txt files found in {DOCUMENTS_DIR}/")
        print("Add your professor review files (e.g. louise_yan.txt) and re-run.")
        return

    print(f"Loaded {len(raw_docs)} document(s) from {DOCUMENTS_DIR}/\n")

    # 5) One cleaned-document preview.
    first_name = next(iter(raw_docs))
    cleaned_preview = clean_text(raw_docs[first_name])
    print("=" * 70)
    print(f"CLEANED DOCUMENT PREVIEW — {first_name}")
    print("=" * 70)
    print(cleaned_preview[:800])
    if len(cleaned_preview) > 800:
        print(f"... [truncated, {len(cleaned_preview)} chars total]")
    print()

    # Build all chunks with metadata.
    records = build_chunks()
    save_chunks(records)
    print(f"Saved {len(records)} chunks to {CHUNKS_OUTPUT.name}\n")

    # 6) Five representative chunks, spread evenly across the corpus.
    print("=" * 70)
    print("5 REPRESENTATIVE CHUNKS")
    print("=" * 70)
    if records:
        n = len(records)
        sample_idx = sorted({round(i * (n - 1) / 4) for i in range(5)})
        for idx in sample_idx:
            rec = records[idx]
            print(f"\n--- [{rec['source']} | chunk #{rec['chunk_number']}"
                  f" | {len(rec['text'])} chars] ---")
            print(rec["text"])
    print()

    # 7) Total number of chunks.
    print("=" * 70)
    print(f"TOTAL CHUNKS: {len(records)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
