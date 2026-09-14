import pymupdf
from ingest import extract_chunks


def test_chunks_keep_physical_page_and_drug(tmp_path):
    path = tmp_path / 'test.pdf'
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'First page evidence.')
        pdf.new_page().insert_text((72, 72), 'Second page evidence.')
        pdf.save(path)
    chunks = extract_chunks(path, 'example')
    assert [meta['page'] for _, meta in chunks] == [1, 2]
    assert all(meta['drug'] == 'EXAMPLE' for _, meta in chunks)
    assert 'Second page' in chunks[1][0]


def test_blank_pdf_rejected(tmp_path):
    import pytest
    path = tmp_path / 'blank.pdf'
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(path)
    with pytest.raises(ValueError, match='No extractable text'):
        extract_chunks(path, 'example')
