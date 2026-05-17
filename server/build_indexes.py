from retrieval.hybrid_retriever import HybridRetriever
from pathlib import Path

if __name__ == '__main__':
    r = HybridRetriever(Path('data/support.db'))
    r.build_indexes()
    print('Hybrid build finished')
