# Jäppinen Ltd. - Technical Support AI (PoC)

A CLI-based Retrieval-Augmented Generation (RAG) chatbot for Jäppinen Ltd. field mechanics. It answers technical questions about Maytag and Midea washing machines strictly from the provided service manuals - no guessing, no hallucination.

---

## What It Does

Field mechanics can ask natural language questions and get precise, sourced answers directly from the service documentation. Every answer includes the source manual and page number so it can be verified on the spot. If the documentation does not cover the question, the system says so - it will not invent an answer.

Multi-turn conversations are supported. Follow-up questions like "How do I test that component?" are resolved against the previous exchange before retrieval, so the mechanic does not need to repeat context.

---

## Architecture

The system is a standard RAG pipeline:

    PDF files
        -> text extraction (pypdfium2)
        -> cleaning + chunking (RecursiveCharacterTextSplitter)
        -> embeddings (text-embedding-3-small)
        -> ChromaDB (local, persistent)

    User query
        -> query rewriting if follow-up (gpt-4o-mini)
        -> ChromaDB similarity search -> top-15 chunks
        -> system prompt + context + query -> gpt-4o-mini
        -> streamed answer + source citations

The LLM never sees the raw PDFs - it only sees the pre-retrieved chunks most relevant to the query. This keeps costs low, latency short, and the grounding constraint reliable.

---

## Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| LLM | gpt-4o-mini | Cost-efficient; retrieval does the heavy lifting |
| Embeddings | text-embedding-3-small | Good quality/cost balance for this scale |
| Vector DB | ChromaDB (local) | Zero infrastructure; persists to disk |
| PDF extraction | pypdfium2 | pdfminer produces garbled text on the Maytag manual due to font encoding issues |
| Chunking | RecursiveCharacterTextSplitter | Chunk size 1000, overlap 200 |
| CLI | Python readline + colorama | Arrow key navigation, colored output, no extra deps |

---

## Project Structure

    jappinen-ai-poc/
    |
    +-- data/                        # Service manual PDFs (not tracked in git)
    +-- vector_store/                # ChromaDB storage (auto-generated)
    +-- logs/                        # Query logs, one JSON file per day
    |
    +-- src/
    |   +-- config.py                # Constants and environment loading
    |   +-- document_processor.py   # PDF extraction, cleaning, chunking
    |   +-- vector_db.py            # Embedding and retrieval
    |   +-- rag_engine.py           # Prompt construction, OpenAI calls
    |   +-- cli.py                  # Interactive input loop
    |   +-- logger.py               # Query logging
    |
    +-- tests/
    |   +-- test_rag.py             # Automated RAG engine tests
    |
    +-- test/
    |   +-- manual_test_suite.md    # Manual test cases and results
    |   +-- logs/                   # Manual test session logs by section
    |
    +-- main.py                      # Entry point
    +-- requirements.txt
    +-- .env                         # LLM_API_KEY (not tracked)

---

## Setup

**Requirements:** Python 3.10+, an OpenAI API key.

    git clone <repo>
    cd jappinen-ai-poc

    python -m venv venv
    source venv/bin/activate

    pip install -r requirements.txt

Create a `.env` file in the project root:

    LLM_API_KEY=sk-...

Add the following service manual PDFs to the `data/` directory:

    data/technical-manual-w11663204-revb.pdf
    data/LAD-Front-Loading-Service-Manual-L11.pdf On first run the system will extract, chunk, and embed all PDFs automatically. This takes around a minute and only happens once - subsequent runs load from the persisted vector store.

    python main.py

---

## Usage

### Basic queries

Just type your question at the prompt:

    Mechanic: What does fault code F9E1 mean?
    Mechanic: How do I remove the drive motor?
    Mechanic: The washer will not drain - what should I check?

Every answer is followed by source citations (manual name and page number).

### Multi-turn conversations

Follow-up questions work naturally within a session. The system rewrites vague follow-ups into self-contained retrieval queries before searching, so context carries over correctly:

    Mechanic: What does fault code F5E2 mean?
    Assistant: F5E2 - Lid Lock Fault ...

    Mechanic: How do I test the component responsible?
    Assistant: To test the lid lock, disconnect J15 and measure resistance ...

    Mechanic: What are the steps to replace it?
    Assistant: Unplug the washer, replace the main control, reassemble ...

### Slash commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/manuals` | List loaded manuals with chunk counts |
| `/filter maytag` | Restrict all queries to the Maytag manual |
| `/filter midea` | Restrict all queries to the Midea manual |
| `/filter off` | Remove the filter |
| `/clear` | Reset conversation history |
| `/last` | Reprint the previous answer and sources |

### Manual filter

When working on a specific machine, set a filter to prevent cross-manual retrieval noise:

    Mechanic: /filter maytag
    Filter set to: technical-manual-w11663204-revb.pdf

    Mechanic [maytag]: What is the resistance of the drain pump?
    Assistant: The resistance should be 14-25 ohms.

The active filter is shown in the prompt. Queries with the filter active will only retrieve chunks from the selected manual.

### Keyboard navigation

The CLI supports standard readline shortcuts:
- Up/down arrows - cycle through previous queries in the session
- Left/right arrows - move cursor within the input line
- Ctrl+A / Ctrl+E - jump to start/end of line

### Confidence warnings

If the top retrieved result is a weak match for the query (cosine distance > 0.55), the system prints a warning before the answer:

    Note: Limited relevant documentation found - answer may be incomplete.

This typically means the question is outside the scope of the loaded manuals, or the terminology used does not closely match the documentation.

---

## Query Logging

Every query is logged to a daily JSON file under `logs/`. Each entry records the query, rewritten query (if applicable), the answer, source citations, retrieval distance, and timestamp. This is useful for reviewing what mechanics are asking and identifying gaps in documentation coverage.

---

## Running Tests

    pytest tests/test_rag.py

The test suite covers the core RAG engine: correct answers for known fault codes, refusals for out-of-scope queries, and source attribution. The manual filter and streaming functions are validated in the manual test suite documented in `test/manual_test_suite.md`.

---

## Design Decisions and Known Issues

### Why pypdfium2 instead of pdfplumber

The initial implementation used `pdfplumber` (built on `pdfminer.six`). During early testing the system failed to answer basic Maytag fault code queries. Investigation showed that `pdfminer` was producing severely corrupted text from the Maytag PDF due to non-standard font encoding - 64 of 66 pages were affected. Switching to `pypdfium2`, which uses Google's PDFium engine, resolved the issue completely. The Midea manual was unaffected.

### Retrieval and fault code lookups

Fault codes like `F5E2` are essentially keywords with weak semantic similarity to natural language queries. Pure vector search does not handle exact identifier lookups well. The current mitigations are aggressive text cleaning (removing short line fragments that dilute chunk embeddings) and a higher top_k (15 instead of the typical 3-5). The proper production fix would be hybrid search (BM25 + vector, reranked).

### Ambiguous cross-manual queries

A query like "What model is this washer?" contains no device-specific terms, so retrieval is determined by which manual's content happens to score highest. Without a filter active, this can silently return information for the wrong machine. The `/filter` command is the intended mitigation - mechanics should scope their session to the manual they are working with.

### Conversation history and grounding

Each prior exchange added to the prompt consumes context window space that would otherwise hold retrieved documentation. The history window is limited to the last 2 exchanges (4 messages) to prevent history from displacing retrieved context and weakening the grounding constraint. Out-of-scope refusals hold reliably within this window.

### Table extraction limitations

Some information in the manuals is presented in multi-column tables. When extracted as flat text, column relationships can be lost. The known case is the Manual Overview Test Mode table in the Maytag manual, where LOW SPIN and HIGH SPIN both extract to the same LED code (8 1) because the visual row separation is not preserved in plain text. This causes the system to refuse rather than risk an ambiguous answer. The fix would be table-aware preprocessing that renders each row as self-contained prose before chunking.

---

## Production Considerations

This is a single-machine PoC. Moving to production would require:

- **Hybrid search** - BM25 keyword search combined with vector search and a reranker (e.g. Cohere Rerank). Essential for fault code and part number lookups.
- **Hosted vector DB** - ChromaDB local is not suitable for multi-user or cloud deployment. Pinecone, Weaviate, or pgvector would be appropriate alternatives.
- **Smarter chunking** - Section-aware chunking that splits at heading boundaries rather than fixed character counts. Keeps related content together and avoids splitting tables.
- **PDF quality validation** - Automated check of extraction output before ingestion to flag encoding issues or empty pages before they silently degrade retrieval quality.
- **Authentication** - The current CLI has no user authentication or session isolation.
- **Dynamic manual filter** - `/filter` currently uses hardcoded aliases (`maytag`, `midea`). With more manuals this does not scale. The filter should be driven dynamically from the vector store contents, letting mechanics select by filename or index rather than a predefined alias.