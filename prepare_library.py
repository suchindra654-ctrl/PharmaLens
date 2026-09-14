"""Index downloaded catalog documents and record reproducible source fingerprints."""
import hashlib
import json
from datetime import datetime, timezone
from catalog import load_catalog, document_details
from config import ROOT, embedder
from ingest import ingest


if __name__ == '__main__':
    model = embedder()
    manifest = []
    for item in load_catalog():
        path = ROOT / 'data' / item['file']
        details = document_details(item)
        if not details:
            raise FileNotFoundError(path)
        count = ingest(path, item['drug'], item['url'], model=model)
        manifest.append(dict(item, **details, passages=count,
                             indexed_at=datetime.now(timezone.utc).isoformat(),
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(f"{item['drug']}: {details['pages']} pages, {count} passages", flush=True)
    (ROOT / 'data' / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
