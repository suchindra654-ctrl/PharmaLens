"""Video-inspired library, comparison and audit interfaces."""
import streamlit as st
from catalog import load_catalog, document_details
from config import ROOT, DISCLAIMER
from pdf_evidence import PdfEvidence
from reference_features import SECTIONS, section_snippets, audit_event


@st.dialog('Original PDF evidence', width='large')
def inspect_page(drug, page, excerpt):
    document = PdfEvidence(drug)
    st.caption(f'{drug} · Physical PDF page {page}')
    st.text(excerpt)
    st.image(document.page_png(page), caption='Original source page — check context, tables and footnotes.', width='stretch')
    st.caption(DISCLAIMER)


def library_browser(medicines):
    entries = {e['drug']: e for e in load_catalog()}
    st.subheader('Published drug knowledge base')
    st.caption('Browse extracted sections and inspect the original PDF page. Excerpts are not generated clinical summaries.')
    sidebar, main = st.columns([1, 3], gap='large')
    with sidebar, st.container(border=True, key='medicine_card_navigation'):
        query = st.text_input('Find a medicine', placeholder='Brand or generic name')
        choices = [m for m in medicines if query.casefold() in (m+' '+entries.get(m, {}).get('generic','')).casefold()]
        if not choices:
            st.info('No matching medicine.')
            return
        selected = st.radio('Medicines', choices, key='library_selected')
        st.caption(entries.get(selected, {}).get('generic', ''))
    with main, st.container(border=True, key='medicine_card_details'):
        item = entries.get(selected)
        if not item:
            st.warning('No source PDF is registered.')
            return
        document = PdfEvidence(selected)
        details = document_details(item)
        st.subheader(selected)
        st.write(item.get('generic', ''))
        st.caption(f"Publication: {details['publication']} · Document age: {details['document_age']} · {details['date_source']}")
        st.caption(f"{item['publisher']} · Revision {details['revision']} · Year {details['year']} · Age {details['age']}")
        st.caption(item.get('verification', {}).get('status', 'Live publisher match not checked'))
        st.caption('Publisher checked at (UTC): ' + item.get('verification', {}).get('checked_at', 'Never'))
        st.caption('Printed revision age does not establish freshness. Publisher verification checks file identity at a point in time, not clinical accuracy or latest-version status.')
        with st.container(horizontal=True):
            st.download_button('Download full PDF', document.data, file_name=item['file'], mime='application/pdf')
            st.link_button('Publisher source', item['url'])
        snippets = section_snippets(document)
        if not snippets:
            st.info('Section headings could not be identified reliably. Read the original PDF using the page viewer below.')
        for snippet in snippets:
            with st.container(border=True, key=f'medicine_card_section_{selected}_{snippet["number"]}'):
                text, action = st.columns([3, 1])
                with text:
                    st.markdown(f"**{snippet['number']}. {snippet['section'].upper()}**")
                with action:
                    if st.button(f"Inspect snippet · p. {snippet['page']}", key=f"inspect_{selected}_{snippet['number']}"):
                        inspect_page(selected, snippet['page'], snippet['text'])
                st.text(snippet['text'])
                st.caption('Excerpt may end mid-section. Open the source page for complete context.')
        with st.expander('Open any PDF page'):
            page = st.number_input('Physical page number', min_value=1, max_value=len(document.texts), value=1, key=f'library_page_{selected}')
            if st.button('Inspect page', key=f'open_page_{selected}'):
                inspect_page(selected, page, document.texts[page-1][:1000])


def swap_medicines():
    a, b = st.session_state['compare_a'], st.session_state['compare_b']
    st.session_state['compare_a'], st.session_state['compare_b'] = b, a
    st.session_state.pop('comparison_snapshot', None)


def comparison_view(medicines, audience, service, evidence_only, events, render_source):
    with st.container(border=True, key='medicine_card_comparison_intro'):
        st.subheader('Clinical drug comparison')
        st.write('Compare published indications, administration, warnings and interactions side by side.')
    if len(medicines) < 2:
        st.info('Add at least two medicines to compare their sources.')
        return
    for key, value in [('compare_a', medicines[0]), ('compare_b', medicines[1])]:
        if st.session_state.get(key) not in medicines:
            st.session_state[key] = value
    a, swap, b = st.columns([5, 1, 5], vertical_alignment='center')
    with a, st.container(border=True, key='medicine_card_comparison_a'):
        first = st.selectbox('Select drug A', medicines, key='compare_a')
    with swap:
        st.button('⇄', help='Swap medicines', on_click=swap_medicines, width='stretch')
    with b, st.container(border=True, key='medicine_card_comparison_b'):
        second = st.selectbox('Select drug B', medicines, key='compare_b')
    topic = st.selectbox('Compare section', [label for _, label, _ in SECTIONS], key='comparison_section')
    question = f'Summarize the labeled {topic.lower()}, retaining relevant qualifications and important limitations.'
    st.caption('Each column uses its own PDF. Different trials and populations cannot establish which medicine is better or safer.')
    if st.button('Compare source information', type='primary'):
        if first == second:
            st.warning('Choose two different medicines.')
        else:
            results = []
            try:
                with st.spinner('Checking both prescribing PDFs…'):
                    for name in [first, second]:
                        try:
                            answer = service.ask(question, name, audience, evidence_only, history=[])
                        except Exception:
                            audit_event(events, question, name, 'Comparison', error=True)
                            raise
                        audit_event(events, question, name, 'Comparison', answer)
                        results.append((name, answer))
                st.session_state['comparison_snapshot'] = (first, second, topic, evidence_only, results)
            except Exception:
                st.session_state.pop('comparison_snapshot', None)
                st.error('The comparison could not finish. Check the model configuration and connection.')
    snapshot = st.session_state.get('comparison_snapshot')
    if snapshot and snapshot[:4] == (first, second, topic, evidence_only):
        st.markdown(f'### {topic}')
        for column, (name, answer) in zip(st.columns(2), snapshot[4]):
            with column, st.container(border=True, key=f'medicine_card_comparison_answer_{name}'):
                st.subheader(name)
                st.markdown(answer['answer'])
                with st.expander(f"Citations · {len(answer['sources'])}"):
                    for source in answer['sources']:
                        render_source(source, f"comparison_{name}_{source['citation']}")
                st.caption(answer.get('disclaimer', DISCLAIMER))
    else:
        st.info('Choose two medicines and a section, then run the comparison.')


def audit_view(events):
    st.subheader('Safety & session audit')
    st.caption('Actual outcomes from this signed-in session. The last 100 requests are retained in memory and cleared on sign-out.')
    a, b, c, d = st.columns(4)
    a.metric('Recorded requests', len(events))
    b.metric('PDF reviews passed', sum(e['Outcome'] == 'PDF review passed' for e in events))
    c.metric('Safety responses', sum(e['Outcome'] == 'Safety response' for e in events))
    d.metric('Failed requests', sum(e['Outcome'] == 'Request failed' for e in events))
    left, right = st.columns(2)
    with left, st.container(border=True, key='medicine_card_audit_sources'):
        st.markdown('**Source-only answering**')
        st.write('Answers display retrieved PDF passages in a structured template with physical-page citations. No LLM generation or image-based claim verification runs. Inspect the original pages for full context.')
    with right, st.container(border=True, key='medicine_card_audit_boundaries'):
        st.markdown('**Medical information boundaries**')
        st.write('The assistant provides label information, not personal diagnosis or treatment changes. Every output includes a disclaimer. Retrieval relevance does not establish clinical correctness.')
    with st.container(border=True, key='medicine_card_audit_trail'):
        st.markdown('**Recent request audit trail**')
        if events:
            st.dataframe(list(reversed(events)), hide_index=True, width='stretch')
        else:
            st.info('No requests recorded yet. Ask a question or run a drug comparison.')
        st.caption('Counts are activity records, not confidence scores or clinical validation. PDF reviews passed describes the model check outcome only.')
    with st.container(border=True, key='medicine_card_audit_disclaimer'):
        st.markdown('**Medical information disclaimer**')
        st.write(DISCLAIMER)
