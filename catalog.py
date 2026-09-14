import json
from config import ROOT


def load_catalog():
    return json.loads((ROOT / 'data' / 'catalog.json').read_text(encoding='utf-8'))


def document_details(item):
    import pymupdf
    path = ROOT / 'data' / item['file']
    if not path.is_file():
        return None
    with pymupdf.open(path) as pdf:
        pages = len(pdf)
    from document_provenance import revision_info
    from publication import publication_info
    data = path.read_bytes()
    return {'pages': pages, 'bytes': path.stat().st_size, **revision_info(data), **publication_info(data, item)}
