# 🏏 IPL AI Analyst

A multi-agent, LangGraph-orchestrated chatbot that answers natural-language questions about IPL cricket — batting/bowling stats, venues, team performance, head-to-head matchups, records, and general cricket knowledge — with a WhatsApp-style chat UI.

Ask things like:
- "How many runs did Virat Kohli score in 2023?"
- "Compare Bumrah and Rashid Khan's economy rates"
- "Best venue for chasing in the IPL"
- "Who has the most sixes at Wankhede?"

## How it works

Every question flows through a single **LangGraph** pipeline (`graph_pipeline.py`):

1. **Unified router** (`agents/unified_router.py`) — one LLM call classifies the question (smalltalk / out-of-scope / SQL / RAG / web search / multi-entity comparison / multi-aspect), resolves pronouns using conversation history, and — for smalltalk/out-of-scope — writes the reply directly. This replaced an earlier design that chained a ML intent classifier + separate pipeline/SQL-intent routers (up to 3 LLM calls per question).
2. **Dispatch** to the right node based on the route:
   - **SQL agents** (`agents/*_agent.py`: batting, bowling, team, season, venue, matchup) — generate and run SQL against a local DuckDB warehouse built from the IPL ball-by-ball dataset.
   - **RAG** (`agents/rag_hybrid.py`) — retrieves from a FAISS vector store over cricket knowledge docs for questions SQL can't answer (rules, records, narrative context).
   - **Web search** (`agents/search_orchestrator.py`, via Tavily) — for anything current/outside the local dataset.
   - **Multi-entity comparisons** — fans out one lookup per player/team (via LangGraph `Send`) and synthesizes a combined answer.
   - **Multi-aspect questions** — questions with two distinct sub-asks (e.g. "who scored the most runs, and what team does he play for") run as two chained lookups, feeding the first result's resolved entity into the second.
3. A **tiered SQL strategy**: a fast, non-reasoning model attempts the SQL query first (`fast_llm`); if the result looks unreliable (e.g. a named player doesn't actually appear in the result set — a sign of a dropped `WHERE` clause) it retries with a stronger model.
4. Every turn is logged to **Supabase** (query, generated SQL, RAG docs, search sources, response time, and optional 👍/👎 user feedback with reasons) for evaluation.

## Architecture

```
whatsapp_app.py / app.py   Streamlit UI
        │
        ▼
graph_pipeline.py           LangGraph StateGraph orchestration
        │
        ▼
agents/unified_router.py    Single-call routing + reference resolution
        │
   ┌────┼─────────┬─────────────┬───────────────┐
   ▼    ▼         ▼             ▼               ▼
 SQL   RAG    Web Search   Multi-entity     Multi-aspect
agents faiss   (Tavily)    fan-out/compare  chained lookup
   │
   ▼
DuckDB (database/ipl.duckdb) ← built from Data/*.csv on first run
```

**LLM providers:** Groq (primary, low-latency) with an NVIDIA-hosted fallback for the main reasoning model, and a small/fast model tier (with further Groq → NVIDIA fallbacks) dedicated to routing and first-pass SQL generation.

## Project structure

```
agents/            Router, SQL agents (batting/bowling/team/season/venue/matchup),
                    RAG, hybrid, search orchestrator, prompts, structured-output schemas
graph_pipeline.py   LangGraph pipeline definition (nodes, routing, fan-out, synthesis)
whatsapp_app.py     WhatsApp-styled Streamlit chat UI (current front end)
app.py              Earlier, non-WhatsApp Streamlit UI
IntentClassifier/   Legacy ML intent classifier (superseded by unified_router.py)
utils/              Player-name alias resolution (fuzzy matching via rapidfuzz)
memory/             Conversation memory + question rewriting
database/           DuckDB warehouse creation/access, Supabase client, query/eval logging
evaluation/         KPI + chart-quality metrics, evaluation dashboard
rag/                FAISS index and source documents for the RAG pipeline
Data/               Raw IPL CSVs (matches, deliveries, player/team/venue stats, etc.)
create_db.py        Builds database/ipl.duckdb from Data/*.csv on first run
build_vectorstore.py Builds the FAISS index for RAG
voice.py            Experimental voice input (mic recording)
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Requires Python 3.11 (see `runtime.txt`).

2. **Environment variables** — create a `.env` file (or use Streamlit secrets) with:
   ```
   GROQ_API_KEY=...
   NVIDIA_API_KEY=...
   TAVILY_API_KEY=...
   SUPABASE_URL=...
   SUPABASE_KEY=...
   ```

3. **Run the app**
   ```bash
   streamlit run whatsapp_app.py
   ```
   The DuckDB database is built automatically from `Data/*.csv` on first run if it doesn't already exist. Build the FAISS index once beforehand with `python build_vectorstore.py` if you want RAG answers available.

## Evaluation

`evaluation/` reads logged queries back from Supabase and computes response-quality and performance KPIs, viewable via `evaluation/dashboard.py`.

## Roadmap

- Voice interface extension ("Cricket Voice Analyst") using Groq Whisper for speech-to-text, TTS (ElevenLabs/Piper), and Twilio for phone-call access.
