import traceback
try:
    import sentence_transformers
    print('sentence_transformers ok')
    from sentence_transformers import SentenceTransformer
    print('SentenceTransformer OK')
except Exception as e:
    print('sentence_transformers failed:', e)
    traceback.print_exc()
try:
    import faiss
    print('faiss ok')
except Exception as e:
    print('faiss failed:', e)
    traceback.print_exc()
try:
    import torch
    print('torch ok', torch.__version__)
except Exception as e:
    print('torch failed:', e)
    traceback.print_exc()
