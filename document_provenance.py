"""Printed label dates and exact-byte publisher verification."""
import hashlib
import re
from datetime import date, datetime, timezone
from urllib.parse import urlsplit, urljoin
import requests
import pymupdf

APPROVED_HOSTS = frozenset({
    'www.rxabbvie.com', 'rxabbvie.com', 'packageinserts.bms.com',
    'www.novo-pi.com', 'novo-pi.com', 'www.accessdata.fda.gov',
    'dailymed.nlm.nih.gov', 'labeling.pfizer.com', 'pi.lilly.com',
})


def revision_info(data, today=None):
    today = today or date.today()
    with pymupdf.open(stream=data, filetype='pdf') as pdf:
        # The prescribing-information cover date takes precedence over dates
        # belonging to patient leaflets or device instructions later in the PDF.
        cover = '\n'.join(pdf[i].get_text() for i in range(min(2, len(pdf))))
    match = re.search(r'\bRevised\s*:?\s*(0?[1-9]|1[0-2])\s*/\s*((?:19|20)\d{2})\b', cover, re.I)
    if not match:
        return {'revision': 'Unknown', 'year': 'Unknown', 'age': 'Unknown',
                'date_note': 'No explicit revision month/year found on the first two PDF pages.'}
    month, year = map(int, match.groups())
    months = (today.year - year) * 12 + today.month - month
    if months < 0:
        return {'revision': f'{year:04d}-{month:02d}', 'year': year, 'age': 'Future-dated — review required',
                'date_note': 'Printed cover revision is later than the current month.'}
    years, remainder = divmod(months, 12)
    return {'revision': f'{year:04d}-{month:02d}', 'year': year,
            'age': f'{years} years, {remainder} months' if years else f'{remainder} months',
            'date_note': 'Approximate age from printed cover revision month; not proof that this is the latest edition.'}


def approved_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in APPROVED_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ValueError('Unverified source: use a direct HTTPS PDF URL from an approved publisher or regulator. Upload blocked.')
    return url


def verify_official_pdf(data, url):
    current = approved_url(url.strip())
    try:
        with requests.Session() as session:
            # Do not inherit machine proxy settings for server-side URL retrieval.
            session.trust_env = False
            for _ in range(4):
                with session.get(current, stream=True, timeout=(10, 25), allow_redirects=False) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        current = approved_url(urljoin(current, response.headers.get('Location', '')))
                        continue
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 20 * 1024 * 1024:
                            raise ValueError('Publisher PDF exceeds 20 MB. Upload blocked.')
                        chunks.append(chunk)
                    published = b''.join(chunks)
                    break
            else:
                raise ValueError('Too many publisher redirects. Upload blocked.')
    except requests.RequestException as exc:
        raise ValueError('Publisher verification could not complete. Check the source URL and internet connection; upload blocked.') from exc
    digest = hashlib.sha256(data).hexdigest()
    if not published.startswith(b'%PDF-') or hashlib.sha256(published).hexdigest() != digest:
        raise ValueError('Uploaded file does not exactly match the PDF at the official source URL. Download that PDF again; upload blocked.')
    return {'status': 'Verified publisher match', 'source_url': current, 'sha256': digest,
            'checked_at': datetime.now(timezone.utc).isoformat()}

