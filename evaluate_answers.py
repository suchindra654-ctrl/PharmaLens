"""Answer-level metrics: latency, abstention, faithfulness, optional entailment.

Run:                          python evaluate_answers.py
Optional NLI pass (slower):   python evaluate_answers.py --nli
"""
import argparse
import json
import re
import time
from datetime import datetime, timezone

from config import ROOT
from rag import Assistant


def _claims(answer):
    """Extract bullet claims from the template answer."""
    return [line[2:].strip() for line in answer.splitlines() if line.strip().startswith('- ')]


def _normalize(text):
    return re.sub(r'\s+', ' ', text).strip().casefold()


def _faithful(claim, source_texts):
    """Template answers should be verbatim substrings of the retrieved sources."""
    normalized = _normalize(claim).rstrip('.')
    return any(normalized in _normalize(s) for s in source_texts if s)


def _keyword_coverage(answer, keywords):
    if not keywords:
        return None
    lowered = answer.casefold()
    return sum(1 for k in keywords if k.casefold() in lowered) / len(keywords)


def _is_abstention(response):
    answer = response.get('answer', '')
    if response.get('outcome') == 'Safety response':
        return True
    if "couldn't verify" in answer or 'could not be verified' in answer:
        return True
    return not response.get('sources') and len(answer) < 200


def _nli_entailment(claim, source_texts, model):
    pairs = [(s, claim) for s in source_texts if s]
    if not pairs:
        return 0.0
    scores = model.predict(pairs)
    # cross-encoder/nli-deberta-v3-base label order: contradiction, entailment, neutral
    for row in scores:
        if int(max(range(len(row)), key=lambda i: row[i])) == 1:
            return 1.0
    return 0.0


def run(use_nli=False):
    cases_path = ROOT / 'evaluation' / 'answers.json'
    if not cases_path.is_file():
        raise SystemExit('Create evaluation/answers.json before running this script.')
    cases = json.loads(cases_path.read_text(encoding='utf-8'))

    service = Assistant()
    nli = None
    if use_nli:
        from sentence_transformers import CrossEncoder
        print('Loading NLI model (first run downloads ~180 MB)...', flush=True)
        nli = CrossEncoder('cross-encoder/nli-deberta-v3-base')

    rows = []
    for case in cases:
        start = time.perf_counter()
        try:
            response = service.ask(case['question'], case['drug'], 'Patient / Caregiver', history=[])
        except Exception as exc:
            response = {'answer': '', 'sources': [], 'outcome': f'Error: {type(exc).__name__}'}
        latency = time.perf_counter() - start

        answer = response.get('answer', '')
        source_texts = [s.get('text', '') for s in response.get('sources', [])]
        claims = _claims(answer)
        faithful = [_faithful(c, source_texts) for c in claims]
        coverage = _keyword_coverage(answer, case.get('expected_keywords', []))
        abstained = _is_abstention(response)
        expected_abstain = bool(case.get('expected_abstain', False))

        row = {
            'id': case['id'],
            'drug': case['drug'],
            'latency_s': round(latency, 2),
            'abstained': abstained,
            'expected_abstain': expected_abstain,
            'abstention_correct': abstained == expected_abstain,
            'claim_count': len(claims),
            'faithful_claim_rate': (sum(faithful) / len(faithful)) if faithful else None,
            'keyword_coverage': coverage,
            'outcome': response.get('outcome', 'answered'),
        }
        if use_nli and claims:
            row['entailment_rate'] = sum(_nli_entailment(c, source_texts, nli) for c in claims) / len(claims)
        rows.append(row)
        print(f"{case['id']}: {row['latency_s']}s abstain={abstained} "
              f"faithful={row['faithful_claim_rate']} coverage={coverage}", flush=True)

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'cases': len(rows),
        'mean_latency_s': mean([r['latency_s'] for r in rows]),
        'abstention_accuracy': mean([1.0 if r['abstention_correct'] else 0.0 for r in rows]),
        'mean_faithful_claim_rate': mean([r['faithful_claim_rate'] for r in rows]),
        'mean_keyword_coverage': mean([r['keyword_coverage'] for r in rows]),
        'rows': rows,
    }
    if use_nli:
        summary['mean_entailment_rate'] = mean([r.get('entailment_rate') for r in rows])

    out = ROOT / 'evaluation' / 'answers_report.json'
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))
    print(f'Report written to {out.relative_to(ROOT)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--nli', action='store_true',
                        help='Run a slow local NLI model for entailment scoring.')
    run(use_nli=parser.parse_args().nli)