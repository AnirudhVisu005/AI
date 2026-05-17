# Technical Documentation — Offline Support Chatbot

Generated: May 17, 2026

This document is a complete, repository-specific technical manual and reverse-engineered architecture report for the project in this workspace (frontend `client/`, backend `server/`). It reconstructs runtime behavior, explains internal flows, traces AI / retrieval logic, lists improvements, and provides a professor-friendly explanation.

NOTE: This document was created by statically analyzing repository files. Where runtime configuration or optional external libraries influence behavior (for example `google-genai`, FAISS, or PyTorch), the document flags assumptions and confidence levels explicitly.

---

## Quick facts

- Frontend: React + Vite single-page app (`client/src/App.tsx`, `client/src/main.tsx`).
- Backend: FastAPI app (`server/app/main.py`) served by Uvicorn.
- Local DB: SQLite file at `server/data/support.db` (created by `bootstrap()` on startup).
- Retrieval: Hybrid for semantic + lexical search — BM25 (`rank_bm25`) + dense embeddings (SentenceTransformers + FAISS) under `server/retrieval/`.
- Optional LLM: `google-genai` client when `GEMINI_API_KEY` is set; otherwise the system returns local content.
- Admin: CRUD endpoints for FAQs, Manuals, and Error Fixes; frontend admin UI in `client/src/App.tsx`.

Confidence: high for code-derived flows; moderate when optional native/remote libs are absent at runtime (document highlights these cases).

---

## Table of Contents

1. Project Overview
2. Complete Tech Stack Analysis
3. Repository Structure Analysis (file-by-file)
4. Frontend Architecture
5. Backend Architecture
6. AI Chatbot Internal Workflow (deep)
7. Database & Storage
8. API Reference (every endpoint)
9. Authentication & Security
10. Environment Variables & Configuration
11. Deployment & DevOps
12. Execution Flow Reconstruction
13. Dependency Analysis
14. Code Quality & Architecture Review
15. Improvement Recommendations (ranked)
16. Master System Summary
17. HOW TO EXPLAIN THIS PROJECT TO A PROFESSOR

---

## 1. PROJECT OVERVIEW

What the application does (simple):

An offline-first, local support chatbot web application. It provides contextual help, FAQs, step-by-step manuals, and suggested fixes for errors relevant to the user's current UI page. Administrators can add, edit, and delete content via an Admin panel. The backend can further synthesize answers via an optional external LLM.

Core purpose: deliver localized, private, offline-capable support content integrated with an SPA UI.

Target users: end-users of the parent application who need help and internal administrators who manage knowledge content.

Major features:

- Chat UI with context-aware responses (current page context).
- Guided step-by-step mode to produce actionable instructions.
- Admin CRUD UIs for FAQs, Manuals, and Error Fixes.
- Simple analytics for chat usage.
- Hybrid retrieval (BM25 + embeddings) and optional LLM synthesis.

High-level architecture: Single-page React client communicates with a FastAPI backend over HTTP. Backend reads and writes a local SQLite DB, runs retrieval logic (BM25 + FAISS), optionally calls a cloud LLM, and serves JSON responses to the frontend.

---

## 2. COMPLETE TECH STACK ANALYSIS

### Frontend Stack

- Framework: React 18 (functional components, hooks).
- Bundler/build: Vite (`client/package.json`).
- Libraries: `lucide-react` for icons, `framer-motion` included as dependency; no router, no global state library.
- Styling: plain CSS (`client/src/styles.css`).
- Routing: none — single-screen app with internal tab state.
- State management: local React state within `App.tsx` (useState/useEffect).
- Websocket usage: None.
- Rendering strategy: client-side SPA.
- Authentication: none implemented.
- API communication: `fetch()` calls to backend endpoints under `/api/*`.

### Backend Stack

- Runtime: Python (FastAPI + Uvicorn)
- Framework: FastAPI (`server/app/main.py`)
- Middleware: CORS for dev origin(s) (`http://127.0.0.1:5173`, `http://localhost:5173`).
- Data store: SQLite local DB created under `server/data/support.db`.
- Retrieval: BM25 and dense embeddings (embedding model default `sentence-transformers/all-MiniLM-L6-v2`) + FAISS index.
- AI client: `google-genai` optional; environment variable `GEMINI_API_KEY` used to create `genai.Client`.
- Background processing: index build executed at startup (synchronous attempt), and a script `server/build_indexes.py` is provided for manual offline building.
- Tests: `pytest` (small test present in `server/tests/test_api.py`).

### AI/ML Stack

- LLM provider: `google-genai` (optional) used in `synthesize_with_ai()` if available.
- Embeddings: `sentence-transformers` via HuggingFace `AutoTokenizer` + `AutoModel` with mean pooling.
- Vector DB: FAISS (`faiss-cpu`) with saved artifacts at `server/data/faiss_index.bin` and `server/data/faiss_meta.pkl`.
- Sparse retrieval: BM25 via `rank_bm25`.
- RAG approach: hybrid combination implemented in `HybridRetriever` with dense matches weighted higher.
- Memory: only `chat_logs` used for analytics; no session-level or long-term conversation memory beyond that.

### Infrastructure Stack

- No Docker/CI files present in the repository.
- Deployment assumption: run `uvicorn` for backend and `vite` for frontend, or build frontend and serve static assets behind a reverse proxy.

---

## 3. COMPLETE REPOSITORY STRUCTURE ANALYSIS

Top-level layout (important paths):

- `client/` — React frontend
  - `src/App.tsx` — main UI and entire client logic (chat, admin, analytics).
  - `src/main.tsx` — React mount point.
  - `index.html` — SPA container.
  - `package.json` — dependencies and scripts.

- `server/` — FastAPI backend
  - `app/main.py` — core FastAPI app, endpoints, DB bootstrap, retrieval orchestration, AI synth.
  - `retrieval/embedding_index.py` — embedding pipeline (transformers + FAISS save/load).
  - `retrieval/bm25_index.py` — BM25 wrapper.
  - `retrieval/hybrid_retriever.py` — orchestrates BM25 + embeddings.
  - `build_indexes.py` — script to build indexes offline.
  - `data/` — seeds, DB, and optional FAISS artifacts:
    - `faq_seed.json`, `manual_seed.json`, `error_seed.json` — initial content.
    - `support.db` — created on bootstrap.
    - `faiss_index.bin`, `faiss_meta.pkl` — optional persisted FAISS artifacts.
  - `requirements.txt` — Python deps.
  - `tests/test_api.py` — baseline API test.

For each important file:

- `client/src/App.tsx`:
  - Purpose: Single-file implementation of UI and logic: chat send, admin CRUD, analytics display.
  - Why it exists: central UI for user and admin flows.
  - Imports: React, lucide-react icons, CSS.
  - Used by: the browser; makes `fetch()` calls to backend endpoints.

- `server/app/main.py`:
  - Purpose: FastAPI app with chat and admin endpoints.
  - Responsibilities: DB bootstrap, chat request handling (retrieval + optional AI), admin CRUD, analytics aggregation.
  - Imports: local retriever modules (`HybridRetriever`), `google.genai` optionally, sqlite3 and pydantic.
  - Runtime role: main server module loaded by Uvicorn.

- `server/retrieval/embedding_index.py`:
  - Purpose: encode texts using a transformer model and persist FAISS index and meta mapping.
  - Why it exists: support dense retrieval.
  - Imports: `faiss`, `transformers`, `torch` — optional; if missing the class handles it gracefully.
  - Depends on: local SQLite to read documents to index (used by `HybridRetriever`).

- `server/retrieval/bm25_index.py`:
  - Purpose: BM25 lexical ranking using `rank_bm25`.
  - Role: fallback OR complement dense retrieval for hybrid ranking.

- `server/retrieval/hybrid_retriever.py`:
  - Purpose: combine BM25 and embedding matches; weight dense matches higher and return top-k results.
  - Called from: `server/app/main.py` during startup and inside `chat()` if available.

... (other files are either seeds or small scripts — see file listing in repo root).

---

## 4. FRONTEND ARCHITECTURE ANALYSIS

App entrypoint: `client/src/main.tsx` mounts `App` into the root DOM node.

Component layout:

- `App` (monolithic) containing:
  - Sidebar: page selection (`Dashboard`, `Upload Page`, `Reports`, `Settings`), quick prompts, Guided Mode toggle, and tab nav (`Chat`, `Admin`, `Analytics`).
  - Main: Chat UI (messages, composer), Admin UI (CRUD forms for FAQs, Errors, Manuals), Analytics UI.

State management and flow:

- All state lives in `App`'s useState hooks: `messages`, admin lists (`adminFaqs`, `adminErrors`, `adminManuals`), analytics results, `page`, and `guidedMode`.
- Chat flow: user sends -> `sendQuestion()` posts JSON to `/api/chat` -> response appended to `messages`.

Message rendering:

- Assistant responses are plain text (`message.text`) and optional `steps` displayed as an ordered list. No markdown rendering.

Admin flows:

- `loadData()` fetches lists via GET endpoints; forms call POST/PUT/DELETE to manage entries; UI reloads data after changes.

Analytics:

- GET `/api/admin/analytics` returns `total_questions`, `top_questions`, and `by_page` which frontend displays as simple stats.

Networks & integration:

- Frontend uses relative fetch calls (`/api/*`) — assumes backend is served on same origin or proxied in dev.

UX notes:

- No streaming: frontend waits for full JSON payload; loading indicator shown while awaiting response.
- Guided mode toggles whether `guided_mode` flag sent to server; backend produces step lists based on this.

---

## 5. BACKEND ARCHITECTURE ANALYSIS

Startup sequence (`server/app/main.py`):

1. Uvicorn loads `main` module.
2. FastAPI registers endpoints and middleware.
3. `@app.on_event("startup")` -> `bootstrap()` called:
   - Creates DB tables if missing.
   - Loads seed JSON content into DB if tables empty.
4. If `HybridRetriever` available, attempt to instantiate and `build_indexes()` (reads DB and builds BM25 and embeddings + FAISS if deps present).

Request lifecycle (chat request):

1. `POST /api/chat` receives `ChatRequest`.
2. Insert question into `chat_logs` for analytics.
3. Retrieval: if `retriever` exists, call `retriever.retrieve()` and attempt to fetch the top record via `get_record_by_id()`. On errors or no results fallback to `best_match()` which computes overlap scoring across DB rows.
4. If no record found: return fallback `ChatResponse`.
5. If record found: optionally call `synthesize_with_ai()` if `ai_client` exists. If AI returns result, return it; otherwise return `answer_from_record()` (local text-based answer with `steps` generated by `make_steps()`).

Endpoint registration (summary):

- `GET /api/health` -> health and `ai_enabled` boolean.
- `POST /api/chat` -> main chat endpoint.
- Admin CRUD endpoints under `/api/admin/*` for faqs, manuals, errors.
- `GET /api/admin/analytics` -> analytics aggregation from `chat_logs`.

Concurrency and blocking:

- Endpoints defined as synchronous (`def`), FastAPI will run them in threadpool for concurrency. However heavy CPU-bound operations (transformer encoding, FAISS building) can block threads; recommendation to offload heavy tasks to background workers.

Error handling & logging:

- Minimal: some try/except print statements around optional systems; otherwise FastAPI default error handling.

---

## 6. AI CHATBOT INTERNAL WORKFLOW (DETAILED)

This section traces the pipeline from a user message to the final AI response.

Overall flow (short):

User Message -> Frontend -> POST `/api/chat` -> Backend logs query -> Retrieval (HybridRetriever or best_match) -> Map id -> Optionally call LLM (synthesize_with_ai) -> Return ChatResponse -> Frontend renders.

Detailed technical flow:

1. Frontend sends JSON:

```json
{ "message": "How do I upload a file?", "page": "Upload Page", "guided_mode": false }
```

2. Backend `chat()` immediately logs the question:

```sql
INSERT INTO chat_logs (question, page) VALUES (?, ?)
```

3. Retrieval strategies (in order of preference):

- Hybrid retriever (if `HybridRetriever` instantiated at startup):
  - `HybridRetriever.retrieve()` runs:
    - BM25 query via `BM25Index.query(query, top_k)`.
    - Embedding query via `EmbeddingIndex.query(query, top_k)`.
    - Results combined: BM25 scores added and embedding scores multiplied by 2.0 then summed and top-k returned.
  - Backend selects top hit `(id,score)` and calls `get_record_by_id()` to fetch the corresponding DB record.

- Fallback `best_match()` if retriever missing or retrieval fails:
  - Reads all records from `faqs`, `manual_sections`, and `error_fixes`.
  - Tokenizes both query and record text using `tokenize()` (lowercased alpha-numeric tokens).
  - Computes overlap-based score plus `page_bonus` and `title_bonus`.
  - Selects top record if score > 0.

4. If no record found -> return fallback Response (instructions to rephrase/add an FAQ).

5. If record found -> synthesize response. Two possibilities:

- AI synthesis (`synthesize_with_ai`) if `ai_client` available:
  - Build a prompt embedding the `page`, `query`, and `record` title/body.
  - Instruct LLM not to hallucinate and to produce step-by-step instructions if `guided_mode`.
  - Call `ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)` and parse `response.text`.
  - Return ChatResponse with `answer=response.text`, `steps` from `make_steps()` if guided, `reference` = `AI Synthesized from: {record.title}` and `source_type` = `ai_{record.source_type}`.

- Local extraction fallback (`answer_from_record`) if no AI or AI fails:
  - Build `ChatResponse.answer` from the record body.
  - Build `steps` using `make_steps()` which depends on source type (`faq`, `manual`, `error`) and `guided_mode`.

6. Frontend receives JSON response and appends assistant message to chat.

Token management, hallucination prevention and limits:

- Tokenization for embeddings is handled by the HuggingFace tokenizer in `EmbeddingIndex._encode_texts()`; `truncation=True` reduces token overflow.
- No explicit prompt chunking or multi-doc assembly in code; if record is very large this may exceed model limits — in practice seeds are small.
- Hallucination mitigation is a single prompt instruction: "Do NOT make up facts outside the provided content." This reduces hallucination probability but is not a guarantee.

Flow diagram (ASCII):

```
User (browser)
  -> POST /api/chat {message,page,guided_mode}
     -> server.app.chat()
         -> INSERT chat_logs
         -> if HybridRetriever: hits = retriever.retrieve(message)
             -> if hits: id = hits[0]; record = get_record_by_id(id)
         -> else: record = best_match(...)
         -> if not record: return fallback ChatResponse
         -> ai_resp = synthesize_with_ai(message, record, guided_mode)
            -> if ai_resp: return ai_resp
         -> else: return answer_from_record(record, guided_mode)
  <- Frontend displays ChatResponse
```

Confidence: high where code paths are explicit. Areas of uncertainty: actual LLM shape/fields returned by `google-genai`, since client usage shown as `models.generate_content` and `response.text` is used.

---

## 7. DATABASE & STORAGE ANALYSIS

SQLite (`server/data/support.db`)

- Tables (created in `bootstrap()`):
  - `faqs` (id, question, answer, tags, page, updated_at)
  - `manual_sections` (id, title, content, tags, page, updated_at)
  - `error_fixes` (id, error_key, message, fix, page, updated_at)
  - `chat_logs` (id, question, page, timestamp)

- Seeds: `server/data/faq_seed.json`, `server/data/manual_seed.json`, `server/data/error_seed.json` used to populate tables if empty.

Vector storage (FAISS):

- When `EmbeddingIndex.build()` runs it creates a FAISS `IndexFlatIP` and writes it to `server/data/faiss_index.bin` and pickles `faiss_meta.pkl` with the id mapping.
- `EmbeddingIndex.load()` will read these files to restore the index without re-encoding.

Storage notes:

- No DB indices other than primary keys; consider adding indexes for frequent queries or migrating to Postgres for concurrency.
- Ensure safe backups of `support.db` and FAISS artifacts if used in production.

---

## 8. COMPLETE API DOCUMENTATION

All endpoints live in `server/app/main.py`. For each endpoint the request/response and side-effects are summarized below.

- `GET /api/health`
  - Purpose: health check and AI availability.
  - Response: `{ "status": "ok", "ai_enabled": <bool> }`.

- `POST /api/chat`
  - Purpose: main chat endpoint. Accepts `ChatRequest`:
    - `message` (string), `page` (string), `guided_mode` (bool), `current_error` (optional string).
  - Behavior: logs question, runs retrieval, optionally calls AI, returns `ChatResponse`:
    - `answer` (string), `steps` (list), `reference` (string|null), `source_type` (string)
  - Side effects: INSERT into `chat_logs`.

- `GET /api/admin/faqs` — list FAQs.
- `POST /api/admin/faqs` — create FAQ, body: `question`, `answer`, `tags`, `page`. Returns created id.
- `PUT /api/admin/faqs/{faq_id}` — update FAQ.
- `DELETE /api/admin/faqs/{faq_id}` — delete FAQ.

- `GET /api/admin/manuals` — list manuals.
- `POST /api/admin/manuals` — create manual (expects `title`, `content`, optionally `tags`, `page`).
- `PUT /api/admin/manuals/{manual_id}` — update manual.
- `DELETE /api/admin/manuals/{manual_id}` — delete manual.

- `GET /api/admin/errors` — list error entries.
- `POST /api/admin/errors` — create error entry (expects `error_key`, `message`, `fix`, optional `page`).
- `PUT /api/admin/errors/{error_id}` — update error entry.
- `DELETE /api/admin/errors/{error_id}` — delete error entry.

- `GET /api/admin/analytics` — Returns aggregate analytics from `chat_logs`:
  - `{ total_questions, top_questions: [{question,count}], by_page: [{page,count}] }`.

Security: all admin endpoints currently unsecured — authentication is recommended for production.

---

## 9. AUTHENTICATION & SECURITY

Current state:

- No auth implemented. Admin endpoints can be called by any client with network access.
- DB queries parameterized to avoid SQL injection.
- CORS restricted to dev origins only in code, but must be tightened for production.

Risks:

- Unauthorized modification of knowledge base (admin endpoints must be protected).
- Rate-limiting absent — potential DoS via POST /api/chat.
- LLM API key management: `GEMINI_API_KEY` stored in environment; ensure it is kept secret (do not commit to repo).

Recommended mitigations (high priority):

1. Add authentication (JWT or session cookies) and protect admin endpoints.
2. Add rate limiting (e.g., `slowapi` or Nginx limit) for chat endpoints.
3. Use HTTPS and reverse proxy in production.
4. Add request-size limits and validation to avoid huge payloads to LLM.

---

## 10. ENVIRONMENT VARIABLES & CONFIGURATION

Variables used or implied by code:

- `GEMINI_API_KEY`
  - Where used: `server/app/main.py` to initialize `genai.Client(api_key=API_KEY)`.
  - Purpose: allows calling `google-genai` API for text synthesis.
  - Effect: If absent, `ai_client` remains `None` and LLM synthesis is skipped.

- `EMBEDDING_MODEL`
  - Where used: `server/retrieval/embedding_index.py` default is `sentence-transformers/all-MiniLM-L6-v2` if not set.
  - Purpose: switch the embedding model used for dense retrieval.

Other config:

- `DATA_DIR` (default `server/data/`) — used to persist DB and index artifacts.

Note: `python-dotenv` is present in `requirements.txt` but code does not explicitly call `load_dotenv()`; if you want `.env` support add a short snippet loading `dotenv` on startup.

---

## 11. DEPLOYMENT & DEVOPS

Local development steps (recommended):

Backend (PowerShell example used in terminals):

```powershell
cd server
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# optionally build indexes
python build_indexes.py
# run server
$env:PYTHONPATH = "."
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd client
npm install
npm run dev
# or build
npm run build
```

Production suggestions:

- Add `Dockerfile` and `docker-compose.yml` to containerize backend and serve built frontend via Nginx.
- Use a process supervisor (systemd or gunicorn/uvicorn with multiple workers) and place behind Nginx for TLS and static serving.
- Use a secrets manager for `GEMINI_API_KEY` and other secrets.
- Offload heavy embedding/index-building tasks to a background service (Celery, RQ) rather than building in-process at startup.

CI/CD: not present; add tests, linting, and build steps in the pipeline.

Monitoring and Logging: implement structured logging and export Prometheus metrics for request rates, error counts, and LLM usage.

---

## 12. EXECUTION FLOW RECONSTRUCTION

### Frontend startup

- Browser loads `index.html` served by Vite or static server.
- `client/src/main.tsx` mounts `App`.
- `App` runs `loadData()` to populate admin lists (calls `/api/admin/*` endpoints).

### Backend startup

- Uvicorn loads `server/app/main.py` (module import path depends on working dir; repository used `python -m uvicorn main:app` in `server/`).
- `startup()` event calls `bootstrap()` to create DB tables and seed initial data if needed.
- If `HybridRetriever` import and dependencies succeed, `retriever = HybridRetriever(DB_PATH)` and `retriever.build_indexes()` attempted.

### Chat message lifecycle (full trace)

1. User types and clicks Send; frontend calls `POST /api/chat`.
2. Backend `chat()` inserts the chat log into `chat_logs`.
3. Backend runs retrieval — `HybridRetriever.retrieve()` if available else `best_match()`.
4. If retrieval returns a record, attempt `synthesize_with_ai()`.
   - If `ai_client` exists and returns text, use it.
   - Else use `answer_from_record()`.
5. Backend returns JSON `ChatResponse`.
6. Frontend appends assistant message and renders `steps` as ordered list if present.

---

## 13. DEPENDENCY ANALYSIS

Frontend (`client/package.json`):

- `react`, `react-dom` — essential UI framework.
- `vite` — dev server and bundler.
- `lucide-react` — icons used across UI.
- `framer-motion` — animation lib present but usage minimal.

Backend (`server/requirements.txt`):

- `fastapi`, `uvicorn[standard]` — web framework and server.
- `pydantic` — data validation.
- `sentence-transformers`, `transformers`, `torch` — embedding pipeline.
- `faiss-cpu` — vector index store.
- `rank-bm25` — lexical retrieval.
- `google-genai` — optional LLM client.
- `python-dotenv` — optional env loader.

Risky or heavy libraries:

- `faiss-cpu` and `torch` are heavy native packages — require compatible platform builds. `sentence-transformers` will download model artifacts.
- `google-genai` introduces network calls and cost considerations.

Recommendation: pin versions carefully, ensure platform compatibility for FAISS/torch, and consider packaging model artifacts if you require offline embeddings.

---

## 14. CODE QUALITY & ARCHITECTURE REVIEW

Strengths:

- Simple and pragmatic design with a small codebase easy to understand.
- Modular retrieval code separated under `server/retrieval`.

Weaknesses & technical debt:

- Monolithic `App.tsx` frontend — should be split into components.
- Admin endpoints open without authentication.
- Heavy operations (index building, model inference) executed synchronously and may block server threads.
- No structured logging, monitoring, or CI.

Scalability concerns:

- SQLite is not suitable for high concurrency; consider Postgres for scale.
- FAISS and transformer encoding need careful orchestration for large corpora.

Security concerns:

- Admin endpoints unsecured.

---

## 15. IMPROVEMENT RECOMMENDATIONS

Critical (must do before production):

1. Add authentication & authorization for admin endpoints.
2. Add rate-limiting and request-size limits on `/api/chat`.
3. Secure `GEMINI_API_KEY` in a secrets manager or environment, do not commit secrets.

High-value:

1. Move heavy tasks (embedding builds, model synth) to background workers and expose status endpoints.
2. Componentize frontend and add unit tests.
3. Add streaming responses (SSE/WebSocket) for long LLM generation.

Optional:

1. Provide Dockerfiles and `docker-compose.yml` for reproducible deployments.
2. Replace SQLite with Postgres for multi-worker deployments.

---

## 16. MASTER SYSTEM SUMMARY

This application is a compact, offline-first support chatbot composed of a React SPA and a FastAPI backend. Content (FAQs, manuals, error fixes) is stored locally in SQLite and seeded from JSON files. A hybrid retrieval pipeline (BM25 + sentence-transformer embeddings + FAISS) resolves user queries to DB records. Optionally, a cloud LLM (`google-genai`) can synthesize responses from the retrieved record (prompting includes explicit instructions to avoid hallucination). Admins edit knowledge directly via REST endpoints; chat usage logs are stored for analytics. In production this design needs authentication, background processing for heavy tasks, and a hardened deployment environment.

Key file references (entrypoints):

- Frontend UI: [client/src/App.tsx](client/src/App.tsx)
- Backend app: [server/app/main.py](server/app/main.py)
- Retrieval: [server/retrieval/hybrid_retriever.py](server/retrieval/hybrid_retriever.py)
- Embeddings: [server/retrieval/embedding_index.py](server/retrieval/embedding_index.py)
- BM25: [server/retrieval/bm25_index.py](server/retrieval/bm25_index.py)

---

## 17. HOW TO EXPLAIN THIS PROJECT TO A PROFESSOR

Simple spoken explanation:

"This is a small web app that offers support to users directly inside an application. The frontend is a single-page React app where users type questions and admins manage content. The backend stores FAQs, manuals and error fixes in a local SQLite database. When a user asks something the system looks up the most relevant entries using a hybrid search (keyword matching plus semantic embeddings), and either returns the matched text or asks a connected language model to rewrite it into a friendly answer. Everything runs locally so it can be used offline or in a private environment."

If professor asks "How does search work?":

- "We run two searches: a lexical BM25 search and a semantic vector search using sentence-transformer embeddings and FAISS. We combine scores from both to pick the best entry; if no match, we fall back to a simple token-overlap heuristic."

If professor asks "How do you avoid hallucinations when using the LLM?":

- "We constrain the prompt by including only the retrieved record content and explicitly instruct the model not to invent facts. For production you should add verification, citations, and post-checks to ensure accuracy."

Short speaking scripts:

- 30-second: "It’s a React + FastAPI support bot that answers user queries from a local knowledge base. It uses hybrid retrieval and optionally a cloud LLM to synthesize readable answers. Admins update content via a built-in admin panel."
- 2-minute: (expand to include the flow: user->frontend->backend->retriever->LLM fallback->response)
- 5-minute: (include architecture diagram, indexing and embedding details, DB schema, and improvement list — you can rely on this document as speaker notes).

Likely viva questions & ideal answers (short):

- Q: "Why hybrid retrieval?" A: "Combines strengths of both lexical methods (BM25) and semantic understanding (dense embeddings) — reduces misses due to paraphrase and keyword variance." 
- Q: "How to scale?" A: "Move to Postgres, external vector DB, and run heavy tasks asynchronously." 
- Q: "What are the main risks?" A: "No auth, blocking heavy ops, and potential hallucinations from LLM — mitigations are recommended here."

---

### Final notes

If you want I can:

- Add this file to the repository (I have done so here).
- Add a `README.md` referencing this documentation and run instructions.
- Implement production-grade changes (auth, Dockerfile, background workers, streaming responses).

If you want me to implement any of the recommended changes or generate a `README` and `Dockerfile`, tell me which task to start next.

---

END OF DOCUMENT
