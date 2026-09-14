"""Conservative publication metadata. No filesystem dates or network access."""
import re
from datetime import date, datetime
import pymupdf


def parse_date(value):
    value = str(value).strip()
    for pattern, precision in [('%Y-%m-%d', 'day'), ('%B %d, %Y', 'day'),
                               ('%d %B %Y', 'day'), ('%Y-%m', 'month'),
                               ('%m/%Y', 'month'), ('%B %Y', 'month'),
                               ('%b %Y', 'month'), ('%Y', 'year')]:
        try:
            parsed = datetime.strptime(value, pattern).date()
            return parsed, precision
        except ValueError:
            pass
    return None


def publication_info(data, catalog=None, today=None):
    today = today or date.today()
    catalog = catalog or {}
    with pymupdf.open(stream=data, filetype='pdf') as pdf:
        # Avoid mistaking dates in references/embedded medication guides for
        # the publication date of the main document.
        cover = '\n'.join(p.get_text() for p in list(pdf)[:2])
        metadata = pdf.metadata or {}
    result, origin = None, 'Unknown'
    date_pattern = r'((?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?|\d{1,2}/(?:19|20)\d{2}|[A-Za-z]+\s+(?:\d{1,2},\s*)?(?:19|20)\d{2})'
    for label, origin_label in [
        (r'publication\s+(?:date|year)|published(?:\s+online)?|date\s+of\s+publication', 'Publication stated in PDF'),
        (r'revised|updated|issued|revision\s+date', 'Revision/update stated in PDF')]:
        candidates = [parse_date(m.group(1)) for m in re.finditer(r'\b(?:'+label+r')\s*:?\s*'+date_pattern, cover, re.I)]
        candidates = [c for c in candidates if c]
        if candidates:
            # Conflicting same-priority dates are not resolved by guessing.
            if len(set(candidates)) != 1:
                return {'publication': 'Unknown', 'document_age': 'Unknown', 'date_source': 'Conflicting dates; review required', 'freshness': 'Publication date could not be established. No newer-source check was performed.'}
            result, origin = candidates[0], origin_label
            break
    if result is None:
        # Only explicitly tagged publication metadata; CreationDate/ModDate
        # usually describe file production and are deliberately ignored.
        match = re.search(r'\bPublicationDate\s*[:=]\s*'+date_pattern, metadata.get('subject') or '', re.I)
        if match:
            result = parse_date(match.group(1))
            origin = 'Explicit publication metadata'
    if result is None:
        for key in ('publication_date', 'publication_year', 'revision'):
            result = parse_date(catalog.get(key, ''))
            if result:
                origin = 'Catalog ' + key.replace('_', ' ')
                break
    if result is None:
        return {'publication': 'Unknown', 'document_age': 'Unknown', 'date_source': 'Unknown',
                'freshness': 'Publication year is unknown. No newer-source check was performed.'}
    parsed, precision = result
    value = parsed.strftime({'year':'%Y', 'month':'%Y-%m', 'day':'%Y-%m-%d'}[precision])
    future = parsed.year > today.year if precision == 'year' else parsed > today
    if future:
        age = 'Future-dated; review required'
    elif precision == 'year':
        age = f'Approximately {today.year-parsed.year} years'
    else:
        months = (today.year-parsed.year)*12 + today.month-parsed.month
        if precision == 'day' and today.day < parsed.day:
            months -= 1
        age = f'Approximately {months//12} years, {months%12} months'
    return {'publication': value, 'document_age': age, 'date_source': origin,
            'freshness': 'Document age alone does not establish whether its contents are current. If you need current recommendations, consider checking newer publications or guidelines. No newer-source check was performed.'}


def newer_information_requested(question, check_current_information=False):
    return check_current_information is True or bool(re.search(
        r'latest|newer|recent research|current (?:recommendations|information|guidelines)|still valid|outdated|what has changed', question, re.I))


def document_information_text(info):
    age = info['document_age']
    if age.startswith('Approximately '):
        age = 'approximately ' + age[len('Approximately '):]
    return ('### Document information\n\n**Published:** '+info['publication']+
            '\n\n**Document age:** '+age+
            ('\n\n*Date shown is a revision/update date, not a confirmed original publication date.*'
             if 'Revision' in info['date_source'] else ''))
