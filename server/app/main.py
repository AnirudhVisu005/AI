from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Setup AI Client if available
try:
    from google import genai
    # We use the provided key or look for an env var
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if API_KEY:
        ai_client = genai.Client(api_key=API_KEY)
    else:
        ai_client = None
except ImportError:
    ai_client = None

# Optional hybrid retriever
try:
    from retrieval.hybrid_retriever import HybridRetriever
except Exception:
    HybridRetriever = None

retriever = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "support.db"
FAQ_SEED = DATA_DIR / "faq_seed.json"
MANUAL_SEED = DATA_DIR / "manual_seed.json"
ERROR_SEED = DATA_DIR / "error_seed.json"


class ChatRequest(BaseModel):
    message: str
    page: str = "Dashboard"
    guided_mode: bool = False
    current_error: str | None = None


class ChatResponse(BaseModel):
    answer: str
    steps: list[str] = Field(default_factory=list)
    reference: str | None = None
    source_type: str


class FaqUpsert(BaseModel):
    question: str
    answer: str
    tags: str = ""
    page: str = "Dashboard"


@dataclass
class SearchRecord:
    id: int
    title: str
    body: str
    tags: str
    page: str
    source_type: str


app = FastAPI(title="Offline Support Chatbot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def bootstrap() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                page TEXT NOT NULL DEFAULT 'Dashboard',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS manual_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                page TEXT NOT NULL DEFAULT 'Dashboard',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS error_fixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_key TEXT NOT NULL,
                message TEXT NOT NULL,
                fix TEXT NOT NULL,
                page TEXT NOT NULL DEFAULT 'Dashboard',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                page TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        if connection.execute("SELECT COUNT(*) FROM faqs").fetchone()[0] == 0:
            load_seed_table(connection, FAQ_SEED, "faqs")
        if connection.execute("SELECT COUNT(*) FROM manual_sections").fetchone()[0] == 0:
            load_seed_table(connection, MANUAL_SEED, "manual_sections")
        if connection.execute("SELECT COUNT(*) FROM error_fixes").fetchone()[0] == 0:
            load_seed_table(connection, ERROR_SEED, "error_fixes")


def load_seed_table(connection: sqlite3.Connection, path: Path, table: str) -> None:
    if not path.exists():
        return

    rows = json.loads(path.read_text(encoding="utf-8"))
    if table == "faqs":
        connection.executemany(
            "INSERT INTO faqs (question, answer, tags, page) VALUES (?, ?, ?, ?)",
            [(row["question"], row["answer"], row.get("tags", ""), row.get("page", "Dashboard")) for row in rows],
        )
    elif table == "manual_sections":
        connection.executemany(
            "INSERT INTO manual_sections (title, content, tags, page) VALUES (?, ?, ?, ?)",
            [(row["title"], row["content"], row.get("tags", ""), row.get("page", "Dashboard")) for row in rows],
        )
    elif table == "error_fixes":
        connection.executemany(
            "INSERT INTO error_fixes (error_key, message, fix, page) VALUES (?, ?, ?, ?)",
            [
                (row["error_key"], row["message"], row["fix"], row.get("page", "Dashboard"))
                for row in rows
            ],
        )


def tokenize(text: str) -> Counter[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(words)


def score(query: str, record: SearchRecord, page: str) -> float:
    query_tokens = tokenize(query)
    record_tokens = tokenize(f"{record.title} {record.body} {record.tags} {record.page}")
    overlap = sum(min(query_tokens[token], record_tokens[token]) for token in query_tokens)
    page_bonus = 3.0 if record.page.lower() == page.lower() else 0.0
    title_bonus = 2.0 if any(token in record.title.lower() for token in query_tokens) else 0.0
    return overlap + page_bonus + title_bonus


def read_records(connection: sqlite3.Connection, table: str) -> list[SearchRecord]:
    if table == "faqs":
        rows = connection.execute("SELECT id, question, answer, tags, page FROM faqs").fetchall()
        return [SearchRecord(row[0], row[1], row[2], row[3], row[4], "faq") for row in rows]
    if table == "manual_sections":
        rows = connection.execute("SELECT id, title, content, tags, page FROM manual_sections").fetchall()
        return [SearchRecord(row[0], row[1], row[2], row[3], row[4], "manual") for row in rows]
    rows = connection.execute("SELECT id, error_key, message, fix, page FROM error_fixes").fetchall()
    return [SearchRecord(row[0], row[1], row[3], row[2], row[4], "error") for row in rows]


def best_match(connection: sqlite3.Connection, query: str, page: str, current_error: str | None = None) -> SearchRecord | None:
    candidates = read_records(connection, "error_fixes") + read_records(connection, "faqs") + read_records(connection, "manual_sections")
    if current_error:
        error_candidates = [record for record in candidates if record.source_type == "error"]
        if error_candidates:
            candidates = error_candidates

    if not candidates:
        return None

    scored = sorted(((score(query, record, page), record) for record in candidates), key=lambda item: item[0], reverse=True)
    top_score, top_record = scored[0]
    return top_record if top_score > 0 else None


def get_record_by_id(connection: sqlite3.Connection, record_id: int) -> SearchRecord | None:
    # Search in faqs
    row = connection.execute("SELECT id, question, answer, tags, page FROM faqs WHERE id = ?", (record_id,)).fetchone()
    if row:
        return SearchRecord(row[0], row[1], row[2], row[3], row[4], "faq")

    row = connection.execute("SELECT id, title, content, tags, page FROM manual_sections WHERE id = ?", (record_id,)).fetchone()
    if row:
        return SearchRecord(row[0], row[1], row[2], row[3], row[4], "manual")

    row = connection.execute("SELECT id, error_key, message, fix, page FROM error_fixes WHERE id = ?", (record_id,)).fetchone()
    if row:
        # Map: title=error_key, body=fix, tags=message
        return SearchRecord(row[0], row[1], row[3], row[2], row[4], "error")

    return None


def make_steps(record: SearchRecord, guided_mode: bool) -> list[str]:
    if record.source_type == "error":
        if guided_mode:
            return [
                "Stop at the screen where the error appears.",
                "Check the exact error message or code.",
                record.body,
                "Retry the action after the fix.",
            ]
        return [record.body]

    if guided_mode:
        return [
            f"Open the {record.page}.",
            f"Follow the action described in '{record.title}'.",
            "Confirm the expected result appears on screen.",
        ]

    if record.source_type == "faq":
        return [record.body]

    return [record.body]


def answer_from_record(record: SearchRecord, guided_mode: bool) -> ChatResponse:
    reference_text = record.title
    if record.source_type == "manual":
        reference_text = f"{record.page} · {record.title}"
        
    return ChatResponse(
        answer=record.body,
        steps=make_steps(record, guided_mode),
        reference=reference_text,
        source_type=record.source_type,
    )

def synthesize_with_ai(query: str, record: SearchRecord, guided_mode: bool, page: str) -> ChatResponse | None:
    if not ai_client:
        return None
        
    prompt = f"""
    You are an intelligent app assistant helping a user on the '{page}' page.
    User's question: "{query}"
    
    Here is the exact information you found from the local '{record.source_type}' database:
    Title: {record.title}
    Content: {record.body}
    
    Task:
    Write a helpful, direct answer combining the context above. If they asked for a tutorial or guided_mode is True ({guided_mode}), provide step-by-step instructions. Keep it concise, friendly, and simple.
    Do NOT make up facts outside the provided content.
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # If guided mode is active, we can extract steps or just return the AI text
        steps = make_steps(record, guided_mode) if guided_mode else []
        reference_text = f"AI Synthesized from: {record.title}"
        
        return ChatResponse(
            answer=response.text,
            steps=steps,
            reference=reference_text,
            source_type=f"ai_{record.source_type}",
        )
    except Exception as e:
        print(f"AI Generation failed: {e}")
        return None


@app.on_event("startup")
def startup() -> None:
    bootstrap()
    global retriever
    if HybridRetriever is not None:
        try:
            retriever = HybridRetriever(DB_PATH)
            retriever.build_indexes()
        except Exception as e:
            print(f"Hybrid retriever initialization failed: {e}")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "ai_enabled": ai_client is not None}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    with connect() as connection:
        # Track the question for analytics
        connection.execute(
            "INSERT INTO chat_logs (question, page) VALUES (?, ?)",
            (request.message, request.page)
        )
        connection.commit()

        record = None
        # Prefer hybrid retriever if available
        try:
            if retriever is not None:
                hits = retriever.retrieve(request.message, top_k=5)
                if hits:
                    # pick top hit and fetch record
                    top_id, top_score = hits[0]
                    record = get_record_by_id(connection, top_id)
        except Exception:
            record = None

        # Fallback to classic best_match
        if record is None:
            record = best_match(connection, request.message, request.page, request.current_error)
        if record is None:
            return ChatResponse(
                answer="I could not find a direct match in the local data. Try a simpler keyword or add a new FAQ from the admin panel.",
                steps=[
                    "Rephrase the question with the feature name.",
                    "Add an FAQ if this is a common question.",
                ],
                reference=request.page,
                source_type="fallback",
            )
            
        # Try AI Synthesis
        ai_response = synthesize_with_ai(request.message, record, request.guided_mode, request.page)
        if ai_response:
            return ai_response

        # Fallback to pure local extraction
        return answer_from_record(record, request.guided_mode)


@app.get("/api/admin/faqs")
def list_faqs() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute("SELECT id, question, answer, tags, page FROM faqs ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


@app.post("/api/admin/faqs")
def create_faq(payload: FaqUpsert) -> dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO faqs (question, answer, tags, page) VALUES (?, ?, ?, ?)",
            (payload.question, payload.answer, payload.tags, payload.page),
        )
        connection.commit()
        return {"id": cursor.lastrowid, **payload.model_dump()}


@app.put("/api/admin/faqs/{faq_id}")
def update_faq(faq_id: int, payload: FaqUpsert) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            "UPDATE faqs SET question = ?, answer = ?, tags = ?, page = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.question, payload.answer, payload.tags, payload.page, faq_id),
        )
        connection.commit()
        return {"id": faq_id, **payload.model_dump()}


@app.delete("/api/admin/faqs/{faq_id}")
def delete_faq(faq_id: int) -> dict[str, Any]:
    with connect() as connection:
        connection.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
        connection.commit()
        return {"id": faq_id}


@app.get("/api/admin/manuals")
def list_manuals() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute("SELECT id, title, content, tags, page FROM manual_sections ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


@app.get("/api/admin/errors")
def list_errors() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute("SELECT id, error_key, message, fix, page FROM error_fixes ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


@app.get("/api/admin/analytics")
def analytics() -> dict[str, Any]:
    """Return top asked questions and per-page breakdown from chat_logs."""
    with connect() as connection:
        total = connection.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        top_questions = connection.execute(
            "SELECT question, COUNT(*) as count FROM chat_logs GROUP BY lower(question) ORDER BY count DESC LIMIT 20"
        ).fetchall()
        by_page = connection.execute(
            "SELECT page, COUNT(*) as count FROM chat_logs GROUP BY page ORDER BY count DESC"
        ).fetchall()
        return {
            "total_questions": total,
            "top_questions": [dict(row) for row in top_questions],
            "by_page": [dict(row) for row in by_page],
        }


@app.delete("/api/admin/faqs/{faq_id}")
def delete_faq(faq_id: int) -> dict[str, str]:
    with connect() as connection:
        connection.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
        connection.commit()
        return {"status": "deleted", "id": faq_id}


@app.post("/api/admin/manuals")
def create_manual(payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO manual_sections (title, content, tags, page) VALUES (?, ?, ?, ?)",
            (payload["title"], payload["content"], payload.get("tags", ""), payload.get("page", "Dashboard")),
        )
        connection.commit()
        return {"id": cursor.lastrowid, **payload}


@app.put("/api/admin/manuals/{manual_id}")
def update_manual(manual_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            "UPDATE manual_sections SET title = ?, content = ?, tags = ?, page = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload["title"], payload["content"], payload.get("tags", ""), payload.get("page", "Dashboard"), manual_id),
        )
        connection.commit()
        return {"id": manual_id, **payload}


@app.delete("/api/admin/manuals/{manual_id}")
def delete_manual(manual_id: int) -> dict[str, str]:
    with connect() as connection:
        connection.execute("DELETE FROM manual_sections WHERE id = ?", (manual_id,))
        connection.commit()
        return {"status": "deleted", "id": manual_id}


@app.post("/api/admin/errors")
def create_error(payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO error_fixes (error_key, message, fix, page) VALUES (?, ?, ?, ?)",
            (payload["error_key"], payload["message"], payload["fix"], payload.get("page", "Dashboard")),
        )
        connection.commit()
        return {"id": cursor.lastrowid, **payload}


@app.put("/api/admin/errors/{error_id}")
def update_error(error_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            "UPDATE error_fixes SET error_key = ?, message = ?, fix = ?, page = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload["error_key"], payload["message"], payload["fix"], payload.get("page", "Dashboard"), error_id),
        )
        connection.commit()
        return {"id": error_id, **payload}


@app.delete("/api/admin/errors/{error_id}")
def delete_error(error_id: int) -> dict[str, str]:
    with connect() as connection:
        connection.execute("DELETE FROM error_fixes WHERE id = ?", (error_id,))
        connection.commit()
        return {"status": "deleted", "id": error_id}

