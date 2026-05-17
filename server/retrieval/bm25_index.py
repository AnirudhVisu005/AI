from __future__ import annotations

from typing import List, Tuple
try:
    from rank_bm25 import BM25Okapi
except Exception:
    BM25Okapi = None

import re


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    def __init__(self):
        self.bm25 = None
        self.docs = []
        self.ids = []

    def build(self, records: List[Tuple[int, str]]):
        if not BM25Okapi:
            return
        self.ids = [int(_id) for _id, _ in records]
        self.docs = [tokenize(t) for _id, t in records]
        self.bm25 = BM25Okapi(self.docs)

    def query(self, text: str, top_k: int = 10):
        if not self.bm25:
            return []
        tokens = tokenize(text)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = [(self.ids[idx], float(score)) for idx, score in ranked]
        return results
