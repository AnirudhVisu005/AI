from __future__ import annotations

import os
import pickle
from typing import List, Tuple
from pathlib import Path

try:
    import faiss
except Exception:
    faiss = None

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
except Exception:
    AutoTokenizer = None
    AutoModel = None
    torch = None

BASE = Path(__file__).resolve().parent.parent
MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
INDEX_PATH = BASE / "data" / "faiss_index.bin"
META_PATH = BASE / "data" / "faiss_meta.pkl"


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # first element of model_output contains token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


class EmbeddingIndex:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name) if AutoTokenizer else None
        self.model = AutoModel.from_pretrained(model_name) if AutoModel else None
        self.index = None
        self.id_to_meta = {}

    def _encode_texts(self, texts: List[str]):
        if not self.tokenizer or not self.model or not torch:
            return None
        self.model.eval()
        with torch.no_grad():
            encoded = self.tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
            outputs = self.model(**encoded)
            embeddings = mean_pooling(outputs, encoded['attention_mask'])
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            return embeddings.cpu().numpy()

    def build(self, records: List[Tuple[int, str]]):
        if not faiss or not self.model:
            return
        texts = [t for _id, t in records]
        ids = [int(_id) for _id, _ in records]
        embeddings = self._encode_texts(texts)
        if embeddings is None:
            return
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        self.index = index
        self.id_to_meta = {i: ids[i] for i in range(len(ids))}
        self._save()

    def _save(self):
        if not faiss:
            return
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(META_PATH, "wb") as f:
            pickle.dump(self.id_to_meta, f)

    def load(self):
        if not faiss or not INDEX_PATH.exists() or not META_PATH.exists():
            return
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self.id_to_meta = pickle.load(f)

    def query(self, text: str, top_k: int = 10):
        if not self.model or not self.index:
            return []
        emb = self._encode_texts([text])
        if emb is None:
            return []
        faiss.normalize_L2(emb)
        D, I = self.index.search(emb, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            doc_id = self.id_to_meta.get(idx)
            results.append((doc_id, float(score)))
        return results
