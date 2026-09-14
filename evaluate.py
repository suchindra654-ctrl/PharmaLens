"""Offline baseline. No Gemini calls; does not measure clinical entailment."""
import hashlib
import json
from datetime import datetime, timezone
from config import ROOT, collection, embedder, EMBEDDING_MODEL
from safety import IntentClassifier, safety_response


def run():
    model, db = embedder(), collection()
    classifier = IntentClassifier(model)
    safety_rows = []
    for case in json.loads((ROOT/'evaluation/safety.json').read_text()):
        rule = safety_response(case['question'])
        predicted = ('emergency' if 'emergency' in rule else 'personal') if rule else classifier.classify(case['question'])[0]
        safety_rows.append(dict(case, predicted=predicted, correct=predicted == case['expected']))
    rows = []
    for case in json.loads((ROOT/'evaluation/retrieval.json').read_text()):
        path = ROOT/'data'/f"{case['drug'].lower()}.pdf"
        if hashlib.sha256(path.read_bytes()).hexdigest() != case['pdf_sha256']:
            raise ValueError(f"Stale evaluation labels: {case['id']}")
        result = db.query(query_embeddings=model.encode([f"{case['drug']}: {case['question']}"], normalize_embeddings=True).tolist(),
                          where={'drug':case['drug']}, n_results=5, include=['metadatas','distances'])
        pages = [m['page'] for m,d in zip(result['metadatas'][0],result['distances'][0]) if d <= .75]
        gold = set(case['gold_pages'])
        hits = set(pages) & gold
        rows.append(dict(id=case['id'], gold_pages=sorted(gold), retrieved_pages=pages,
                         hit_at_5=bool(hits), page_recall=len(hits)/len(gold),
                         page_precision=len(hits)/len(set(pages)) if pages else 0,
                         reciprocal_rank=next((1/(i+1) for i,p in enumerate(pages) if p in gold),0)))
    unsafe = [r for r in safety_rows if r['expected'] in ('emergency','personal')]
    report = dict(timestamp=datetime.now(timezone.utc).isoformat(), embedding_model=EMBEDDING_MODEL,
        scope='Offline silver retrieval benchmark and small developer-authored safety set; not clinical validation.',
        retrieval_count=len(rows), safety_count=len(safety_rows),
        metrics={key:sum(r[key] for r in rows)/len(rows) for key in ['hit_at_5','page_recall','page_precision','reciprocal_rank']},
        safety_accuracy=sum(r['correct'] for r in safety_rows)/len(safety_rows),
        unsafe_allowed=sum(r['predicted']=='information' for r in unsafe),
        emergency_missed=sum(r['expected']=='emergency' and r['predicted']!='emergency' for r in safety_rows),
        citation_entailment='NOT MEASURED: requires live generated answers plus independent claim/page annotations.',
        retrieval=rows, safety=safety_rows)
    (ROOT/'evaluation/report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('retrieval','safety')},indent=2))


if __name__ == '__main__':
    run()
