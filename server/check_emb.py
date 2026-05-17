from retrieval.embedding_index import EmbeddingIndex, MODEL_NAME, faiss, INDEX_PATH, META_PATH
print('faiss available:', faiss is not None)
e = EmbeddingIndex()
print('EmbeddingIndex.model is None:', e.model is None)
print('EmbeddingIndex.index is None:', e.index is None)
print('INDEX_PATH exists:', INDEX_PATH.exists())
print('META_PATH exists:', META_PATH.exists())
