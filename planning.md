# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I chose BMCC professor reviews and student experiences as my domain. This knowledge is valuable because official BMCC resources provide course descriptions, degree requirements, and faculty information, but they do not explain what students actually experience in class. Students often want to know about workload, grading style, exam difficulty, attendance expectations, and teaching effectiveness before registering for courses. This information is usually scattered across student reviews and is difficult to search efficiently.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->For this project, I will split the professor review documents using paragraph-based chunking. My target chunk size will be about 800 characters with a 150-character overlap between chunks.

This strategy fits my documents because Rate My Professors reviews are usually short opinion-based comments. A single review may only be a few sentences, so splitting every fixed number of characters could cut off important context. Paragraph-based chunking keeps each student review or group of related reviews more readable.

The 150-character overlap helps when useful information is near the edge of a chunk. For example, one part of a review may mention that a professor gives many assignments while the next part explains that the workload is manageable if students keep up. The overlap helps preserve that connection.

If chunks are too small, the retrieval system may return fragments that do not fully answer the question. If chunks are too large, unrelated comments about grading, exams, attendance, and personality may all get mixed together, making retrieval less precise.

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->I will use all-MiniLM-L6-v2 from sentence-transformers as my embedding model. This model runs locally, is free to use, and is lightweight enough for this project.

I will store the embedded chunks in ChromaDB. For each user query, I will retrieve the top 5 most relevant chunks. Retrieving 5 chunks gives the LLM enough context to answer while limiting unrelated information.

Semantic search is useful because students may ask questions using different wording than the reviews. For example, a student might ask, “Which professor gives useful feedback?” while a review might say, “She writes detailed comments on every essay.” The words are different, but the meaning is similar.

If this system were used in production, I would compare embedding models based on accuracy, context length, cost, speed, multilingual support, and how well they handle student review language. Since BMCC has many multilingual students, multilingual support would be an important tradeoff to consider.

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 |Which professor is most frequently described as helpful and supportive?| The professor whose reviews most consistently mention helping students, answering questions, and being available outside class.|
| 2 | Which professor is described as having the most difficult exams?| The professor whose reviews mention challenging exams, difficult tests, or low exam averages.|
| 3 | Which professor is described as providing detailed feedback?|The professor whose reviews specifically discuss detailed comments on assignments, papers, or projects. |
| 4 | Which professor is described as assigning the heaviest workload?| The professor whose reviews mention large amounts of homework, projects, readings, or assignments.|
| 5 | What do students say about attendance requirements?| What do students say about attendance requirements?|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.One risk is noisy or inconsistent review text. Some Rate My Professors reviews are detailed, but others are very short or emotional. This could make retrieval harder because not every review gives clear evidence about workload, grading, exams, or teaching style.
2.Another risk is off-topic retrieval. A user might ask about exam difficulty, but the system could retrieve a chunk that mentions the professor without actually discussing exams. This may happen if chunks are too large or if the query is too general.
3.A third risk is missing source attribution. If the system does not correctly save the professor name and file name as metadata, the final answer may not clearly show which document the information came from.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
     flowchart LR

    A[Document Ingestion<br/>Professor Review TXT Files] --> B[Chunking<br/>800 Character Chunks<br/>150 Character Overlap]

    B --> C[Embeddings<br/>all-MiniLM-L6-v2]

    C --> D[Vector Store<br/>ChromaDB]

    D --> E[Retrieval<br/>Top 5 Relevant Chunks]

    E --> F[Generation<br/>Groq Llama 3.3 70B]

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I will use Claude Code to help implement document loading, cleaning, and chunking. I will provide Claude Code with my Documents section, Chunking Strategy section, and project requirements. I expect it to create Python code that loads all professor review text files, cleans the text, and creates paragraph-based chunks with a target size of 800 characters and a 150-character overlap. I will verify the output by printing sample chunks and checking that they are readable, contain complete thoughts, and match my chunking strategy.
**Milestone 4 — Embedding and retrieval:**
I will use Claude Code to implement embeddings and retrieval. I will provide Claude Code with my Retrieval Approach section and architecture diagram. I expect it to generate code that uses the all-MiniLM-L6-v2 embedding model, stores embeddings in ChromaDB, saves source metadata, and retrieves the top 5 most relevant chunks for a query. I will verify the output by testing multiple questions and confirming that the retrieved chunks are relevant and come from the correct source documents.
**Milestone 5 — Generation and interface:**
I will use Claude Code to implement response generation and the user interface. I will provide Claude Code with the project requirements, architecture diagram, and retrieval code. I expect it to generate code that connects Groq’s llama-3.3-70b-versatile model to the retrieval pipeline and builds a Gradio interface. I will verify the output by testing questions from my evaluation plan, checking that answers are grounded in the retrieved documents, and confirming that source citations are displayed correctly.