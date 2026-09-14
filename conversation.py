"""Bounded, session-only context. Previous answers are never documentary evidence."""
import re


def recent_history(history, drug, audience):
    result = []
    for turn in (history or [])[-6:]:
        if turn.get('drug') != drug or turn.get('audience') != audience:
            continue
        question = str(turn.get('question', ''))[:2000]
        answer = str(turn.get('answer', ''))[:4000]
        result.append({'question': question, 'answer': answer})
    return result


def retrieval_question(question, history):
    followup = re.search(r'\b(it|its|they|them|those|that|these|this|above|same|more|why|explain|also)\b', question, re.I)
    if history and (followup or len(question.split()) <= 4):
        # Put the current request first so long history cannot truncate it out of embeddings.
        return question + '\nRecent questions: ' + ' | '.join(turn['question'][:200] for turn in history[-3:])
    return question
