import numpy as np
from safety import IntentClassifier, UNCERTAIN, EMERGENCY


class Encoder:
    def __init__(self, query):
        self.query = query
    def encode(self, texts, **kwargs):
        if len(texts) == 1:
            return np.array([self.query])
        return np.repeat(np.eye(3), 4, axis=0)


def test_semantic_emergency_routes_without_regex():
    classifier = IntentClassifier(Encoder([.8, .1, .1]))
    assert classifier.response('unseen paraphrase') == EMERGENCY


def test_near_tie_abstains():
    classifier = IntentClassifier(Encoder([.7, .69, .1]))
    assert classifier.response('ambiguous paraphrase') == UNCERTAIN


def test_low_similarity_abstains():
    assert IntentClassifier(Encoder([.1, .2, .3])).response('unrelated') == UNCERTAIN


def test_information_can_proceed():
    assert IntentClassifier(Encoder([.1, .1, .8])).response('label question') is None


def test_classifier_failure_prevents_retrieval():
    from rag import Assistant
    from types import SimpleNamespace
    def fail(question):
        raise RuntimeError('model unavailable')
    service = Assistant.__new__(Assistant)
    service.model = object()
    service.medicines = lambda: ['EXAMPLE']
    service.intent_classifier = SimpleNamespace(response=fail)
    result = service.ask('Describe the label', 'EXAMPLE')
    assert result['answer'] == UNCERTAIN
    assert result['sources'] == []
