# Evaluation scope and remaining work

`evaluation/safety.json` is a small developer-authored challenge set separate from
the semantic classifier's prototype examples. It covers urgent symptoms, personal
treatment decisions, general label requests, ambiguity and an instruction attack.
This is a smoke benchmark, not a representative or clinically adjudicated test set.
Do not tune thresholds on it and then report it as an independent holdout.

`evaluation/retrieval.json` freezes PDF SHA-256 hashes and physical page positions.
Gold pages are SILVER annotations: pages containing a predefined relevant phrase,
not independently reviewed evidence judgments. They can include incidental mentions
and miss synonymous relevant evidence. Results quantify this limited benchmark only.
Hit@5, unique-page precision/recall and reciprocal rank include the deployed .75
distance cutoff. The evaluation uses the current dense retrieval directly so safety
routing does not confound retrieval quality. It never calls Gemini or sends PDF data.

Citation structural rejection and the mandatory second image review are tested in
tests/test_pdf_evidence.py and tests/test_safety.py. Passing these tests is NOT an
entailment score. Live answer correctness, claim completeness, citation entailment,
visual/table accuracy and false abstention on clinical cases remain unmeasured.
Before any clinical-quality claim, have independent reviewers annotate a larger,
versioned holdout with question, audience/history, expected abstention, claims,
acceptable physical pages and image/table evidence. Score live two-pass answers
against it and record model version, latency, failures and adjudication disagreements.

Safety now adds a local embedding/prototype classifier to existing rules. Similarity
scores are not probabilities. Low similarity or a small winning margin abstains;
classifier errors also abstain. This can overblock valid questions and still miss
unsafe intent. It is not a validated triage system. Emergency rules retain priority.

Hybrid search and reranking are explicitly deferred. Compare them with this frozen
baseline on an independently annotated holdout before changing retrieval defaults.
