# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
    This project covers BMCC professor reviews and student experiences. The goal is to help students learn about professors before registering for classes by providing information about teaching style, workload, exam difficulty, grading policies, attendance expectations, and overall classroom experience.
     This knowledge is valuable because official BMCC resources provide course descriptions, degree requirements, and faculty information, but they do not describe what students actually experience in a course. Information about professors is often scattered across student review websites and can be difficult to search efficiently. By using a retrieval-augmented generation (RAG) system, students can ask natural language questions and receive answers grounded in real student reviews.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |Louise Yan |Student reviews discussing computer science courses, teaching style, workload, exams, and grading. |https://www.ratemyprofessors.com/professor/2262999 |
| 2 |Brett Sim  |Student reviews discussing programming courses, assignments, exams, and classroom experience. |https://www.ratemyprofessors.com/professor/1558787 |
| 3 |Lara Stapleton | Student reviews discussing English courses, writing assignments, feedback, and grading.| https://www.ratemyprofessors.com/professor/376128|
| 4 | Angela Polite| Student reviews discussing speech courses, presentations, participation, and classroom expectations.|https://www.ratemyprofessors.com/professor/2445910 |
| 5 |Mohammad Azhar | Student reviews discussing computer science courses, coding assignments, exams, and workload.|https://www.ratemyprofessors.com/professor/1869854 |
| 6 | Jenna Hirsch |Student reviews discussing mathematics courses, homework, exams, and teaching effectiveness.|https://www.ratemyprofessors.com/professor/804692 |
| 7 | Kenneth Levinson |Student reviews discussing English courses, essays, workload, and grading policies. |https://www.ratemyprofessors.com/professor/1499892 |
| 8 | Elizabeth Whitney |Student reviews discussing speech courses, presentations, grading, and instructor support. |https://www.ratemyprofessors.com/professor/1919143 |
| 9 |  Albert Duncan |Student reviews discussing economics courses, lectures, assignments, exams, and grading. |https://www.ratemyprofessors.com/professor/67247 |
| 10 |  Ivan Reramoso |Student reviews discussing mathematics courses, homework, exams, and student support. |https://www.ratemyprofessors.com/professor/2504915 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
800 characters
**Overlap:**
150 characters

**Why these choices fit your documents:**
I used paragraph-based chunking because my documents are professor review summaries, not long textbook-style documents. Each review usually contains one complete idea about teaching style, grading, exams, workload, or support. An 800-character chunk size keeps related review information together while still being small enough for focused retrieval. I used a 150-character overlap so that important context near the end of one chunk can still appear in the next chunk.

Before chunking, the pipeline cleaned the text by removing extra whitespace, empty lines, HTML artifacts, duplicate boilerplate, and repeated RateMyProfessors-style text such as rating labels. Each chunk also stores metadata including the source filename and chunk number.

**Final chunk count:**
34 chunks across 10 professor review documents.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I used all-MiniLM-L6-v2 from sentence-transformers.

**Production tradeoff reflection:**
I chose all-MiniLM-L6-v2 because it is lightweight, free, and runs locally without requiring an API key. This made it a good choice for a small student project with 10 professor review documents.

For a production system, I would compare embedding models based on retrieval accuracy, context length, latency, cost, and multilingual support. Since BMCC has many multilingual students, multilingual support would be important if students asked questions or wrote reviews in different languages. I would also consider whether to use a local model for privacy and lower cost or an API-hosted model for potentially stronger retrieval quality.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The system prompt tells the model to answer only using the retrieved review context. It specifically instructs the model not to use outside knowledge or make assumptions. The prompt also tells the model that if the retrieved context does not contain enough information to answer the question, it must respond with: “I don’t have enough information in the provided documents to answer that.”

The retrieved chunks are formatted into a context block before being sent to the model. Each chunk includes a source label with the filename and chunk number, so the model receives only the retrieved review evidence for that question.
**How source attribution is surfaced in the response:**
Source attribution is added programmatically after the model generates its answer. The system automatically appends a Sources section containing the source filename, chunk number, and retrieval distance score for each retrieved chunk. This means source citations are guaranteed even if the model does not include them on its own.


---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which professor is most frequently described as helpful and supportive? | The professor whose reviews most consistently mention helping students, answering questions, and being available outside class. | Multiple professors were identified as helpful and supportive, including Mohammad Azhar, Brett Sim, Elizabeth Whitney, and Angela Polite. | Partially relevant | Partially accurate |

| 2 | Which professor is described as having the most difficult exams? | The professor whose reviews mention challenging exams, difficult tests, or low exam averages. | A professor associated with difficult exams was correctly identified using review evidence. | Relevant | Accurate |

| 3 | Which professor is described as providing detailed feedback? | The professor whose reviews specifically discuss detailed comments on assignments, papers, or projects. | Kenneth Levinson was identified as providing detailed feedback. Duplicate Albert Duncan and Kenneth Levinson chunks appeared in the rankings. | Relevant | Partially accurate |

| 4 | Which professor is described as assigning the heaviest workload? | The professor whose reviews mention large amounts of homework, projects, readings, or assignments. | Kenneth Levinson was identified as having the heaviest workload because reviews mentioned extensive reading and writing assignments. | Relevant | Accurate |

| 5 | What do students say about attendance requirements? | Summary of comments regarding attendance expectations across reviews. | Attendance expectations varied by professor, with several reviews indicating flexible or non-required attendance policies. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

Which professor is most frequently described as helpful and supportive?

**What the system returned:**

The system identified multiple professors as helpful and supportive, including Mohammad Azhar, Brett Sim, Elizabeth Whitney, and Angela Polite. However, it could not confidently determine one single professor as the most frequently described as helpful and supportive.

**Root cause (tied to a specific pipeline stage):**

This failure happened during the retrieval stage. The system retrieves only the top 5 chunks for each query, so it does not examine all review documents at once. Because many professors had reviews that described them as helpful or supportive, the model did not have enough evidence to perform document-wide frequency counting. The system is good at retrieving relevant chunks, but it is not designed to count how often each professor is described a certain way across the full corpus.

**What you would change to fix it:**

I would add a document-level aggregation step before generation. Instead of only retrieving the top 5 chunks, the system could scan all professor documents, count mentions of words and phrases like "helpful," "supportive," "accessible," and "caring," and then compare results across professors. I would also improve retrieval diversity so multiple chunks from the same professor do not crowd out other useful results.v

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The planning document helped guide the overall structure of the project before I started coding. The chunking strategy, retrieval approach, and architecture diagram made it easier to build each milestone step by step. Having the evaluation questions prepared in advance also gave me a clear way to test whether retrieval and generation were working correctly.
**One way your implementation diverged from the spec, and why:**
he original plan assumed that retrieval would always be able to identify a single best answer for comparison questions. During testing, I found that some questions, such as determining the most supportive professor, required comparing information across many documents rather than retrieving only a few relevant chunks. As a result, the system sometimes returned multiple professors instead of one. This happened because the retrieval-based design was optimized for answering questions from retrieved evidence rather than performing document-wide analysi
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
    I gave Claude Code my Chunking Strategy section from planning.md, including the requirement for paragraph-based chunking, an 800-character chunk size, and a 150-character overlap.
- *What it produced:*
    It produced the chunking.py file that loads documents, cleans text, creates chunks, and stores chunk metadata including source filename and chunk number.
- *What I changed or overrode:*
    I reviewed the output and verified that the chunk size, overlap, and metadata matched my specification. I also tested the chunk count and sample chunks to make sure the chunks contained complete review information rather than fragmented text.
**Instance 2**

- *What I gave the AI:*
    I gave Claude Code my Retrieval Approach section and architecture diagram. I specified that the project should use all-MiniLM-L6-v2, ChromaDB, top-5 retrieval, and source metadata.
- *What it produced:*
    It generated retrieval.py, query.py, and app.py, which implemented embeddings, vector search, Groq-based generation, source attribution, and a Gradio interface.
- *What I changed or overrode:*
    I tested retrieval results using my evaluation questions and reviewed the generated code to ensure that source attribution was added programmatically rather than relying only on the language model. I also verified that out-of-domain questions returned a refusal response instead of using outside knowledge.

## Demo Video

Loom Video:

https://www.loom.com/share/your-link-here