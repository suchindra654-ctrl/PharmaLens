# PharmaLens local demo

Extract into a NEW folder. Open the inner PharmaLens directory containing app.py in VS Code.
Install Python 3.12 from python.org if needed; `py --list` shows installed versions.
Run `powershell -ExecutionPolicy Bypass -File .\setup.ps1` in that folder.
The script installs locked dependencies and indexes the six bundled PDFs; first setup needs internet.
It preserves an existing .env. Enter your Gemini key there for generated answers.
Create your own administrator with `.\.venv\Scripts\python.exe create_admin.py`.
Start with `.\.venv\Scripts\python.exe -m streamlit run app.py`.

This release intentionally contains NO accounts, passwords, sessions, API keys,
virtual environment, cached embedding weights or prebuilt database. Previous demo
credentials do not apply to a fresh installation. Existing installations retain
their accounts if their .local directory is kept. Never overwrite .local or .env.

AI answers retain the second verification call against rendered PDF page images.
Source excerpts are retrieved text, not generated or clinically verified answers.
Publisher verification means an exact byte match at the time of checking, not
regulatory approval, clinical correctness or proof of the latest available edition.
Printed revision age is separate from the date of the publisher check.

Run `.\.venv\Scripts\python.exe evaluate.py` for the offline benchmark and
`.\.venv\Scripts\python.exe -m pytest tests -q` for regression tests.
Read EVALUATION.md before interpreting benchmark results. Local demo only.
