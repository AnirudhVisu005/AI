import sys, pkgutil
print('executable:', sys.executable)
print('sentence_transformers loader:', pkgutil.find_loader('sentence_transformers'))
print('faiss loader:', pkgutil.find_loader('faiss'))
print('torch loader:', pkgutil.find_loader('torch'))
