"""PDF section browsing and session-only audit events."""
import re
from datetime import datetime

SECTIONS = [
    ('1', 'Indications and usage', r'INDICATIONS\s+AND\s+USAGE'),
    ('2', 'Dosage and administration', r'DOSAGE\s+AND\s+ADMINISTRATION'),
    ('3', 'Dosage forms and strengths', r'DOSAGE\s+FORMS\s+AND\s+STRENGTHS'),
    ('4', 'Contraindications', r'CONTRAINDICATIONS'),
    ('5', 'Warnings and precautions', r'WARNINGS\s+AND\s+PRECAUTIONS'),
    ('6', 'Adverse reactions', r'ADVERSE\s+REACTIONS'),
    ('7', 'Drug interactions', r'DRUG\s+INTERACTIONS'),
    ('11', 'Description / composition', r'DESCRIPTION'),
    ('16', 'How supplied / storage', r'HOW\s+SUPPLIED(?:\s*/\s*STORAGE\s+AND\s+HANDLING)?'),
]


def section_snippets(document):
    result = []
    for number, label, pattern in SECTIONS:
        matches = []
        heading = re.compile(r'(?m)^\s*' + number + r'\s+' + pattern + r'\s*(?:\n|$)')
        for page, text in enumerate(document.texts, 1):
            contents = re.search(r'FULL\s+PRESCRIBING\s+INFORMATION\s*:\s*CONTENTS', text, re.I)
            if contents:
                text = text[:contents.start()]
            found = heading.search(text)
            if found:
                body = text[found.end():].strip()
                if re.match(r'^\d+\s+[A-Z]', body):
                    continue
                # Avoid contents pages, whose next line is another numbered heading.
                if re.match(r'^\d+(?:\.\d+)?\s+[A-Z]', body):
                    # A numbered subsection is legitimate; only skip if it looks like a contents list.
                    if len(re.findall(r'\.{3,}', body[:800])) >= 2:
                        continue
                remainder = text[found.end():]
                next_heading = re.search(r'(?m)^\s*\d+\s+[A-Z][A-Z /&-]{5,}\s*$', remainder)
                end = min(found.end()+1000, found.end()+next_heading.start() if next_heading else len(text))
                matches.append({'section': label, 'number': number, 'page': page,
                                'text': text[found.start():end].strip()})
        if matches:
            # Full prescribing sections normally follow highlights and contents.
            selected = next((m for m in matches if m['page'] > 1), matches[0])
            result.append(selected)
    return result


def audit_event(events, question, drug, category, response=None, error=False):
    response = response or {}
    outcome = ('Request failed' if error else response.get('outcome') or
               ('PDF review passed' if response.get('review') else
                'Source excerpts' if response.get('sources') else 'No cited answer'))
    events.append({'Time': datetime.now().strftime('%H:%M:%S'), 'Question': question,
                   'Medicine': drug, 'View': category, 'Outcome': outcome,
                   'References': len(response.get('sources', []))})
    del events[:-100]
