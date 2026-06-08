"""
Milestone 5 — Gradio interface for the BMCC Professor Reviews RAG system.

Input:  a user question
Outputs:
  1. Grounded answer (LLM answer + guaranteed Sources section)
  2. Retrieved sources (filename, chunk #, distance)
  3. Retrieved chunks / debug view (full chunk text)

Run:  .venv/bin/python app.py   then open the printed local URL.
"""

import gradio as gr

from query import ask


def _format_debug(hits: list[dict]) -> str:
    """Render full retrieved chunks for the debug panel."""
    if not hits:
        return "No chunks retrieved."
    blocks = []
    for h in hits:
        blocks.append(
            f"[Rank {h['rank']}] {h['source']} | chunk #{h['chunk_number']} | "
            f"distance={h['distance']:.4f}\n{'-' * 60}\n{h['text']}"
        )
    return "\n\n".join(blocks)


def answer_question(question: str):
    """Gradio handler → (answer, sources, debug view)."""
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    result = ask(question)
    return (
        result["answer"],
        result["sources"],
        _format_debug(result["retrieved_chunks"]),
    )


with gr.Blocks(title="BMCC Professor Reviews — RAG") as demo:
    gr.Markdown(
        "# BMCC Professor Reviews — RAG\n"
        "Ask about BMCC professors. Answers are grounded **only** in the "
        "student-review documents; sources are always shown."
    )

    with gr.Row():
        question = gr.Textbox(
            label="Your question",
            placeholder="e.g. Which professor gives detailed feedback?",
            lines=2,
        )
    ask_btn = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Grounded answer", lines=10)
    sources = gr.Textbox(label="Retrieved sources", lines=6)
    debug = gr.Textbox(label="Retrieved chunks (debug view)", lines=18)

    gr.Examples(
        examples=[
            "Which professor gives detailed feedback?",
            "Which professor has a heavy workload?",
            "Which professor is supportive and accessible outside class?",
            "What do the documents say about campus dining?",
        ],
        inputs=question,
    )

    ask_btn.click(answer_question, inputs=question,
                  outputs=[answer, sources, debug])
    question.submit(answer_question, inputs=question,
                    outputs=[answer, sources, debug])


if __name__ == "__main__":
    demo.launch()
