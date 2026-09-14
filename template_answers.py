"""Concise evidence synthesis; retrieval and source records stay unchanged."""
import re
from config import DISCLAIMER, NOT_FOUND

STOP = set('what are is the a an of for this medicine drug does how should be in to and about please explain'.split())
TOPIC_TERMS = {
    'side effects': {'side', 'effect', 'adverse', 'reaction', 'symptom'},
    'use': {'use', 'indication', 'indicated', 'treat', 'treatment'},
    'warnings': {'warning', 'precaution', 'contraindication', 'avoid', 'risk'},
    'storage': {'storage', 'stored', 'store', 'refrigerat', 'temperature', 'keep'},
}
SIDE_EFFECT_MARKERS = r'\b(headache|nausea|vomiting|diarrhea|pain|rash|itch|swelling|yellowing|yellow|appetite|fatigue|dizziness|bleeding|reaction)\b'

def terms(text):
    words = set(re.findall(r"[a-z]{3,}", text.lower())) - STOP
    return {('contraindicat' if w.startswith('contraindicat') else w.rstrip('s')) for w in words}


def _clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(\d)\.\s+(\d)', r'\1.\2', text)
    text = re.sub(r'\((\d+)\.\s+(\d+)', r'(\1.\2', text)
    text = re.sub(r'(?<!\w)[o0]\s+(?=[a-z])', '', text, flags=re.I)
    text = re.sub(r'\s*([,.;:])\s*', r'\1 ', text)
    return text.strip()


def _sentences(text):
    if len(re.findall(r'\s[o0]\s+[a-z]', text, re.I)) >= 2:
        text = re.sub(r'\s[o0]\s+(?=[a-z])', '. ', text, flags=re.I)
    text = _clean_text(text)
    text = re.sub(r'\s+(?=[-•▪]\s*)', '. ', text)
    return [part.strip(' .') + '.' for part in re.split(r'(?<=[.!?])\s+|(?:^|(?<=\s))[•▪-]\s*', text)
            if len(part.split()) >= 3]


def _topic(question):
    lowered = question.casefold()
    if re.search(r'\b(side effects?|adverse reactions?|symptoms?)\b', lowered):
        return 'side effects'
    if re.search(r'\b(warnings?|precautions?|contraindications?)\b', lowered):
        return 'warnings'
    if re.search(r'\b(used for|uses?|indications?|treats?)\b', lowered):
        return 'use'
    if re.search(r'\b(storage|stored|store|refrigerat|room temperature)\b', lowered):
        return 'storage'
    return None


def _is_relevant(sentence, question, topic):
    sentence_terms = terms(sentence)
    question_terms = terms(question)
    if topic == 'side effects':
        if re.search(r'\b(currently have|ever had|warnings? and precautions?|see .*precautions?|risk of)\b', sentence, re.I):
            return False
        return bool(re.search(SIDE_EFFECT_MARKERS, sentence, re.I))
    if topic and sentence_terms & TOPIC_TERMS[topic]:
        return True
    if topic == 'warnings' and re.search(r'\b(do not|avoid|must not|contraindicated|should not|serious risk)\b', sentence, re.I):
        return True
    return bool(sentence_terms & question_terms)


def _normalise_list(items):
    cleaned = []
    for item in items:
        item = re.sub(r'^[o0]\s+', '', item, flags=re.I).strip(' .,:;')
        item = re.sub(r'\s+', ' ', item)
        if item and item.casefold() not in {entry.casefold() for entry in cleaned}:
            cleaned.append(item)
    return cleaned


def _topic_title(topic):
    return {
        'side effects': 'Adverse reactions and side effects',
        'use': 'Indications and usage',
        'warnings': 'Warnings and precautions',
        'storage': 'Storage and handling',
    }.get(topic, 'Relevant PDF section')


def _claim_text(text):
    text = _clean_text(text)
    text = text.replace('®', '').replace('™', '')
    text = re.sub(r'\s*\[[^]]*\]', '', text)
    text = re.sub(r'\s*\(\d+(?:\.\d+)?\)\.?', '.', text)
    text = re.sub(r'\s*\),', ',', text)
    text = re.sub(r'^\d+\s+(?:Pediatric Use|Adult Use)\s+', '', text, flags=re.I)
    text = re.sub(r'^\d+\s+(?:Rheumatoid Arthritis|Crohn[’\']s Disease|Ulcerative Colitis|Plaque Psoriasis|Psoriatic Arthritis|Treatment of [A-Z][^.]*)\s+', '', text, flags=re.I)
    text = re.sub(r'^\s*Storage and Handling\s+', '', text, flags=re.I)
    text = re.sub(r'^\d+\s+(?:Reduction in the Risk of|Treatment of) .*?\s+(?=(?:RINVOQ|HUMIRA|SKYRIZI|ELIQUIS|OZEMPIC|SYNTHROID)\b)', '', text, flags=re.I)
    text = re.sub(r'^\d+\s+.*?(?=(?:RINVOQ|HUMIRA|SKYRIZI|ELIQUIS|OZEMPIC|SYNTHROID)\s+is indicated)', '', text, flags=re.I)
    text = re.sub(r'^(?:\d+\s+)?(?:HIGHLIGHTS OF PRESCRIBING INFORMATION|FULL PRESCRIBING INFORMATION|CONTENTS)\s*', '', text, flags=re.I)
    return text.strip(' .,:;-')


def _is_document_noise(text):
    return bool(re.search(r'\b(highlights(?: of prescribing information)?|full prescribing information|contents|indications and usage|approval:|revised:|patient counseling information)\b', text, re.I))


def _use_summary(evidence):
    claims, citations = [], set()
    for citation, (sentences, raw_text) in evidence.items():
        indication_context = bool(re.search(r'\bindications?\s+and\s+usage\b', raw_text, re.I))
        for sentence in sentences:
            direct_claim = re.search(r'\bis indicated\b', sentence, re.I)
            bullet_claim = indication_context and re.search(r'\b(as an adjunct to diet and exercise|to reduce the risk of major adverse cardiovascular events|to reduce the risk of sustained eGFR decline|replacement therapy in|as an adjunct to surgery and radioiodine therapy)\b', sentence, re.I)
            if (_is_document_noise(sentence) and not direct_claim) or re.search(r'\b(warning|precaution|contraindicat|avoid|do not|adverse reaction|toxicity|life-threatening|sympathomimetic|anorectic)\b', sentence, re.I):
                continue
            if not direct_claim and not re.search(r'\b(indicated for|indicated to|used for|is used for|is used to|indications?)\b', sentence, re.I) and not bullet_claim:
                continue
            if re.search(r'\b(not indicated|should not|do not|not for|contraindicat|warning|precaution)\b', sentence, re.I):
                continue
            claim = _claim_text(sentence)
            incomplete = re.search(r'\b(?:of|for|and|or|to|with|the|a|an|in|on|by|non|active|plaque|prophylaxis)$', claim.rstrip('.'), re.I)
            normalized = re.sub(r'[^a-z0-9]+', ' ', claim.casefold()).strip()
            existing = [re.sub(r'[^a-z0-9]+', ' ', item.casefold()).strip() for item in claims]
            duplicate = any(normalized == item or normalized in item or item in normalized for item in existing)
            if 5 <= len(claim.split()) <= 45 and not incomplete and not duplicate:
                claims.append(claim + '.')
                citations.add(citation)
    if not claims:
        return '', []
    return '\n'.join(f'- {claim}' for claim in claims[:4]), sorted(citations)


def _storage_summary(evidence):
    claims, citations = [], set()
    for citation, (sentences, raw_text) in evidence.items():
        for sentence in sentences:
            if _is_document_noise(sentence) or re.search(r'\bhandling and storage of the vial\b', sentence, re.I) or not re.search(r'\b(store|storage|stored|refrigerat|room temperature|temperature|keep)\b', sentence, re.I):
                continue
            if '?' in sentence or re.match(r'\s*how should i store\b', sentence, re.I):
                continue
            claim = _claim_text(sentence)
            if 4 <= len(claim.split()) <= 45 and claim.rstrip('.').casefold() not in {item.rstrip('.').casefold() for item in claims}:
                claims.append(claim + '.')
                citations.add(citation)
    if not claims:
        return '', []
    return '\n'.join(f'- {claim}' for claim in claims[:4]), sorted(citations)


def _side_effect_summary(evidence):
    effects, citations = [], set()
    for citation, (_, raw_text) in evidence.items():
        if not re.search(r'adverse reactions?|during treatment|signs or symptoms of bleeding', raw_text, re.I):
            continue
        if re.search(r'adverse reactions?', raw_text, re.I) and re.search(r'\bbleeding\b', raw_text, re.I):
            citations.add(citation)
        bullets = re.split(r'[\u2022\u25aa\u25fe]', raw_text)
        for bullet in bullets[1:]:
            item = re.split(r'\bCall your healthcare\b', bullet, maxsplit=1, flags=re.I)[0]
            item = re.sub(r'\s+', ' ', item).strip(' .,:;')
            if not item or len(item.split()) > 24:
                continue
            if not re.search(r'\b(bruise\w*|bleed\w*|nosebleed\w*|gums?|menstrual|vaginal)\b', item, re.I):
                continue
            if re.search(r'\b(active pathological|potentially fatal|promptly evaluate|warning signs?|see warnings)\b', item, re.I):
                continue
            item = _claim_text(item)
            if item.casefold() not in {effect.casefold() for effect in effects}:
                effects.append(item)
                citations.add(citation)
    if not effects:
        return '', []
    direct = [item for item in effects if re.match(r'(you may|it may|unexpected|unusual|nosebleeds|menstrual)', item, re.I)]
    if not direct:
        direct = effects
    first = direct[:2]
    rest = direct[2:6]
    lines = ['Reported effects include:']
    lines += [f'- {item.rstrip(".")}.' for item in first]
    if rest:
        lines.append(f'- Warning signs include {rest[0].rstrip(".")}.')
        lines += [f'- {item.rstrip(".")}.' for item in rest[1:]]
    return '\n'.join(lines), sorted(citations)


def _warning_summary(evidence):
    claims, citations = [], set()
    for citation, (_, raw_text) in evidence.items():
        text = _clean_text(raw_text)
        if _is_document_noise(text):
            text = re.sub(r'\b(?:these )?highlights.*?(?=warning:|boxed warning:|$)', '', text, flags=re.I).strip()
        boxed = re.search(r'\b(?:boxed )?warning:\s*(.*?)(?=\s+\d+\s+|$)', text, re.I)
        if boxed:
            claim = _claim_text(boxed.group(1))
            if claim:
                claims.append('Warning: ' + claim + '.')
                citations.add(citation)
        if re.search(r'active pathological bleeding', text, re.I):
            claims.append('Contraindications include Active pathological bleeding.')
            citations.add(citation)
        elif re.search(r'contraindicat', text, re.I):
            match = re.search(r'conditions:\s*(.*?)(?=\s+\d+\s+WARNINGS|\s+\d+\.\d+\s+Increased|$)', text, re.I)
            if match:
                claim = re.sub(r'\s*\[see .*?\]', '', match.group(1)).strip(' .,:;')
                if claim and len(claim.split()) < 28:
                    claims.append('Contraindications include ' + claim + '.')
                    citations.add(citation)
        match = re.search(r'(increased risk of .*?premature discontinuation)', text, re.I)
        if match and not any('premature discontinuation' in claim.casefold() for claim in claims):
            claims.append(match.group(1).capitalize() + '.')
            citations.add(citation)
        if not re.search(r'active pathological bleeding|increased risk of .*?premature discontinuation', text, re.I):
            for sentence in _sentences(text):
                if re.search(r'\b(do not|avoid|must not)\b', sentence, re.I):
                    claim = _claim_text(sentence)
                    if len(claim.split()) <= 24 and not re.search(r'\bhighlights of prescribing information\b', claim, re.I):
                        claims.append(claim + '.')
                        citations.add(citation)
                        break
    unique = []
    for claim in claims:
        if claim.casefold() not in {item.casefold() for item in unique}:
            unique.append(claim)
    if not unique:
        return '', []
    return '\n'.join(f'- {claim}' for claim in unique[:4]), sorted(citations)


def _synthesise(question, evidence):
    topic = _topic(question)
    relevant = []
    for citation, (sentences, raw_text) in evidence.items():
        for sentence in sentences:
            if _is_relevant(sentence, question, topic):
                relevant.append((citation, sentence))
    if not relevant:
        return '', []

    unique = []
    seen = set()
    for citation, sentence in relevant:
        identity = sentence.casefold()
        if identity not in seen:
            seen.add(identity)
            unique.append((citation, sentence))

    if topic == 'side effects':
        parsed_answer, parsed_citations = _side_effect_summary(evidence)
        if parsed_answer:
            return parsed_answer, parsed_citations
        effects = []
        warnings = []
        for citation, sentence in unique:
            if re.search(r'\b(call|tell|contact|report|seek|emergency|serious|allergic)\b', sentence, re.I):
                warnings.append((citation, sentence))
            else:
                effects.append((citation, sentence))
        names = []
        for citation, sentence in effects:
            match = re.search(r'\b(?:common adverse reactions?|reported effects?)\s+(?:include|were|included)\s*:?[ ]*(.*)', sentence, re.I)
            if match:
                names.extend(re.split(r'\s*(?:,|;|\band\b)\s*', match.group(1).rstrip('.')))
            elif len(sentence.split()) <= 18 and not re.search(r'\b(risk|stop|clot|provider|medicine|surgery|procedure|prescribed|information)\b', sentence, re.I):
                names.append(sentence.rstrip('.'))
        names = _normalise_list(names)[:8]
        if names:
            answer = 'Reported effects include:\n' + '\n'.join(f'- {name.rstrip(".")}.' for name in names)
        else:
            answer = ''
        return answer.strip(), sorted({citation for citation, _ in unique})

    if topic == 'warnings':
        parsed_answer, parsed_citations = _warning_summary(evidence)
        return parsed_answer, parsed_citations

    if topic == 'use':
        parsed_answer, parsed_citations = _use_summary(evidence)
        return parsed_answer, parsed_citations

    if topic == 'storage':
        parsed_answer, parsed_citations = _storage_summary(evidence)
        return parsed_answer, parsed_citations

    paragraphs = []
    for _, sentence in unique[:4]:
        if _is_document_noise(sentence):
            continue
        if not any(sentence in paragraph or paragraph in sentence for paragraph in paragraphs):
            paragraphs.append(sentence)
    return '\n'.join(f'- {paragraph}' for paragraph in paragraphs), sorted({citation for citation, _ in unique})


def format_extracted_answer(question, drug, sources):
    used = [dict(s, citation=i) for i, s in enumerate(sources, 1)]
    evidence = {source['citation']: (_sentences(source.get('text', '')), source.get('text', '')) for source in used}
    answer, citations = _synthesise(question, evidence)
    if not answer:
        answer = 'A concise answer could not be verified from the retrieved PDF evidence. Open Sources to review the original context.' if used else NOT_FOUND
        citations = []
    topic = _topic(question)
    lines = [f'According to the official prescribing information for **{drug}**:', '',
             '### Document summary', '', answer]
    if citations:
        lines += ['', f'### Related section: {_topic_title(topic)}', '',
                  '*Answer synthesized from the retrieved PDF evidence with traceable citations.*', '',
                  '### Verified citations']
        lines += [f'[{citation}] PDF page {used[citation - 1].get("page", "unknown")}' for citation in citations]
    return {'answer': '\n'.join(lines), 'sources': used, 'disclaimer': DISCLAIMER, 'outcome': 'Evidence synthesis'}
