import json
from types import SimpleNamespace
import pytest
import pymupdf
import pdf_evidence as pe
from config import NOT_FOUND


@pytest.fixture
def doc():
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), 'Fixture text: Keep the carton dry.')
        page.draw_rect(pymupdf.Rect(72, 100, 150, 140), color=(0, 0.5, 0))
        data = pdf.tobytes()
    return SimpleNamespace(texts=['Fixture text: Keep the carton dry.'], data=data,
        item={'drug': 'FIXTURE', 'file': 'fixture.pdf', 'url': 'https://example.com/fixture.pdf'},
        digest='fixture-hash', page_png=lambda page: b'page-image')


def payload(kind='text', page=1, evidence='Keep the carton dry.'):
    return {'supported': True, 'claims': [{'section': 'Summary', 'text': 'Keep the carton dry.',
        'page': page, 'kind': kind, 'evidence': evidence}]}


@pytest.mark.parametrize('data', [payload(page=2), payload(page=True), payload(evidence='Invented source quote here'),
    {'supported': True, 'claims': []}, {'supported': False, 'claims': []}, None, {'supported': True, 'claims': ['bad']}])
def test_invalid_evidence_rejected(doc, data):
    assert pe.checked_claims(data, doc) is None


def test_formatted_answer_preserves_page_and_disclaimer(doc):
    result = pe.format_answer(pe.checked_claims(payload(), doc), doc)
    assert result['answer'].startswith('According to the prescribing PDF for **FIXTURE**:')
    assert '[1]' in result['answer']
    assert result['sources'][0]['page'] == 1
    assert result['sources'][0]['pdf_sha256'] == 'fixture-hash'
    assert 'not medical advice' in result['disclaimer']


def test_details_are_paragraphs_not_bullets(doc):
    claim = payload()['claims'][0]
    claim['section'] = 'Details'
    result = pe.format_answer([claim], doc)
    assert '\n\nKeep the carton dry. [1]' in result['answer']
    assert '\n- ' not in result['answer']


def test_pdf_bracket_spacing_is_typographic_only():
    assert pe.normalize('[\u200asee USP]') == pe.normalize('[see USP]')
    assert pe.normalize('15 mg') != pe.normalize('150 mg')
    assert pe.normalize('Do not use') != pe.normalize('Do use')


def test_instruction_images_are_bounded_to_real_pages():
    document = SimpleNamespace(texts=['Other page', 'INSTRUCTIONS FOR USE\nOral solution', 'Figure A'])
    assert pe.instruction_pages(document, 'Explain the illustrated instructions') == [2, 3]
    assert pe.instruction_pages(document, 'What are the contraindications?') == []


@pytest.mark.parametrize('review', [{'checks': [{'claim': 1, 'supported': False}]}, {'checks': []},
    {'checks': [{'claim': True, 'supported': True}]}, {'checks': [{'claim': 2, 'supported': True}]},
    {'checks': [{'claim': 1, 'supported': 'true'}]}])
def test_visual_claim_cannot_skip_support_review(monkeypatch, doc, review):
    monkeypatch.setattr(pe, 'PdfEvidence', lambda drug: doc)
    calls = []
    def generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(text=json.dumps(payload(kind='visual', evidence='A green outlined rectangle is visible.') if len(calls) == 1 else review))
    result = pe.generate_pdf_answer(SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
                                   'model', 'Describe the figure', 'FIXTURE', 'Patient / Caregiver', [], [], '')
    assert result['answer'] == NOT_FOUND
    assert len(calls) == 2
    assert calls[0]['contents'][0].inline_data.mime_type == 'application/pdf'
    assert calls[1]['contents'][2].inline_data.mime_type == 'image/png'


def test_real_page_render_and_path_guard(monkeypatch, tmp_path):
    (tmp_path / 'data').mkdir()
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Actual fixture text')
        pdf.save(tmp_path / 'data/fixture.pdf')
    monkeypatch.setattr(pe, 'ROOT', tmp_path)
    monkeypatch.setattr(pe, 'load_catalog', lambda: [{'drug': 'FIXTURE', 'file': 'fixture.pdf'}])
    document = pe.PdfEvidence('FIXTURE')
    assert document.page_png(1).startswith(b'\x89PNG')
    with pytest.raises(ValueError):
        document.page_png(2)
    monkeypatch.setattr(pe, 'load_catalog', lambda: [{'drug': 'FIXTURE', 'file': '../outside.pdf'}])
    with pytest.raises(ValueError):
        pe.PdfEvidence('FIXTURE')
