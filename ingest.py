"""Run: python ingest.py data/rinvoq.pdf --drug RINVOQ --url https://..."""
import argparse
import hashlib
import re
from pathlib import Path

from config import collection, embedder


def _is_meaningful(text):
    """Reject pages where PDF extraction produced noise — mostly single digits
    like '0 0 0 0 1 0 0 0 2 ...'. These pollute the vector index because their
    embeddings accidentally match short queries like 'warnings'.

    A real medical page has mostly alphabetic words. A junk page has almost
    none. The 50% cutoff cleanly separates the two without discarding pages
    that contain legitimate numeric tables (dose tables still have plenty of
    alphabetic words like 'mg', 'daily', 'weight')."""
    words = text.split()
    if len(words) < 20:
        return False
    alphanumeric = sum(1 for w in words if any(c.isalpha() for c in w))
    return alphanumeric / len(words) > 0.5


def extract_chunks(path, drug, url=''):
    import pymupdf
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # Short chunks fit the embedding model's 256 wordpiece-token window better.
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)
    chunks = []
    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, 1):
            text = page.get_text('text').strip()
            if not text or not _is_meaningful(text):
                continue
            # Avoid inventing section labels when PDF layout makes them ambiguous.
            headings = re.findall(r'^\s*\d+(?:\.\d+)?\s+[A-Z][A-Z /,()-]{6,}\s*$', text, re.M)
            section = headings[0].strip() if len(headings) == 1 else 'See source page'
            for part in splitter.split_text(text):
                chunks.append((part, {'drug': drug.upper().strip(), 'page': page_number,
                                     'source': Path(path).name, 'section': section, 'url': url}))
    if not chunks:
        raise ValueError('No extractable text found. Use a text PDF; scanned PDFs require OCR.')
    return chunks


def ingest(path, drug, url='', model=None):
    if not drug.strip():
        raise ValueError('Drug name is required.')
    chunks = extract_chunks(path, drug, url)
    model = model or embedder()
    vectors = model.encode([c[0] for c in chunks], normalize_embeddings=True).tolist()
    db = collection()
    fingerprint = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    ids = [hashlib.sha256(f'{drug.upper()}:{fingerprint}:{i}'.encode()).hexdigest() for i in range(len(chunks))]
    # Write before pruning so an embedding/download failure preserves the old index.
    for start in range(0, len(chunks), 100):
        end = start + 100
        db.upsert(ids=ids[start:end], embeddings=vectors[start:end],
                  documents=[c[0] for c in chunks[start:end]], metadatas=[c[1] for c in chunks[start:end]])
    old = db.get(where={'drug': drug.upper().strip()})['ids']
    stale = list(set(old) - set(ids))
    if stale:
        db.delete(ids=stale)
    return len(chunks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Index one official prescribing PDF per medicine.')
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--drug', required=True)
    parser.add_argument('--url', default='')
    args = parser.parse_args()
    print(f'Indexed {ingest(args.pdf, args.drug, args.url)} passages.')