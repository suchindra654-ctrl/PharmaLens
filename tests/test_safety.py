from safety import safety_response, is_label_information_request
from rag import validate_answer
from config import NOT_FOUND


def test_emergency_precedes_medication_advice():
    assert 'emergency' in safety_response('I have chest pain. Should I stop taking it?')


def test_information_request_is_allowed():
    assert safety_response('What are the documented side effects?') is None


def test_common_label_questions_bypass_uncertain_intent():
    for question in ['How should this medicine be stored?', 'What is this medicine used for?',
                     'What are the warnings?']:
        assert is_label_information_request(question)


def test_personal_decision():
    assert 'cannot diagnose' in safety_response('Should I stop taking RINVOQ?')


def test_fabricated_citation_is_rejected():
    assert validate_answer({'supported': True, 'claims': [{'text': 'Claim', 'sources': [2]}]}, [{'text': 'Evidence'}])['answer'] == NOT_FOUND


def test_uncited_claim_is_rejected():
    assert validate_answer({'supported': True, 'claims': [{'text': 'Claim', 'sources': []}]}, [])['answer'] == NOT_FOUND


def test_valid_citation_is_mapped():
    result = validate_answer({'supported': True, 'claims': [{'text': 'Claim', 'sources': [1]}]}, [{'text': 'Evidence', 'page': 7}])
    assert result['sources'][0]['page'] == 7
    assert result['answer'] == 'Claim [1]'
