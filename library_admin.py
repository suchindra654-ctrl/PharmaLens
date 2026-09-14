"""Server-side authorization for library changes; one document per medicine."""
import hashlib
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
import pymupdf
from config import ROOT, collection
from catalog import load_catalog
from ingest import ingest
from document_provenance import verify_official_pdf, revision_info

LIBRARY_LOCK = threading.Lock()


def validate_pdf(data):
    if not data or len(data) > 20 * 1024 * 1024 or not data.startswith(b'%PDF-'):
        raise ValueError('Upload a PDF of at most 20 MB.')
    try:
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            if pdf.is_encrypted or not 1 <= len(pdf) <= 300:
                raise ValueError('Use an unencrypted PDF with 1–300 pages.')
            if not any(page.get_text().strip() for page in pdf):
                raise ValueError('This PDF has no extractable text. Scanned documents require OCR.')
            return len(pdf)
    except pymupdf.FileDataError:
        raise ValueError('The uploaded PDF could not be read.') from None


def write_json(path, value):
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def add_document(accounts, token, drug, generic, publisher, url, data, reviewed):
    accounts.require_admin(token)
    drug = drug.strip().upper()
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9 -]{1,59}', drug):
        raise ValueError('Medicine name must be 2–60 letters, numbers, spaces or hyphens.')
    if not generic.strip() or not publisher.strip() or max(len(generic), len(publisher)) > 150:
        raise ValueError('Enter the generic name and publisher (up to 150 characters each).')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Provide an HTTPS publisher source URL without credentials.')
    if reviewed is not True:
        raise ValueError('Review the document identity and publisher before indexing.')
    pages = validate_pdf(data)
    verification = verify_official_pdf(data, url)
    dates = revision_info(data)
    with LIBRARY_LOCK:
        accounts.require_admin(token)
        catalog = load_catalog()
        if drug in {c['drug'] for c in catalog} or collection().get(where={'drug': drug})['ids']:
            raise ValueError('This medicine already exists. Use Reindex for existing documents.')
        filename = f'upload-{uuid.uuid4().hex}.pdf'
        path = ROOT / 'data' / filename
        path.write_bytes(data)
        entry = {'drug': drug, 'generic': generic.strip(), 'publisher': publisher.strip(), 'file': filename, 'url': url,
                 'verification': verification, 'revision_info': dates}
        try:
            count = ingest(path, drug, url)
            entry.update(pages=pages, passages=count, sha256=hashlib.sha256(data).hexdigest(),
                         indexed_at=datetime.now(timezone.utc).isoformat())
            write_json(ROOT / 'data' / 'catalog.json', catalog + [entry])
        except Exception:
            collection().delete(where={'drug': drug})
            path.unlink(missing_ok=True)
            raise
        return count


def reindex_document(accounts, token, drug):
    accounts.require_admin(token)
    with LIBRARY_LOCK:
        entry = next((c for c in load_catalog() if c['drug'] == drug), None)
        if not entry:
            raise ValueError('Select a medicine from the library.')
        return ingest(ROOT / 'data' / entry['file'], drug, entry['url'])


def verify_existing_document(accounts, token, drug):
    accounts.require_admin(token)
    with LIBRARY_LOCK:
        entries = load_catalog()
        entry = next((e for e in entries if e['drug'] == drug), None)
        if not entry:
            raise ValueError('Select a document from the library.')
        data = (ROOT / 'data' / entry['file']).read_bytes()
        verification = verify_official_pdf(data, entry['url'])
        accounts.require_admin(token)
        entry['verification'] = verification
        write_json(ROOT / 'data' / 'catalog.json', entries)
        return verification
