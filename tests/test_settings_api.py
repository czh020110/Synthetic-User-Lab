from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.stores import get_entity_store

client = TestClient(app)


def setup_function():
    get_entity_store().clear()


def test_get_frontend_settings_returns_defaults():
    resp = client.get('/api/v1/settings/frontend')
    assert resp.status_code == 200
    data = resp.json()['data']
    assert data['theme'] == 'light'
    assert data['locale'] == 'zh-CN'
    assert data['default_headless'] is True
    assert data['default_max_steps'] == 30


def test_update_frontend_settings_persists_changes():
    resp = client.put(
        '/api/v1/settings/frontend',
        json={
            'theme': 'dark',
            'locale': 'en-US',
            'default_headless': False,
            'refresh_interval_ms': 8000,
            'default_run_name': 'night-run',
            'default_max_steps': 18,
            'notify_run_failed': False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()['data']
    assert data['theme'] == 'dark'
    assert data['locale'] == 'en-US'
    assert data['default_headless'] is False
    assert data['refresh_interval_ms'] == 8000
    assert data['default_run_name'] == 'night-run'
    assert data['default_max_steps'] == 18
    assert data['notify_run_failed'] is False

    resp2 = client.get('/api/v1/settings/frontend')
    data2 = resp2.json()['data']
    assert data2['theme'] == 'dark'
    assert data2['default_max_steps'] == 18


def test_update_frontend_settings_validation():
    resp = client.put('/api/v1/settings/frontend', json={'refresh_interval_ms': 500})
    assert resp.status_code == 422
