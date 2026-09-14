import sqlite3
import pytest
from accounts import Accounts
from library_admin import add_document


@pytest.fixture
def store(tmp_path):
    return Accounts(tmp_path / 'accounts.sqlite3')


def test_password_is_hashed_and_sessions_revoke(store):
    store.bootstrap('admin', 'admin-password-123', 'Admin')
    store.register('patient', 'patient-password', 'Patient', 'patient')
    token = store.login('patient', 'patient-password')
    admin = store.login('admin', 'admin-password-123')
    user = store.current(token)
    with store.connect() as db:
        row = db.execute("SELECT digest FROM users WHERE username='patient'").fetchone()
    assert row['digest'] != 'patient-password'
    store.update_user(admin, user['id'], 'professional', True)
    assert store.current(token) is None
    token = store.login('patient', 'patient-password')
    assert store.current(token)['role'] == 'professional'
    store.logout(token)
    assert store.current(token) is None


def test_admin_operations_reject_user(store):
    store.register('patient', 'patient-password', 'Patient', 'patient')
    token = store.login('patient', 'patient-password')
    with pytest.raises(PermissionError):
        store.users(token)
    with pytest.raises(PermissionError):
        store.create_user(token, 'evil', 'long-password', 'Evil', 'admin')
    with pytest.raises(PermissionError):
        add_document(store, token, 'DRUG', 'generic', 'publisher', 'https://example.com', b'', True)
    with pytest.raises(PermissionError):
        store.register('evil', 'long-password', 'Evil', 'admin')


def test_bootstrap_once_and_no_self_disable(store):
    store.bootstrap('admin', 'admin-password-123', 'Admin')
    with pytest.raises(ValueError):
        store.bootstrap('admin2', 'admin-password-123', 'Admin')
    token = store.login('admin', 'admin-password-123')
    with pytest.raises(ValueError):
        store.update_user(token, store.current(token)['id'], 'patient', False)


def test_lockout_and_disabled_login(store):
    store.register('patient', 'patient-password', 'Patient', 'patient')
    for _ in range(5):
        with pytest.raises(ValueError, match='Invalid'):
            store.login('patient', 'wrong')
    with pytest.raises(ValueError, match='Too many'):
        store.login('patient', 'patient-password')
    with store.connect() as db:
        db.execute('DELETE FROM attempts')
        db.execute('UPDATE users SET active=0')
    with pytest.raises(ValueError):
        store.login('patient', 'patient-password')
