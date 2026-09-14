from datetime import date
import pymupdf
from publication import publication_info, newer_information_requested


def pdf(text, metadata=None):
    with pymupdf.open() as d:
        d.new_page().insert_text((40,40), text)
        if metadata:
            d.set_metadata(metadata)
        return d.tobytes()


def test_known_year_and_age():
    r = publication_info(pdf('Published: 2021'), today=date(2026,9,13))
    assert r['publication'] == '2021'
    assert r['document_age'] == 'Approximately 5 years'


def test_unknown_ignores_file_creation_metadata():
    assert publication_info(pdf('Undated', {'creationDate':'D:20210101000000'}))['publication'] == 'Unknown'


def test_publication_precedes_revision():
    assert publication_info(pdf('Published: 2021\nRevised: 2024'))['publication'] == '2021'


def test_month_and_full_date():
    assert publication_info(pdf('Revised: 06/2024'), today=date(2026,9,13))['document_age'] == 'Approximately 2 years, 3 months'
    assert publication_info(pdf('Published: 2024-09-20'), today=date(2026,9,13))['document_age'] == 'Approximately 1 years, 11 months'


def test_current_year():
    assert publication_info(pdf('Published: 2026'), today=date(2026,1,1))['document_age'] == 'Approximately 0 years'


def test_old_document_does_not_assert_obsolescence():
    r = publication_info(pdf('Published: 2010'), today=date(2026,9,13))
    assert r['document_age'] == 'Approximately 16 years'
    assert 'No newer-source check' in r['freshness']


def test_explicit_newer_request():
    for q in ['What is the latest guideline?', 'Is this still valid?', 'Are there newer studies?', 'Is this PDF outdated?']:
        assert newer_information_requested(q)
    assert newer_information_requested('Explain storage', True)


def test_normal_question_does_not_enable_search():
    assert not newer_information_requested('What are the contraindications?')


def test_catalog_fallback_and_future():
    assert publication_info(pdf('No date'), {'publication_year':2021})['publication'] == '2021'
    assert 'Future' in publication_info(pdf('Published: 2099'), today=date(2026,1,1))['document_age']
