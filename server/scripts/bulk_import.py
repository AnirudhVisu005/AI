#!/usr/bin/env python3
"""Bulk import script for FAQs, Errors, and Manuals via Admin API."""
import sys
import json
import requests

API_BASE = 'http://127.0.0.1:8000/api/admin'

def import_items(kind: str, path: str):
    with open(path, 'r', encoding='utf-8') as f:
        arr = json.load(f)
    for item in arr:
        url = f"{API_BASE}/{kind}"
        r = requests.post(url, json=item)
        if r.status_code >= 400:
            print('Failed to import', item, '->', r.status_code, r.text)
        else:
            print('Imported', r.json().get('id'))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: bulk_import.py <faqs|errors|manuals> <file.json>')
        sys.exit(1)
    kind = sys.argv[1]
    path = sys.argv[2]
    if kind not in ('faqs', 'errors', 'manuals'):
        print('Kind must be one of faqs|errors|manuals')
        sys.exit(1)
    import_items(kind, path)
