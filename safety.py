"""Conservative prototype routing; not a clinical safety classifier."""
import re

# Prototype examples are configuration, never evaluation cases. Cosine scores
# are similarity scores, not calibrated probabilities or clinical confidence.
INTENT_EXAMPLES = {
    'emergency': ['I swallowed an entire bottle of tablets', 'My father is unconscious and will not wake up',
                  'I am bleeding heavily and it will not stop', 'My throat is swelling and I am gasping for air'],
    'personal': ['Tell me which medication to take for my symptoms', 'Choose a treatment for this patient',
                 'Is it safe for me to double the tablets tonight', 'Decide whether I should discontinue treatment'],
    'information': ['Summarize the adverse reactions listed in the prescribing information',
                    'What does the label say about storage and composition',
                    'Explain the labeled indications and contraindications',
                    'Describe the overdose section of the published label'],
}
EMERGENCY = 'If this is happening now, contact local emergency services or seek urgent medical care immediately. This assistant cannot assess an emergency.'
PERSONAL = 'I cannot diagnose you or recommend starting, stopping, or changing medication. Please consult a qualified healthcare professional for advice about your situation.'
UNCERTAIN = 'I could not safely determine the intent of this question. Please rephrase it as a general question about the published drug label. For personal symptoms or treatment decisions, consult a qualified healthcare professional.'

# Two ways a question counts as a label-information request:
#   1. It contains a known label topic keyword (storage, warnings, etc.)
#   2. It explicitly asks what the label/document/PDF says about something.
# The second form is important because questions like
# "What does the label say about bleeding risk?" otherwise get routed as
# emergencies by the semantic classifier, which over-generalizes from the
# bleeding prototype example.
LABEL_INFORMATION = re.compile(
    r'\b(storage|stored|store|used for|indication|indications|warnings?|precautions?'
    r'|contraindications?|side effects?|adverse reactions?)\b'
    r'|(?:label|document|pdf|prescribing information|package insert|insert|leaflet|guideline)'
    r'\s+(?:say|state|mention|describe|list|recommend|according to)',
    re.I)


def is_label_information_request(question):
    return bool(LABEL_INFORMATION.search(question))


class IntentClassifier:
    """Local semantic routing supplements rules; uncertain/error results abstain."""
    def __init__(self, encoder):
        self.encoder = encoder
        self.labels = [label for label, examples in INTENT_EXAMPLES.items() for _ in examples]
        self.vectors = encoder.encode([q for examples in INTENT_EXAMPLES.values() for q in examples], normalize_embeddings=True)

    def classify(self, question):
        scores = self.vectors @ self.encoder.encode([question], normalize_embeddings=True)[0]
        best = sorted(((float(max(scores[i] for i, name in enumerate(self.labels) if name == label)), label)
                       for label in INTENT_EXAMPLES), reverse=True)
        score, label = best[0]
        if score < .35 or score - best[1][0] < .03:
            label = 'uncertain'
        return label, score

    def response(self, question):
        label, _ = self.classify(question)
        return {'emergency': EMERGENCY, 'personal': PERSONAL, 'uncertain': UNCERTAIN}.get(label)


def safety_response(question):
    q = question.lower().replace('’', "'")
    emergency = r"(can't breathe|cannot breathe|difficulty breathing|chest pain|overdos(?:e|ed)|suicid|kill myself)"
    personal = r"(\bi\b|\bmy\b|\bi'm\b|right now|just took|someone|my child)"
    if re.search(emergency, q) and re.search(personal, q):
        return 'If this is happening now, contact local emergency services or seek urgent medical care immediately. This assistant cannot assess an emergency.'
    if re.search(r'(should|can|may|could)\s+i\b|\bmy dose\b|\bdiagnose\b|\bdo i have\b|\bwhat should i take\b', q):
        return 'I cannot diagnose you or recommend starting, stopping, or changing medication. Please consult a qualified healthcare professional for advice about your situation.'
    return None