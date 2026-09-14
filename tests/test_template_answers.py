from template_answers import format_extracted_answer
from publication import document_information_text


def source(text, page):
    return {'text': text, 'page': page, 'drug': 'FIXTURE', 'source': 'fixture.pdf'}


def test_side_effects_are_synthesized_and_cleaned():
    result = format_extracted_answer('What are the common side effects?', 'FIXTURE', [
        source('The most common adverse reactions include injection-site reactions and headache.', 4),
        source('o skin or eyes look yellow o poor appetite or vomiting o right-sided abdominal pain.', 5),
        source('Tell your doctor if side effects are severe. Call your doctor immediately for trouble breathing.', 6),
    ])
    assert 'Reported effects include:' in result['answer']
    assert 'injection-site reactions' in result['answer']
    assert 'skin or eyes look yellow' in result['answer']
    assert 'yellow poor appetite' not in result['answer']
    assert 'o skin' not in result['answer']
    assert 'Tell your doctor' not in result['answer']
    assert 'Seek medical help promptly' not in result['answer']
    summary = result['answer'].split('### Document summary', 1)[1].split('### Related section:', 1)[0]
    assert len([line for line in summary.splitlines() if line.strip()]) <= 7
    assert 'According to the official prescribing information' in result['answer']
    assert '### Document summary' in result['answer']
    assert '### Related section: Adverse reactions and side effects' in result['answer']
    assert '### Verified citations' in result['answer']
    assert '[1] PDF page 4' in result['answer']
    assert [source['page'] for source in result['sources']] == [4, 5, 6]


def test_other_questions_prioritize_relevant_evidence():
    uses = format_extracted_answer('What is this medicine used for?', 'FIXTURE', [
        source('This medicine is indicated for treatment of rheumatoid arthritis in adults.', 2),
        source('Store the carton at room temperature and keep it dry.', 8),
    ])
    warnings = format_extracted_answer('What are the warnings?', 'FIXTURE', [
        source('Do not use this medicine in patients with a serious infection.', 3),
        source('The medicine is indicated for rheumatoid arthritis.', 2),
    ])
    assert 'rheumatoid arthritis' in uses['answer']
    assert 'Store the carton' not in uses['answer']
    assert 'Do not use' in warnings['answer']
    assert 'indicated for rheumatoid arthritis' not in warnings['answer']


def test_side_effect_bullets_prioritize_adverse_reactions_over_warnings():
    result = format_extracted_answer('What are the common side effects?', 'ELIQUIS', [
        source('Tell your healthcare provider about your medicines. Some medicines may affect the way ELIQUIS works, causing side effects.', 15),
        source('During treatment with ELIQUIS: • you may bruise more easily • it may take longer than usual for any bleeding to stop Call your healthcare provider if you develop signs of bleeding: • unexpected bleeding or bruising • unusual bleeding from the gums • nosebleeds that happen often • menstrual bleeding heavier than normal', 14),
        source('6 ADVERSE REACTIONS • Bleeding [see Warnings and Precautions (5.2)]', 4),
    ])
    assert 'bruise more easily' in result['answer']
    assert 'bleeding to stop' in result['answer']
    assert 'provider who prescribed' not in result['answer']
    assert '[2] PDF page 14' in result['answer']
    assert '[3] PDF page 4' in result['answer']


def test_document_information_uses_requested_labels():
    text = document_information_text({'publication': '2021', 'document_age': 'Approximately 5 years', 'date_source': 'Catalog publication year'})
    assert '**Published:** 2021' in text
    assert '**Document age:** approximately 5 years' in text


def test_warning_summary_removes_split_section_numbers():
    result = format_extracted_answer('What are the warnings?', 'ELIQUIS', [
        source('4 CONTRAINDICATIONS ELIQUIS is contraindicated in patients with the following conditions: Active pathological bleeding [see Warnings and Precautions (5. 1)] 5 WARNINGS AND PRECAUTIONS 5. 1 Increased Risk of Thrombotic Events after Premature Discontinuation.', 3),
    ])
    assert '- Contraindications include Active pathological bleeding.' in result['answer']
    assert '- Increased risk of thrombotic events after premature discontinuation.' in result['answer']
    assert '5. 1' not in result['answer']
    assert '1)] 5 WARNINGS' not in result['answer']


def test_warning_summary_uses_explicit_claims_across_chunks():
    result = format_extracted_answer('What are the warnings?', 'ELIQUIS', [
        source('4 CONTRAINDICATIONS ELIQUIS is contraindicated in patients with the following conditions:', 3),
        source('Active pathological bleeding [see Warnings and Precautions (5.1)].', 3),
        source('5.1 Increased Risk of Thrombotic Events after Premature Discontinuation.', 4),
    ])
    assert 'Contraindications include Active pathological bleeding.' in result['answer']
    assert 'Increased risk of thrombotic events after premature discontinuation.' in result['answer']
    assert '5.1' not in result['answer']


def test_use_summary_excludes_document_headings_and_warnings():
    result = format_extracted_answer('What is this medicine used for?', 'FIXTURE', [
        source('HIGHLIGHTS OF PRESCRIBING INFORMATION These highlights do not include all information. WARNING: SERIOUS INFECTIONS.', 1),
        source('This medicine is indicated for treatment of rheumatoid arthritis in adults.', 2),
        source('Do not use during an active infection.', 3),
    ])
    assert 'rheumatoid arthritis' in result['answer']
    assert 'HIGHLIGHTS' not in result['answer']
    assert 'Do not use' not in result['answer']


def test_boxed_warning_is_kept_without_document_heading():
    result = format_extracted_answer('What are the warnings?', 'OZEMPIC', [
        source('HIGHLIGHTS OF PRESCRIBING INFORMATION WARNING: RISK OF THYROID C-CELL TUMORS.', 1),
    ])
    assert 'Warning: RISK OF THYROID C-CELL TUMORS.' in result['answer']
    assert 'HIGHLIGHTS OF PRESCRIBING INFORMATION' not in result['answer']


def test_storage_summary_excludes_pdf_question_headings():
    result = format_extracted_answer('How should this medicine be stored?', 'ELIQUIS', [
        source('How should I store ELIQUIS? Store ELIQUIS at room temperature between 68°F to 77°F (20°C to 25°C). Keep ELIQUIS out of the reach of children.', 16),
    ])
    assert 'Store ELIQUIS at room temperature' in result['answer']
    assert 'How should I store ELIQUIS?' not in result['answer']


def test_storage_summary_deduplicates_repeated_label_text():
    result = format_extracted_answer('How should this medicine be stored?', 'ELIQUIS', [
        source('Store ELIQUIS at room temperature between 68°F to 77°F (20°C to 25°C). Keep ELIQUIS out of the reach of children.', 16),
        source('Store ELIQUIS at room temperature between 68°F to 77°F (20°C to 25°C). Keep ELIQUIS out of the reach of children.', 22),
    ])
    assert result['answer'].count('Store ELIQUIS at room temperature') == 1
    assert result['answer'].count('Keep ELIQUIS out of the reach') == 1


def test_use_summary_does_not_promote_treatment_warnings():
    result = format_extracted_answer('What is this medicine used for?', 'SYNTHROID', [
        source('Larger doses may produce serious toxicity, particularly when given with sympathomimetic amines used for anorectic effects.', 4),
        source('SYNTHROID is indicated for the treatment of hypothyroidism.', 2),
    ])
    assert 'hypothyroidism' in result['answer']
    assert 'toxicity' not in result['answer']


def test_use_summary_deduplicates_and_rejects_truncated_claims():
    result = format_extracted_answer('What is this medicine used for?', 'RINVOQ', [
        source('RINVOQ is indicated for the treatment of adults with active rheumatoid arthritis.', 1),
        source('RINVOQ® is indicated for the treatment of adults with active rheumatoid arthritis.', 5),
        source('RINVOQ/RINVOQ LQ is indicated for the treatment of adults and pediatric patients 2 years of.', 1),
    ])
    assert result['answer'].count('rheumatoid arthritis') == 1
    assert 'patients 2 years of.' not in result['answer']


def test_use_summary_rejects_trailing_non_fragment():
    result = format_extracted_answer('What is this medicine used for?', 'RINVOQ', [
        source('RINVOQ is indicated for the treatment of adults with active non.', 5),
    ])
    assert 'active non.' not in result['answer']


def test_use_summary_removes_numbered_indication_headings():
    result = format_extracted_answer('What is this medicine used for?', 'ELIQUIS', [
        source('1 Reduction of Risk of Stroke and Systemic Embolism in Nonvalvular Atrial Fibrillation ELIQUIS is indicated to reduce the risk of stroke and systemic embolism.', 3),
    ])
    assert '1 Reduction of Risk' not in result['answer']
    assert 'ELIQUIS is indicated to reduce the risk' in result['answer']


def test_use_summary_supports_indication_bullets_and_embedded_headings():
    ozempic = format_extracted_answer('What is this medicine used for?', 'OZEMPIC', [
        source('INDICATIONS AND USAGE OZEMPIC is indicated: • as an adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus. • to reduce the risk of major adverse cardiovascular events in adults with type 2 diabetes mellitus and established cardiovascular disease.', 1),
    ])
    synthroid = format_extracted_answer('What is this medicine used for?', 'SYNTHROID', [
        source('FULL PRESCRIBING INFORMATION 1 INDICATIONS AND USAGE Hypothyroidism SYNTHROID is indicated in adult and pediatric patients as replacement therapy in primary, secondary, and tertiary hypothyroidism.', 3),
    ])
    assert 'glycemic control' in ozempic['answer']
    assert 'major adverse cardiovascular events' in ozempic['answer']
    assert 'replacement therapy' in synthroid['answer']