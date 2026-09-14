from datetime import date
import pytest
import pymupdf
import document_provenance as provenance


def make_pdf(text):
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), text)
        return pdf.tobytes()


def test_revision_age_uses_explicit_date():
    result = provenance.revision_info(make_pdf('Revised: 2/2024'), date(2026, 9, 11))
    assert result['year'] == 2024
    assert result['age'] == '2 years, 7 months'
    assert provenance.revision_info(make_pdf('Copyright 2025'))['year'] == 'Unknown'


@pytest.mark.parametrize('url', ['http://www.rxabbvie.com/a.pdf', 'https://www.rxabbvie.com.evil.test/a.pdf', 'https://127.0.0.1/a.pdf', 'https://example.com/a.pdf', 'https://user:pass@www.rxabbvie.com/a.pdf'])
def test_unapproved_sources_rejected(url):
    with pytest.raises(ValueError):
        provenance.approved_url(url)


def test_exact_match_required(monkeypatch):
    data = make_pdf('Revised: 6/2026')
    class Response:
        status_code = 200
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def raise_for_status(self): pass
        def iter_content(self, size): yield data
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, *args, **kwargs): return Response()
    monkeypatch.setattr(provenance.requests, 'Session', Session)
    assert provenance.verify_official_pdf(data, 'https://www.rxabbvie.com/a.pdf')['status'] == 'Verified publisher match'
    with pytest.raises(ValueError, match='exactly match'):
        provenance.verify_official_pdf(data + b'changed', 'https://www.rxabbvie.com/a.pdf')


def test_unapproved_redirect_rejected(monkeypatch):
    class Response:
        status_code = 302
        headers = {'Location': 'https://127.0.0.1/private'}
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, *args, **kwargs): return Response()
    monkeypatch.setattr(provenance.requests, 'Session', Session)
    with pytest.raises(ValueError, match='Unverified'):
        provenance.verify_official_pdf(b'%PDF-test', 'https://www.rxabbvie.com/a.pdf')
