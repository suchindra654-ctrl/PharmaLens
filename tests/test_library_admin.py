import pymupdf
import pytest
from library_admin import validate_pdf


def test_pdf_validation():
    with pytest.raises(ValueError):
        validate_pdf(b'not a pdf')
    with pymupdf.open() as pdf:
        pdf.new_page()
        with pytest.raises(ValueError, match='extractable text'):
            validate_pdf(pdf.tobytes())
        pdf[0].insert_text((72, 72), 'Example label text')
        assert validate_pdf(pdf.tobytes()) == 1


def test_upload_publishes_catalog_only_after_indexing(monkeypatch, tmp_path):
    import json
    import library_admin as lib
    (tmp_path / 'data').mkdir()
    class Accounts:
        def require_admin(self, token):
            assert token == 'admin-session'
    class DB:
        def get(self, **kwargs):
            return {'ids': []}
        def delete(self, **kwargs):
            pass
    monkeypatch.setattr(lib, 'verify_official_pdf', lambda *args: {'status': 'Verified publisher match'})
    monkeypatch.setattr(lib, 'ROOT', tmp_path)
    monkeypatch.setattr(lib, 'load_catalog', lambda: [])
    monkeypatch.setattr(lib, 'collection', DB)
    monkeypatch.setattr(lib, 'ingest', lambda *args: 2)
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Example label')
        data = pdf.tobytes()
    count = lib.add_document(Accounts(), 'admin-session', 'EXAMPLE', 'generic', 'publisher',
                             'https://example.com/label.pdf', data, True)
    entries = json.loads((tmp_path / 'data/catalog.json').read_text())
    assert count == 2
    assert entries[0]['drug'] == 'EXAMPLE'
    assert (tmp_path / 'data' / entries[0]['file']).read_bytes() == data


def test_failed_upload_is_not_published(monkeypatch, tmp_path):
    import library_admin as lib
    (tmp_path / 'data').mkdir()
    class Accounts:
        def require_admin(self, token):
            pass
    class DB:
        def get(self, **kwargs):
            return {'ids': []}
        def delete(self, **kwargs):
            pass
    def fail(*args):
        raise RuntimeError('Embedding unavailable')
    monkeypatch.setattr(lib, 'verify_official_pdf', lambda *args: {'status': 'Verified publisher match'})
    monkeypatch.setattr(lib, 'ROOT', tmp_path)
    monkeypatch.setattr(lib, 'load_catalog', lambda: [])
    monkeypatch.setattr(lib, 'collection', DB)
    monkeypatch.setattr(lib, 'ingest', fail)
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Example label')
        data = pdf.tobytes()
    with pytest.raises(RuntimeError):
        lib.add_document(Accounts(), 'token', 'EXAMPLE', 'generic', 'publisher', 'https://example.com', data, True)
    assert not list((tmp_path / 'data').iterdir())
