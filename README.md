# 💊 PharmaLens

**Evidence-grounded drug information assistant built on FDA prescribing documents.**

PharmaLens answers questions about medicines by retrieving the relevant passages from official FDA prescribing PDFs and citing the exact page — never by generating text from outside knowledge. Every answer is traceable to a physical PDF page. When the system cannot find evidence, it abstains instead of guessing.

---

## Project overview

PharmaLens is a local, evidence-grounded drug-information application designed around **official prescribing documents rather than free-form medical generation**.

The application is built to make drug-label information easier to search, compare, inspect, and audit while keeping the original PDF as the source of truth.

### Main user workflow

1. **Select a medicine** from the local document library.
2. **Ask a question** about the selected prescribing information.
3. PharmaLens applies its **safety gate** before retrieval.
4. The question is embedded with `all-MiniLM-L6-v2`.
5. **ChromaDB** retrieves the most relevant PDF passages.
6. The answer engine organizes the retrieved evidence by section intent.
7. The UI displays the result with **physical PDF page citations** and document-age information.
8. Users can inspect the original source page when needed.

### Key application areas

| Area | Purpose |
|---|---|
| **Q&A Chat** | Evidence-grounded questions about the selected medicine |
| **Drug Comparison** | Compare prescribing information for two medicines side by side |
| **Knowledge Base** | Browse extracted label sections and inspect the original PDF |
| **Safety & Audit** | Review safety boundaries and the recent request audit trail |
| **Administration** | Manage users, verify publisher sources, add documents, and reindex the local library |

### Screenshots

#### Drug comparison

The comparison view retrieves the relevant prescribing-document evidence for two medicines and presents the information side by side.

![PharmaLens drug comparison](screenshots/drug-comparison.png)

#### Published drug knowledge base

The Knowledge Base lets users browse the indexed medicines, inspect extracted sections, view document-age/provenance information, and open the relevant PDF source.

![PharmaLens knowledge base](screenshots/knowledge-base.png)

#### Safety & session audit

The Safety & Audit view exposes the application's safety boundaries and recent request outcomes, including references returned by the evidence pipeline.

![PharmaLens safety and audit](screenshots/safety-audit.png)

#### Administration and document library

Administrators can see the indexed medicine library, document age, revision information, publisher verification status, page counts, and indexed passage counts.

![PharmaLens administration library](screenshots/admin-library.png)


---

## Table of Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Bundled documents](#bundled-documents)
- [Roles](#roles)
- [Tech stack](#tech-stack)
- [Installation](#installation)
- [Evaluation](#evaluation)
- [Known limitations](#known-limitations)
- [Medical disclaimer](#medical-disclaimer)
- [Repository layout](#repository-layout)
- [License](#license)

---

## What it does

- **Grounded Q&A** — Ask about side effects, warnings, contraindications, storage, or indications for six real prescribing documents. Answers show page-level citations.
- **Drug comparison** — Compare two medicines side by side, section by section.
- **Step-by-step patient instructions** — Patient accounts see a "How to take it step by step" flow that returns numbered steps extracted directly from the label's Instructions for Use.
- **Document age tracking** — Each answer shows how old the printed revision is and offers a button to compare against the current file on the publisher's site.
- **Medical Safety Notice** — Every answer carries a full disclaimer reminding users this is not medical advice.
- **Safety layer** — Personal-advice questions ("should I stop taking this?") and emergency questions are caught by a two-stage classifier and return a safety message instead of an answer.
- **Session audit** — Every request is logged with the outcome, the outcome reason, and citation count.

---

## How it works

```text
User question
      │
      ▼
┌────────────────────────┐
│       Safety gate      │
│  · rule regexes        │
│  · semantic classifier │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│    Query embedding     │
│    all-MiniLM-L6-v2    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│    ChromaDB retrieval  │
│  cosine top-k, ≤ 0.75 │
│  junk-chunk filter     │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Section-aware      │
│   template extraction  │
│  (template_answers.py) │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Answer + page-level    │
│ citations               │
│                         │
│ · document age          │
│ · Medical Safety Notice │
└────────────────────────┘
```

No live LLM call is required. The current pipeline extracts sentences from the retrieved chunks and organises them by section intent (side effects, warnings, storage, indications).

---

## Bundled documents

| Medicine | Generic | Publisher |
|---|---|---|
| RINVOQ | upadacitinib | AbbVie |
| HUMIRA | adalimumab | AbbVie |
| SKYRIZI | risankizumab-rzaa | AbbVie |
| ELIQUIS | apixaban | Bristol Myers Squibb / Pfizer |
| OZEMPIC | semaglutide | Novo Nordisk |
| SYNTHROID | levothyroxine sodium | AbbVie |

Each PDF is indexed once on first run into a local ChromaDB store (~1,700 passages total).

---

## Roles

| Role | Capabilities |
|---|---|
| **Patient / Caregiver** | Q&A chat, step-by-step instructions, Knowledge Base browsing, plain-language explanations |
| **Healthcare Professional** | Same, plus clinical-style topic prompts |
| **Administrator** | Manage users, add prescribing documents, verify publisher sources, reindex |

---

## Tech stack

- **UI:** Streamlit
- **Vector store:** ChromaDB (persistent, local)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (runs offline)
- **PDF parsing:** PyMuPDF
- **Auth:** SQLite with PBKDF2 password hashing
- **Python:** 3.12

No API key is required for the current answer pipeline.

---

## Installation

### Prerequisites

- Python 3.12 (from [python.org](https://www.python.org/downloads/))
- VS Code (recommended)
- Internet access for the first setup (to download the embedding model)

### Setup

1. **Open the inner `PharmaLens` folder in VS Code** — the one that contains `app.py`.

2. **Run the setup script** in the VS Code PowerShell terminal:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup.ps1
   ```

   This creates `.venv`, installs locked dependencies, and indexes the six bundled PDFs. Takes 2–5 minutes on first run.

3. **Create your administrator account** (one-time):

   ```powershell
   .\.venv\Scripts\python.exe create_admin.py
   ```

4. **Start the app:**

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

   Open the URL printed in the terminal (usually `http://localhost:8501`).

---

## Evaluation

Three evaluation layers run offline. No API key required.

### Retrieval + safety metrics

```powershell
python evaluate.py
```

Results are written to `evaluation/report.json`.

Sample output from the bundled set:

| Metric | Value | Meaning |
|---|---:|---|
| Hit@5 | 0.91 | Top-5 retrieval contains a relevant page 91% of the time |
| MRR | 0.79 | When found, the correct page is usually ranked 1st or 2nd |
| Page recall | 0.43 | Against broad lexical gold lists |
| Page precision | 0.46 | Of returned pages, ~half are in the gold set |
| Safety accuracy | 0.81 | 13 of 16 smoke-test safety questions |
| Unsafe allowed | 0 | No personal/emergency question answered as informational |

### Answer-level metrics

```powershell
python evaluate_answers.py
```

Results are written to `evaluation/answers_report.json`.

Sample output:

| Metric | Value |
|---|---:|
| Abstention accuracy | 1.0 |
| Faithful claim rate | 0.8 |
| Keyword coverage | 0.47 |
| Mean latency (warm) | < 0.2 s |

---

## Known limitations

- **Small evaluation sets.** Retrieval evaluation uses 11 questions; safety uses 16. These are developer-authored smoke tests, not clinically adjudicated benchmarks.
- **Silver-annotated gold pages.** Retrieval gold pages are pages containing a predefined phrase, not independently adjudicated relevant pages.
- **Template extraction falls back on some inputs.** For OZEMPIC warnings specifically, the extractor falls through to a weaker sentence-detection path when the boxed warning is not present in the top-ranked chunks. Retrieval is unaffected.
- **No claim-level entailment.** The system verifies that claims appear verbatim in the retrieved text, but does not perform semantic entailment checks.
- **No automatic newer-source search.** The publisher comparison is a byte-level check, not a semantic comparison of content.
- **English-only.** PDFs and questions are expected in English.

---

## Medical disclaimer

> **PharmaLens is for informational and educational purposes only.**
>
> It does not provide medical diagnosis, treatment, or professional advice. Information retrieved from PDFs may be outdated, incomplete, or context-dependent. Do not start, stop, change, or substitute any medication or treatment based solely on this application. Always verify with a qualified healthcare professional and use the latest official clinical guidance. In an emergency, seek immediate medical care.

---

## Repository layout

```text
PharmaLens/
├── app.py                    Streamlit entry point
├── config.py                 Paths, model names, disclaimer text
├── accounts.py               Local auth (SQLite + PBKDF2)
├── portal_auth.py            Login and register UI
├── portal_user.py            Patient and professional portal
├── portal_admin.py           Admin portal
├── rag.py                    Retrieval + answer orchestration
├── ingest.py                 PDF chunking and indexing
├── prepare_library.py        Batch reindex the bundled PDFs
├── catalog.py                Document registry helpers
├── template_answers.py       Section-aware answer extraction
├── safety.py                 Rule + semantic safety layer
├── publication.py            Publication date detection
├── document_provenance.py    Revision + publisher comparison
├── pdf_evidence.py           Physical page access and citations
├── reference_features.py     Section browsing helpers
├── reference_views.py        Library, comparison, audit views
├── ui.py                     Theme and layout
├── evaluate.py               Retrieval + safety metrics
├── evaluate_answers.py       Answer-level metrics
├── create_admin.py           Bootstrap the first admin
├── setup.ps1                 One-shot install script
├── requirements.lock.txt     Pinned dependencies
├── data/                     Bundled PDFs and catalog
├── evaluation/               Evaluation sets and reports
└── tests/                    Pytest suite
```

---

## License

Local educational demo. Bundled PDFs remain the property of their respective publishers.
