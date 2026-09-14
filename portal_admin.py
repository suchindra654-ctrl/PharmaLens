import os
import streamlit as st
from accounts import ROLES, LABELS
from catalog import load_catalog, document_details
from library_admin import add_document, reindex_document, verify_existing_document
from document_provenance import APPROVED_HOSTS


def admin_portal(accounts, service):
    token = st.session_state['auth_token']
    accounts.require_admin(token)
    st.title('Administration')
    st.caption('Manage local accounts and the published document library.')
    overview, users_tab, upload_tab = st.tabs(['Library status', 'Users', 'Add document'])
    with overview, st.container(border=True, key='medicine_card_admin_library'):
        st.info('Publisher match means identical file bytes at the recorded check time. It does not certify clinical accuracy, regulatory approval, or that no newer label exists. PDF age is time since the printed revision, not time since verification.')
        entries = load_catalog()
        users = accounts.users(token)
        first, second, third = st.columns(3)
        first.metric('Medicines', len(entries))
        second.metric('User accounts', len(users))
        third.metric('Indexed passages', service.db.count())
        st.caption('Answer engine: local PDF retrieval and template formatting. No API key required.')
        rows = []
        for entry in entries:
            details = document_details(entry)
            count = len(service.db.get(where={'drug': entry['drug']})['ids'])
            rows.append({'Medicine': entry['drug'], 'Publisher': entry['publisher'],
                         'Publication': details['publication'] if details else 'Unknown',
                         'Document age': details['document_age'] if details else 'Unknown',
                         'PDF pages': details['pages'] if details else 0, 'Passages': count,
                         'Revision': details['revision'] if details else 'Unknown',
                         'Year': str(details['year']) if details else 'Unknown',
                         'PDF age': details['age'] if details else 'Unknown',
                         'Source verification': entry.get('verification', {}).get('status', 'Not checked against live publisher'),
                         'Publisher checked at (UTC)': entry.get('verification', {}).get('checked_at', 'Never'),
                         'Status': 'Indexed' if details and count else 'Needs indexing'})
        st.dataframe(rows, hide_index=True, width='stretch')
        if entries:
            selected = st.selectbox('Document to reindex', [e['drug'] for e in entries])
            if st.button('Verify selected publisher source'):
                try:
                    with st.spinner('Comparing the stored PDF with the publisher download…'):
                        verification = verify_existing_document(accounts, token, selected)
                    st.success(verification['status'] + '. Refresh status to see the result.')
                except ValueError as error:
                    st.error(str(error))
            if st.button('Reindex selected document'):
                try:
                    with st.spinner('Rebuilding document index…'):
                        count = reindex_document(accounts, token, selected)
                    st.success(f'{selected}: indexed {count} passages. Refresh status to see the updated counts.')
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
                except Exception:
                    st.error('Indexing failed. Check the source PDF, embedding model and terminal.')
            st.button('Refresh status')
    with users_tab, st.container(border=True, key='medicine_card_admin_users'):
        st.dataframe(users, hide_index=True, width='stretch')
        with st.expander('Create a user'):
            with st.container(border=True, key='medicine_card_admin_create'), st.form('admin_create', clear_on_submit=True):
                username = st.text_input('Username', key='new_username')
                name = st.text_input('Display name', key='new_name')
                role = st.selectbox('Role', ROLES, format_func=LABELS.get, key='new_role')
                password = st.text_input('Initial password (12+ characters)', type='password')
                if st.form_submit_button('Create user'):
                    try:
                        accounts.create_user(token, username, password, name, role)
                        st.success('User created. Refresh the user list to view it.')
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))
        editable = [u for u in users if u['id'] != accounts.current(token)['id']]
        if editable:
            selected_id = st.selectbox('Manage account', [u['id'] for u in editable],
                format_func=lambda uid: next(u['username'] for u in editable if u['id'] == uid))
            target = next(u for u in editable if u['id'] == selected_id)
            with st.container(border=True, key='medicine_card_admin_edit'), st.form(f'edit_{selected_id}'):
                role = st.selectbox('Account role', ROLES, index=ROLES.index(target['role']), format_func=LABELS.get)
                active = st.checkbox('Account active', value=bool(target['active']))
                if st.form_submit_button('Save account changes'):
                    try:
                        accounts.update_user(token, selected_id, role, active)
                        st.success('Account updated. Existing sessions have been signed out.')
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))
            with st.container(border=True, key='medicine_card_admin_reset'), st.form(f'reset_{selected_id}', clear_on_submit=True):
                password = st.text_input('New password (12+ characters)', type='password')
                if st.form_submit_button('Reset password'):
                    try:
                        accounts.reset_password(token, selected_id, password)
                        st.success('Password reset. Existing sessions have been signed out.')
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))
        st.button('Refresh user list')
    with upload_tab, st.container(border=True, key='medicine_card_admin_upload'):
        st.subheader('Add a published prescribing document')
        st.caption('One PDF per medicine. Review its identity and provenance before publishing it to the local library.')
        st.info('Uploads are indexed only after an exact file match with the PDF downloaded from an approved publisher or regulator. A logo, filename or administrator checkbox alone does not verify authenticity.')
        with st.expander('Approved source domains and date policy'):
            st.write(', '.join(sorted(APPROVED_HOSTS)))
            st.write('Other domains are unverified and blocked until reviewed by the project maintainer. PDF age uses the printed prescribing-information cover revision. Unknown dates remain unknown; age does not prove currency.')
        with st.form('upload'):
            drug = st.text_input('Medicine brand name')
            generic = st.text_input('Generic name')
            publisher = st.text_input('Publisher')
            url = st.text_input('Official HTTPS source URL')
            uploaded = st.file_uploader('Prescribing PDF (20 MB maximum, 300 pages maximum)', type=['pdf'])
            reviewed = st.checkbox('I reviewed the medicine identity and official publisher source.')
            if st.form_submit_button('Upload and index', type='primary'):
                try:
                    if uploaded is None:
                        raise ValueError('Choose a PDF first.')
                    with st.spinner('Validating PDF and indexing passages…'):
                        count = add_document(accounts, token, drug, generic, publisher, url, uploaded.getvalue(), reviewed)
                    st.success(f'{drug.upper()}: {count} passages indexed. It is now available in user portals.')
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
                except Exception:
                    st.error('The upload could not be indexed. Check the document and embedding model.')
