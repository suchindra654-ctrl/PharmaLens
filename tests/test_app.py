from pathlib import Path
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from accounts import Accounts


@pytest.fixture
def portal(monkeypatch, tmp_path):
    import accounts
    import rag
    st.cache_resource.clear()
    store = Accounts(tmp_path / 'users.sqlite3')
    store.register('patient', 'patient-pass-123', 'Patient', 'patient')
    store.register('clinician', 'clinical-pass-123', 'Clinician', 'professional')
    calls = []
    class Service:
        class DB:
            def count(self):
                return 0
            def get(self, **kwargs):
                return {'ids': []}
        db = DB()
        def medicines(self):
            return ['HUMIRA', 'RINVOQ']
        def ask(self, question, drug, audience, evidence_only, history=None):
            calls.append((question, drug, audience, list(history or [])))
            return {'answer': 'Example evidence', 'sources': []}
    monkeypatch.setattr(accounts, 'Accounts', lambda: store)
    monkeypatch.setattr(rag, 'Assistant', Service)
    yield store, calls
    st.cache_resource.clear()


def app():
    return AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py', default_timeout=10)


def test_login_and_signout(portal):
    page = app().run()
    assert not any(r.label == 'Appearance' for r in page.radio)
    assert not page.exception
    assert not page.chat_input
    page.text_input(key='login_username').set_value('patient')
    page.text_input(key='login_password').set_value('patient-pass-123')
    next(b for b in page.button if b.label == 'Sign in').click().run()
    assert not page.exception
    assert any(t.value == 'Understand your medicine' for t in page.subheader)
    next(b for b in page.button if b.label == 'Sign out').click().run()
    assert not page.exception
    assert not page.chat_input
    assert not any(str(key).startswith('conversation:') for key in page.session_state.filtered_state)
    assert not any(r.label == 'Appearance' for r in page.radio)


def test_followups_and_medicine_isolation(portal):
    store, calls = portal
    page = app()
    page.session_state['auth_token'] = store.login('patient', 'patient-pass-123')
    page.run()
    page.chat_input[0].set_value('What are the side effects?').run()
    page.chat_input[0].set_value('Can you explain those?').run()
    assert not page.exception
    assert len(calls[-1][3]) == 1
    page.selectbox(key='medicine').set_value('RINVOQ').run()
    page.chat_input[0].set_value('How is it stored?').run()
    assert calls[-1][1] == 'RINVOQ'
    assert calls[-1][3] == []
    page.button(key='new_conversation').click().run()
    assert not page.chat_message


def test_professional_has_different_portal(portal):
    store, calls = portal
    page = app()
    page.session_state['auth_token'] = store.login('clinician', 'clinical-pass-123')
    page.run()
    assert not page.exception
    assert any(t.value == 'Clinical drug information' for t in page.subheader)
    assert any(b.label == 'Monitoring' for b in page.button)
    assert any(b.label == 'Drug composition' for b in page.button)
    assert any(b.label == 'Label recommendations' for b in page.button)
    assert not any(b.label == 'What it is for' for b in page.button)
    page.chat_input[0].set_value('What monitoring is described?').run()
    assert calls[-1][2] == 'Healthcare Professional'
    assert not page.exception


def test_admin_portal_and_revoked_session(portal):
    store, _ = portal
    store.bootstrap('admin', 'admin-password-123', 'Admin')
    token = store.login('admin', 'admin-password-123')
    page = app()
    page.session_state['auth_token'] = token
    page.run()
    assert not page.exception
    assert any(t.value == 'Administration' for t in page.title)
    assert any(b.label == 'Upload and index' for b in page.button)
    assert not page.chat_input
    store.logout(token)
    page.run()
    assert not page.exception
    assert not any(t.value == 'Administration' for t in page.title)

def test_ai_answers_ignore_previous_excerpt_mode(portal, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    store, calls = portal
    page = app()
    page.session_state['auth_token'] = store.login('patient', 'patient-pass-123')
    page.session_state['response_mode'] = 'Source excerpts'
    page.run()
    assert not any(s.key == 'response_mode' for s in page.selectbox)
    assert any('GEMINI_API_KEY' in w.value for w in page.warning)
    assert not page.exception
    assert not any(r.label == 'Appearance' for r in page.radio)
    assert not page.exception

def test_comparison_uses_each_selected_pdf(portal):
    store, calls = portal
    page = app()
    page.session_state['auth_token'] = store.login('clinician', 'clinical-pass-123')
    page.run()
    page.selectbox(key='compare_a').set_value('HUMIRA').run()
    page.selectbox(key='compare_b').set_value('RINVOQ').run()
    next(b for b in page.button if b.label == 'Compare source information').click().run()
    assert not page.exception
    assert [call[1] for call in calls] == ['HUMIRA', 'RINVOQ']
    assert all(call[3] == [] for call in calls)
