from __future__ import annotations

from typing import List, Tuple
from .embedding_index import EmbeddingIndex
from .bm25_index import BM25Index
import sqlite3
from pathlib import Path


class HybridRetriever:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        try:
            self.emb = EmbeddingIndex()
        except Exception:
            self.emb = None
        try:
            self.bm25 = BM25Index()
        except Exception:
            self.bm25 = None

    def build_indexes(self):
        # collect records
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = []
        for row in conn.execute("SELECT id, question AS title, answer AS body, tags, page FROM faqs").fetchall():
            rows.append((row[0], f"{row['title']}\n{row['body']}"))
        for row in conn.execute("SELECT id, title, content, tags, page FROM manual_sections").fetchall():
            rows.append((row[0], f"{row['title']}\n{row['content']}"))
        for row in conn.execute("SELECT id, error_key AS title, fix AS body, message, page FROM error_fixes").fetchall():
            rows.append((row[0], f"{row['title']}\n{row['body']}"))
        conn.close()

        if self.emb:
            try:
                self.emb.build(rows)
            except Exception:
                pass
        if self.bm25:
            try:
                self.bm25.build(rows)
            except Exception:
                pass

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        results = {}
        if self.bm25:
            for doc_id, score in self.bm25.query(query, top_k=top_k*2):
                results.setdefault(doc_id, 0.0)
                results[doc_id] += float(score)
        if self.emb:
            for doc_id, score in self.emb.query(query, top_k=top_k*2):
                results.setdefault(doc_id, 0.0)
                results[doc_id] += float(score) * 2.0  # give dense higher weight

        ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return ranked
