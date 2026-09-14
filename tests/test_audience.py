import json
from types import SimpleNamespace
import pytest
from rag import Assistant
import pdf_evidence


@pytest.mark.parametrize('audience,phrase', [
    ('Patient / Caregiver', 'everyday words'),
    ('Healthcare Professional', 'formal clinical drug-information response'),
])
def test_selected_style_reaches_gemini_with_same_evidence(monkeypatch, audience, phrase):
    from google import genai
    calls = []
    class Client:
        def __init__(self, **kwargs):
            self.models = self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text=json.dumps({'checks': [{'claim': 1, 'supported': True}]} if len(calls) == 2 else {'supported': True, 'claims': [{'text': 'Example', 'page': 4, 'section': 'Summary', 'kind': 'text', 'evidence': 'Source passage'}]}))
    class DB:
        def get(self, **kwargs):
            return {'metadatas': [{'drug': 'EXAMPLE'}]}
        def query(self, **kwargs):
            return {'documents': [['Source passage']], 'metadatas': [[{'drug': 'EXAMPLE', 'page': 4}]], 'distances': [[0.1]]}
    service = Assistant.__new__(Assistant)
    # This test isolates audience generation after the safety gate allows a query.
    service.intent_classifier = SimpleNamespace(response=lambda question: None)
    service.db = DB()
    service.model = SimpleNamespace(encode=lambda *a, **kw: SimpleNamespace(tolist=lambda: [[0.1]]))
    monkeypatch.setattr(genai, 'Client', Client)
    monkeypatch.setattr(pdf_evidence, 'PdfEvidence', lambda drug: SimpleNamespace(data=b'%PDF-fixture', texts=['', '', '', 'Source passage'], digest='testhash', item={'drug': drug, 'file': 'example.pdf', 'url': 'https://example.com'}, page_png=lambda page: b'png-fixture'))
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only')
    result = service.ask('What are the warnings?', 'EXAMPLE', audience)
    instruction = calls[0]['config'].system_instruction
    assert phrase in instruction
    assert 'Do not diagnose, prescribe' in instruction
    assert json.loads(calls[0]['contents'][1])['audience'] == audience
    assert json.loads(calls[0]['contents'][1])['retrieved_passages'][0]['text'] == 'Source passage'
    assert result['sources'][0]['page'] == 4
