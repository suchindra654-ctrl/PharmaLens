import os
import uuid
import streamlit as st
from accounts import LABELS
from config import ROOT, DISCLAIMER
from catalog import load_catalog, document_details
from pdf_evidence import PdfEvidence
from reference_features import audit_event
from reference_views import library_browser, comparison_view, audit_view


def choose_medicine(name):
    st.session_state['medicine'] = name
    st.session_state.pop('pending_question', None)


def render_source(source, key):
    with st.expander(f"[{source['citation']}] {source.get('drug', '')} · PDF page {source['page']}"):
        st.caption(f"{source.get('source', '')} · Physical PDF page")
        st.caption('Evidence description includes visual content.' if source.get('visual') else 'Supporting source excerpt')
        st.text(source['text'])
        url = source.get('url', '')
        if url.startswith('https://'):
            st.link_button('Open publisher PDF', url + f"#page={source['page']}")
        if st.toggle('View original page image', key=f'page_{key}'):
            try:
                doc = PdfEvidence(source['drug'])
                if source.get('pdf_sha256') and source['pdf_sha256'] != doc.digest:
                    st.warning('This PDF has changed since the answer was generated. Ask again to review the current source.')
                else:
                    st.image(doc.page_png(source['page']), caption=f"{source['drug']} · physical PDF page {source['page']}", width='stretch')
            except (ValueError, KeyError):
                st.warning('This source page is unavailable. Use the publisher link.')


def source_card(item):
    with st.container(border=True):
        st.caption('PUBLISHED PRESCRIBING INFORMATION')
        st.subheader(item['drug'])
        st.write(item.get('generic', ''))
        st.caption(item.get('publisher', ''))
        details = document_details(item) if 'file' in item else None
        if details:
            st.write(f"Revision: **{details['revision']}** · Year: **{details['year']}** · Age: **{details['age']}**")
            st.caption(details['date_note'])
            st.caption(item.get('verification', {}).get('status', 'Source URL recorded; live publisher match not checked'))
            st.caption(f"{details['pages']} physical PDF pages · Text, tables & figures")
            st.download_button('Download PDF', (ROOT / 'data' / item['file']).read_bytes(),
                               file_name=item['file'], mime='application/pdf', key=f"pdf_{item['drug']}")
        if item.get('url', '').startswith('https://'):
            st.link_button('Publisher source', item['url'])


def user_portal(user, service):
    events = st.session_state.setdefault('session_audit', [])
    professional = user['role'] == 'professional'
    audience = LABELS[user['role']]
    medicines = service.medicines()
    if not medicines:
        st.warning('No medicines indexed yet. Ask an administrator to add a prescribing document.')
        return
    catalog = {e['drug']: e for e in load_catalog()}
    if st.session_state.get('medicine') not in medicines:
        st.session_state['medicine'] = medicines[0]
    medicine_col, mode_col, info_col = st.columns([2, 1, 2], vertical_alignment='center')
    with medicine_col:
        drug = st.selectbox('Select medicine', medicines, key='medicine')
    with mode_col:
        st.caption('Response format')
        st.write('PDF source answer')
        evidence_only = False
    with info_col:
        st.caption('Original excerpts · No Gemini call' if evidence_only else 'PDF text + page images · Gemini answer + support review')
        st.caption('Clinical explanations' if professional else 'Plain-language explanations')
    st.html(f'<div class="pl-badges"><span>PDF citations</span><span>{len(medicines)} medicines</span><span>Source checks enabled</span><span>{"Clinical reference" if professional else "Patient & caregiver"}</span></div>')
    chat_tab, compare_tab, library_tab, safety_tab = st.tabs(['Q&A Chat', 'Drug Comparison', f'Knowledge Base ({len(medicines)})', 'Safety & Audit'])
    topics = ([('How to use', 'Explain the labeled route, administration instructions and use limitations. Do not recommend an individual dose.'),
              ('Drug composition', 'Describe the active ingredient, strengths, dosage forms and listed inactive ingredients.'),
              ('Label recommendations', 'Summarize recommendations explicitly stated in this PDF for administration, monitoring and precautions. Do not add external guidelines or individual treatment advice.'),
              ('Clinical use', 'Summarize the labeled indications and applicable populations.'),
              ('Contraindications', 'What contraindications and warnings are documented?'),
              ('Interactions', 'Describe the documented drug interactions and mechanisms where provided.'),
              ('Monitoring', 'What monitoring requirements are described in the label?')] if professional else
             [('What it is for', 'What is this medicine used for?'), ('Side effects', 'What are the common side effects?'),
              ('Storage', 'How should this medicine be stored?'), ('Warnings', 'What warnings are listed in the PDF?')])
    with chat_tab:
        key = f"conversation:{user['id']}:{user['role']}:{drug}:{evidence_only}"
        history = st.session_state.setdefault(key, [])
        heading, new = st.columns([5, 1], vertical_alignment='center')
        with heading:
            st.subheader('Clinical drug information' if professional else 'Understand your medicine')
            st.caption(f"{drug} · {'Healthcare professional workspace' if professional else 'Patient & caregiver workspace'}")
        with new:
            if st.button('New conversation', key='new_conversation', width='stretch'):
                st.session_state[key] = []
                history = []
        with st.container(key='chat_space'):
            if not history:
                with st.container(key='welcome_card', border=True):
                    st.markdown('**PharmaLens · Your drug information assistant**')
                    st.write('Explore published passages about indications, contraindications, interactions and monitoring.' if professional else
                             'Ask about your medicine in your own words. I’ll help explain the published information and show you the source pages.')
                    st.write('I organize relevant text from the selected PDF with page citations. Open the original page to inspect figures and tables. These are source excerpts, not an AI interpretation.')
                    st.caption('Choose a topic below or type a question. You can follow up in the same conversation.')
            for index, turn in enumerate(history):
                with st.chat_message('user'):
                    st.write(turn['question'])
                with st.chat_message('assistant', avatar=':material/medication:'):
                    st.markdown('**PharmaLens · Source excerpts**' if evidence_only else ('**PharmaLens · Clinical response**' if professional else '**PharmaLens · Your answer**'))
                    st.markdown(turn['answer'])
                    if turn['sources']:
                        with st.expander(f"Sources · {len(turn['sources'])} references", expanded=evidence_only):
                            for source in turn['sources']:
                                render_source(source, f"{turn.get('id', str(index))}_{source['citation']}")
                    if turn.get('review'):
                        st.caption(turn['review'])
                    with st.container(border=True, key=f'disclaimer_card_{turn.get("id", index)}'):
                        st.markdown('**Medical information disclaimer**')
                        st.markdown(f'<div class="disclaimer-text">{turn.get("disclaimer", DISCLAIMER)}</div>', unsafe_allow_html=True)
        with st.container(horizontal=True):
            for label, prompt in topics:
                if st.button(label):
                    st.session_state['pending_question'] = (key, prompt)
        question = st.chat_input('Ask about this medicine, a PDF figure, or follow up…', max_chars=2000, key='chat_question')
        st.caption('Educational information only · Not a substitute for professional medical advice · Check the cited PDF pages')
        pending = st.session_state.pop('pending_question', None)
        if pending and pending[0] == key:
            question = pending[1]
        if question:
            try:
                with st.spinner('Retrieving source passages…' if evidence_only else 'Reviewing the PDF and checking the answer against its pages…'):
                    response = service.ask(question, drug, audience, evidence_only, history=history)
                audit_event(events, question, drug, 'Chat', response)
                history.append(dict(response, question=question, drug=drug, audience=audience, id=uuid.uuid4().hex))
                st.session_state[key] = history[-20:]
                st.rerun()
            except ValueError as error:
                audit_event(events, question, drug, 'Chat', error=True)
                st.warning(str(error))
                st.caption(DISCLAIMER)
            except Exception:
                audit_event(events, question, drug, 'Chat', error=True)
                st.error('The document review could not be completed. No unverified answer was displayed. Check the PDF index and local embedding model.')
                st.caption(DISCLAIMER)
    with library_tab:
        library_browser(medicines)
    with safety_tab:
        audit_view(events)
    with compare_tab:
        comparison_view(medicines, audience, service, evidence_only, events, render_source)