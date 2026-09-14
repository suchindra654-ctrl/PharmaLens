"""Local smoke check: every document retrieves only its own source and valid pages."""
from catalog import load_catalog, document_details
from config import ROOT
from rag import Assistant
import pymupdf

service = Assistant()
for item in load_catalog():
    result = service.ask('What are the common side effects?', item['drug'], evidence_only=True)
    assert result['sources'], item['drug']
    with pymupdf.open(ROOT / 'data' / item['file']) as pdf:
        for source in result['sources']:
            assert source['drug'] == item['drug']
            assert source['source'] == item['file']
            assert 1 <= source['page'] <= len(pdf)
            assert source['text'] in pdf[source['page'] - 1].get_text()
    print(item['drug'], 'PASS; pages:', [s['page'] for s in result['sources']])
