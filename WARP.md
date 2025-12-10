# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development commands

### Environment setup
- Create a virtual environment (PowerShell on Windows):
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
- Install dependencies:
  - `pip install -r requirements.txt`
- Download the required spaCy English model (must be done once):
  - `python -m spacy download en_core_web_sm`

### Running the web app
From the project root:

- Start the Flask development server:
  - `python app.py`
- The app serves a single page at `http://127.0.0.1:5000/` with a sample article pre-filled. Submissions POST to `/extract`.

### Working with the FiNER sample dataset (optional)
If you have a FiNER CSV at `data/finer_sample.csv`:

- Open a Python shell and load a small sample:
  - `python`
  - `>>> from data_loader import load_finer_sample`
  - `>>> df = load_finer_sample()`

This is useful for exploring how dataset columns could map to the custom entity categories used in `ner_engine.py`.

### Linting and tests
The repository does not currently define any linting or test commands or configuration. If you introduce them, update this section with the exact commands (e.g., how to run the full suite vs. an individual test).

## High-level architecture

### Overview
This is a small Flask + spaCy project intended as an easy-to-read college project that demonstrates financial news entity extraction. The stack is:

- **Backend**: Flask app (`app.py`) exposing two routes and orchestrating NER.
- **NER engine**: spaCy-based entity extraction with light rule-based post-processing (`ner_engine.py`).
- **Data helper**: Optional FiNER dataset loader (`data_loader.py`) for experimentation.
- **Frontend**: A single HTML template (`templates/index.html`) styled with CSS (`static/style.css`).

There is no database or background processing; all work happens synchronously in the request/response cycle.

### Flask layer (`app.py` + templates)

- `app.py` creates a Flask app and defines:
  - `GET /` (`index`): Renders `templates/index.html` with a sample article (`SAMPLE_TEXT`), no results, and no error.
  - `POST /extract` (`extract`):
    - Reads the `text` field from the submitted form.
    - Enforces basic validation (non-empty, max length 10,000 characters).
    - Calls `perform_ner(text)` from `ner_engine.py` when valid.
    - Renders `index.html` with the original input, any extracted `results`, and an `error` message if validation fails.
- `templates/index.html` is a Jinja2 template that:
  - Displays the textarea pre-populated with `input_text`.
  - Shows a validation error banner when `error` is set.
  - Renders extracted entities when `results` is not `None`, grouping them into cards/tables using keys from the NER output (see below).
  - Imports styling via `{{ url_for('static', filename='style.css') }}`.

**Important coupling**: The template expects `results` to be a dictionary with the following keys:

- `companies`
- `currencies`
- `stock_tickers`
- `economic_indicators`
- `financial_events`
- `other_entities`

If you change `perform_ner` to rename or remove these keys, you must update the template accordingly.

### NER engine (`ner_engine.py`)

- On import, `_load_spacy_model()` is called with `"en_core_web_sm"` and assigned to a module-level `NLP` object:
  - This keeps request handling fast (model is loaded once), but any failure to load the model will raise at import time, preventing the Flask app from starting until `en_core_web_sm` is installed.
- `perform_ner(text: str) -> dict` is the main entry point used by the Flask app. It:
  1. Runs the spaCy pipeline over the input text (`doc = NLP(text)`).
  2. Initializes a `results` dict with the keys listed above and tracks per-key `seen_*` sets to deduplicate entities.
  3. **Maps spaCy entities** to project-specific buckets:
     - `ORG` entities, plus some `GPE`/`FAC` with company-like suffixes (`corp`, `inc`, `bank`, etc.), go into `companies`.
     - `MONEY` entities go into `currencies`.
     - All other entities are preserved in `other_entities` as strings of the form `"<text> (<LABEL>)"` (e.g., `"United States (GPE)"`).
  4. **Adds stock tickers** using a regex `\b[A-Z]{1,5}\b`, filtering out known non-ticker all-caps tokens (`GDP`, `CPI`, etc.). Results go into `stock_tickers`.
  5. **Detects economic indicators** by scanning the lowercased text for a set of phrases (e.g., `"inflation"`, `"interest rates"`, `"consumer price index"`) and normalizing them into display names like `"Inflation"`, `"Interest rates"`. These populate `economic_indicators`.
  6. **Detects financial events** via keyword-based phrases (acquisitions, mergers, funding rounds, IPOs, earnings, dividends, bankruptcies). For each occurrence it records a small snippet and a `subtype` string into `financial_events`, e.g. `{"text": "earnings call", "subtype": "earnings"}`.

When extending the project (e.g., adding new categories or refining detection rules), keep the following in mind:

- The `results` schema is the contract between `perform_ner` and `templates/index.html`. Add new keys only if you also update the template.
- Regex and keyword lists are simple and intentionally transparent for teaching; prefer adding new phrases or refining these lists over introducing heavy machinery unless the project requirements change.

### Data helper (`data_loader.py`)

- `load_finer_sample(path="data/finer_sample.csv", n_rows=5)` reads a small CSV sample via pandas, prints basic metadata (path, columns, head), and returns a DataFrame.
- This module is not used by the Flask app at runtime; it exists to:
  - Demonstrate how a labeled FiNER dataset might be inspected.
  - Help map dataset labels/columns to the custom categories defined in `ner_engine.py` if you later integrate supervised training.

If you introduce any automatic dataset loading into the web app, keep it separate from request handlers or behind a clear initialization step so that missing local files do not prevent the basic demo from running.

### Frontend styling (`static/style.css`)

- Provides layout and visual styling (container, cards, results grid, tables, inline chips for `other_entities`).
- There is no frontend JS; form submission is a full page reload handled by the Flask routes.

Changes to class names or structure in `index.html` should be mirrored here to keep the UI readable, but there is no complex frontend logic to coordinate.
