import streamlit as st
from accounts import LABELS
from ui import brand


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def login_page(accounts):
    with st.container(horizontal=True, horizontal_alignment='center'):
        with st.container(width=440, key='auth_card'):
            brand(center=True)
            sign_in, register = st.tabs(['Sign in', 'Create account'])
            with sign_in:
                st.html('<div class="auth-welcome"><h2>Welcome back</h2><p>Sign in to access your drug information assistant</p></div>')
                with st.form('login', clear_on_submit=True):
                    username = st.text_input('Username', key='login_username', placeholder='Enter your username')
                    password = st.text_input('Password', type='password', key='login_password', placeholder='Enter your password')
                    if st.form_submit_button('Sign in', type='primary', width='stretch'):
                        try:
                            st.session_state['auth_token'] = accounts.login(username, password)
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                with st.popover('Forgot password?'):
                    st.write('Ask your PharmaLens administrator to reset your password in Administration → Users. Password recovery by email is not configured for this local demo.')
                st.caption('Your account opens the patient, professional or administrator portal assigned to you.')
            with register:
                with st.form('register', clear_on_submit=True):
                    name = st.text_input('Display name')
                    username = st.text_input('Choose username')
                    role = st.selectbox('Account type', ['patient', 'professional'], format_func=LABELS.get)
                    password = st.text_input('Choose password (12+ characters)', type='password')
                    confirm = st.text_input('Confirm password', type='password')
                    if st.form_submit_button('Create account', width='stretch'):
                        try:
                            if password != confirm:
                                raise ValueError('Passwords do not match.')
                            accounts.register(username, password, name, role)
                            st.success('Account created. Use the Sign in tab to continue.')
                        except (ValueError, PermissionError) as error:
                            st.error(str(error))
                st.caption('Professional status is self-declared for this local demo, not credential-verified.')
            st.divider()
            st.caption('Educational information only. Not medical advice or a substitute for professional care and the full prescribing information.')
    with st.container(horizontal=True, horizontal_alignment='center'):
        st.caption('Local demo · Private accounts · Published PDF sources')


def require_user(accounts):
    token = st.session_state.get('auth_token')
    user = accounts.current(token)
    if not user:
        if token:
            clear_session()
        login_page(accounts)
        st.stop()
    return user


def sidebar_identity(accounts, user):
    left, right = st.columns([4, 1])
    with left:
        brand()
    with right:
        st.caption(f"{user['name']} · {LABELS[user['role']]}")
        if st.button('Sign out', width='stretch'):
            accounts.logout(st.session_state.get('auth_token'))
            clear_session()
            st.rerun()
