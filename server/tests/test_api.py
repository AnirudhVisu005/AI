import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert 'ai_enabled' in r.json()

def test_faq_crud():
    # create
    payload = {'question':'test q','answer':'test a','tags':'test','page':'Dashboard'}
    r = client.post('/api/admin/faqs', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['question'] == 'test q'
    fid = data['id']
    # list
    r2 = client.get('/api/admin/faqs')
    assert any(f['id'] == fid for f in r2.json())
    # delete
    d = client.delete(f'/api/admin/faqs/{fid}')
    assert d.status_code == 200
