from reference_features import section_snippets, audit_event
from types import SimpleNamespace


def test_section_excerpts_keep_physical_page():
    doc = SimpleNamespace(texts=['Cover', 'Contents', '1 INDICATIONS AND USAGE\nActual source paragraph.\n2 DOSAGE AND ADMINISTRATION\nOther source details.'])
    snippets = section_snippets(doc)
    assert snippets[0]['page'] == 3
    assert 'Actual source paragraph.' in snippets[0]['text']
    assert section_snippets(SimpleNamespace(texts=['Unnumbered unrelated text'])) == []


def test_audit_records_real_outcomes_and_bounds_history():
    events=[]
    audit_event(events,'Question','RINVOQ','Chat',{'outcome':'Safety response','sources':[]})
    assert events[0]['Outcome']=='Safety response'
    audit_event(events,'Question','RINVOQ','Comparison',error=True)
    assert events[-1]['Outcome']=='Request failed'
    for _ in range(105):
        audit_event(events,'Question','HUMIRA','Chat',{'sources':[{}], 'review':'passed'})
    assert len(events)==100
    assert events[-1]['Outcome']=='PDF review passed'
    assert events[-1]['References']==1
