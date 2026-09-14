"""Local-demo accounts. Do not expose this deployment publicly."""
import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from pathlib import Path
from config import ROOT

ROLES = ('patient', 'professional', 'admin')
LABELS = {'patient': 'Patient / Caregiver', 'professional': 'Healthcare Professional', 'admin': 'Administrator'}


class Accounts:
    def __init__(self, path=None):
        self.path = Path(path or ROOT / '.local' / 'accounts.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                role TEXT NOT NULL, salt TEXT NOT NULL, digest TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS sessions (digest TEXT PRIMARY KEY, user_id INTEGER, expires REAL);
            CREATE TABLE IF NOT EXISTS attempts (username TEXT PRIMARY KEY, failures INTEGER, until_time REAL);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def credentials(username, password):
        username = username.strip().lower()
        if not re.fullmatch(r'[a-z0-9_.-]{3,40}', username):
            raise ValueError('Username must be 3–40 letters, numbers, dots, underscores or hyphens.')
        if not 12 <= len(password) <= 128:
            raise ValueError('Use a password between 12 and 128 characters.')
        return username

    @staticmethod
    def hash_password(password, salt):
        return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600_000).hex()

    def _insert(self, db, username, password, name, role):
        username = self.credentials(username, password)
        if role not in ROLES or not name.strip() or len(name) > 80:
            raise ValueError('Enter a display name (up to 80 characters) and a valid role.')
        salt = secrets.token_hex(16)
        try:
            db.execute('INSERT INTO users(username,name,role,salt,digest) VALUES(?,?,?,?,?)',
                       (username, name.strip(), role, salt, self.hash_password(password, salt)))
        except sqlite3.IntegrityError:
            raise ValueError('That username is unavailable.') from None

    def bootstrap(self, username, password, name):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
                raise ValueError('An administrator already exists. Sign in to manage accounts.')
            self._insert(db, username, password, name, 'admin')

    def register(self, username, password, name, role):
        if role not in ('patient', 'professional'):
            raise PermissionError('Administrator accounts cannot self-register.')
        with self.connect() as db:
            self._insert(db, username, password, name, role)

    def login(self, username, password):
        username = username.strip().lower()[:40]
        if len(password) > 128:
            raise ValueError('Invalid username or password.')
        now = time.time()
        with self.connect() as db:
            attempt = db.execute('SELECT * FROM attempts WHERE username=?', (username,)).fetchone()
            if attempt and attempt['until_time'] > now:
                raise ValueError('Too many attempts. Wait one minute and try again.')
            row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            digest = self.hash_password(password, row['salt'] if row else '00' * 16)
            valid = row and row['active'] and hmac.compare_digest(digest, row['digest'])
            if not valid:
                failures = (attempt['failures'] if attempt and attempt['until_time'] == 0 else 0) + 1
                db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)', (username, failures, now + 60 if failures >= 5 else 0))
            else:
                db.execute('DELETE FROM attempts WHERE username=?', (username,))
                token = secrets.token_urlsafe(32)
                db.execute('DELETE FROM sessions WHERE expires<?', (now,))
                db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), row['id'], now + 8 * 3600))
                return token
        raise ValueError('Invalid username or password.')

    def current(self, token):
        if not token or not isinstance(token, str):
            return None
        with self.connect() as db:
            row = db.execute('''SELECT u.id,u.username,u.name,u.role FROM users u JOIN sessions s
                ON u.id=s.user_id WHERE s.digest=? AND s.expires>? AND u.active=1''',
                (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return dict(row) if row else None

    def require_admin(self, token):
        actor = self.current(token)
        if not actor or actor['role'] != 'admin':
            raise PermissionError('Administrator access required.')
        return actor

    def logout(self, token):
        if token:
            with self.connect() as db:
                db.execute('DELETE FROM sessions WHERE digest=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def users(self, token):
        self.require_admin(token)
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,username,name,role,active FROM users ORDER BY username')]

    def create_user(self, token, username, password, name, role):
        self.require_admin(token)
        with self.connect() as db:
            self._insert(db, username, password, name, role)

    def update_user(self, token, user_id, role, active):
        actor = self.require_admin(token)
        if role not in ROLES or type(active) is not bool:
            raise ValueError('Invalid role or account status.')
        if user_id == actor['id']:
            raise ValueError('You cannot change your own role or disable your own account.')
        with self.connect() as db:
            db.execute('UPDATE users SET role=?,active=? WHERE id=?', (role, int(active), user_id))
            db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))

    def reset_password(self, token, user_id, password):
        self.require_admin(token)
        self.credentials('valid', password)
        salt = secrets.token_hex(16)
        with self.connect() as db:
            db.execute('UPDATE users SET salt=?,digest=? WHERE id=?', (salt, self.hash_password(password, salt), user_id))
            db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
