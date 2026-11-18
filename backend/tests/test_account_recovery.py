import re
from datetime import datetime, timedelta

from app.api.v1 import auth
from app.core.config import settings
from app.models.recovery import RecoveryChallenge


def register(client):
    response = client.post('/api/v1/auth/register', json={
        'username': 'recovery_user', 'email': 'recover@example.com', 'password': 'oldpassword',
    })
    assert response.status_code == 200
    return response.json()['id']


def capture_email(monkeypatch):
    monkeypatch.setattr(settings, 'SMTP_HOST', 'smtp.example.com')
    monkeypatch.setattr(settings, 'SMTP_FROM', 'PiggyNest <noreply@example.com>')
    messages = []
    monkeypatch.setattr(auth, 'send_recovery_email', lambda to, subject, body: messages.append((to, subject, body)))
    return messages


def test_username_reminder_is_private_and_throttled(client, monkeypatch):
    register(client)
    messages = capture_email(monkeypatch)
    route = '/api/v1/auth/recovery/username'
    unknown = client.post(route, json={'email': 'missing@example.com'})
    known = client.post(route, json={'email': 'recover@example.com'})
    repeated = client.post(route, json={'email': 'recover@example.com'})
    assert unknown.status_code == known.status_code == repeated.status_code == 202
    assert unknown.json() == known.json() == repeated.json()
    assert len(messages) == 1
    assert messages[0][0] == 'recover@example.com'
    assert 'recovery_user' in messages[0][2]


def test_reset_code_changes_password_and_invalidates_old_token(client, monkeypatch):
    register(client)
    messages = capture_email(monkeypatch)
    old_login = client.post('/api/v1/auth/login', data={
        'username': 'recover@example.com', 'password': 'oldpassword',
    })
    old_token = old_login.json()['access_token']
    route = '/api/v1/auth/recovery/password'
    unknown = client.post(route, json={'email': 'missing@example.com'})
    known = client.post(route, json={'email': 'recover@example.com'})
    repeated = client.post(route, json={'email': 'recover@example.com'})
    assert unknown.status_code == known.status_code == repeated.status_code == 202
    assert unknown.json() == known.json() == repeated.json()
    assert len(messages) == 1
    code = re.search(r'\b\d{8}\b', messages[0][2]).group()
    confirm = '/api/v1/auth/recovery/password/confirm'
    payload = {'email': 'recover@example.com', 'code': code, 'new_password': 'newpassword'}
    assert client.post(confirm, json={**payload, 'code': '00000000' if code != '00000000' else '11111111'}).status_code == 400
    assert client.post(confirm, json=payload).status_code == 200
    assert client.post(confirm, json=payload).status_code == 400
    assert client.post('/api/v1/auth/test-token', headers={'Authorization': f'Bearer {old_token}'}).status_code == 401
    assert client.post('/api/v1/auth/login', data={
        'username': 'recover@example.com', 'password': 'oldpassword',
    }).status_code == 400
    assert client.post('/api/v1/auth/login', data={
        'username': 'recover@example.com', 'password': 'newpassword',
    }).status_code == 200


def test_reset_code_expires_and_limits_attempts(client, monkeypatch, db):
    user_id = register(client)
    messages = capture_email(monkeypatch)
    route = '/api/v1/auth/recovery/password'
    confirm = '/api/v1/auth/recovery/password/confirm'
    client.post(route, json={'email': 'recover@example.com'})
    code = re.search(r'\b\d{8}\b', messages[0][2]).group()
    challenge = db.get(RecoveryChallenge, user_id)
    challenge.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.flush()
    assert client.post(confirm, json={
        'email': 'recover@example.com', 'code': code, 'new_password': 'newpassword',
    }).status_code == 400
    challenge.expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.flush()
    wrong = '00000000' if code != '00000000' else '11111111'
    for _ in range(5):
        assert client.post(confirm, json={
            'email': 'recover@example.com', 'code': wrong, 'new_password': 'newpassword',
        }).status_code == 400
    assert client.post(confirm, json={
        'email': 'recover@example.com', 'code': code, 'new_password': 'newpassword',
    }).status_code == 400


def test_recovery_requires_mail_configuration(client, monkeypatch):
    monkeypatch.setattr(settings, 'SMTP_HOST', '')
    monkeypatch.setattr(settings, 'SMTP_FROM', '')
    response = client.post('/api/v1/auth/recovery/password', json={'email': 'missing@example.com'})
    assert response.status_code == 503
