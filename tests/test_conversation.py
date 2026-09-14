from conversation import recent_history, retrieval_question
from rag import Assistant


def test_history_filters_drug_and_role():
    history = [{'drug': 'A', 'audience': 'Patient / Caregiver', 'question': 'What warnings?', 'answer': 'Example'},
               {'drug': 'B', 'audience': 'Patient / Caregiver', 'question': 'Other medicine', 'answer': ''},
               {'drug': 'A', 'audience': 'Healthcare Professional', 'question': 'Other role', 'answer': ''}]
    result = recent_history(history, 'A', 'Patient / Caregiver')
    assert len(result) == 1
    assert 'What warnings?' in retrieval_question('Explain those', result)
    assert retrieval_question('What are the documented storage conditions?', result) == 'What are the documented storage conditions?'


def test_followup_keeps_personal_advice_guard():
    service = Assistant.__new__(Assistant)
    result = service.ask('Why?', 'A', history=[{'drug': 'A', 'audience': 'Patient / Caregiver',
        'question': 'Should I stop taking this?', 'answer': 'Cannot advise.'}])
    assert 'cannot diagnose' in result['answer']
    assert result['sources'] == []
