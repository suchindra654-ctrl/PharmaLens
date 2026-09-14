import streamlit as st
from accounts import Accounts
from portal_auth import require_user, sidebar_identity
from portal_admin import admin_portal
from portal_user import user_portal
from rag import Assistant
from config import embedder
from ui import apply_theme

st.set_page_config(page_title='PharmaLens', page_icon='💊', layout='wide')
apply_theme()


@st.cache_resource
def accounts_store():
    return Accounts()


@st.cache_resource
def assistant():
    service = Assistant()
    try:
        # Warm the embedding model once so the first user query does not pay
        # the 8-10 second cold-start cost. encode() also initializes BLAS
        # kernels used by every subsequent query in this session.
        service.model = embedder()
        service.model.encode(['warmup'], normalize_embeddings=True)
    except Exception:
        # Warm-up is best-effort; the app still works if it fails, the first
        # query simply takes longer.
        pass
    return service


accounts = accounts_store()
user = require_user(accounts)
sidebar_identity(accounts, user)
try:
    service = assistant()
except Exception:
    st.error('The document index could not be opened. Check your database configuration.')
    st.stop()
if user['role'] == 'admin':
    admin_portal(accounts, service)
else:
    user_portal(user, service)