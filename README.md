# Financial News Entity Extraction (Flask + spaCy)

This is a simple Flask web application for a college project that
extracts finance-related entities from business or financial news text.
It uses spaCy for Named Entity Recognition (NER) and adds a few
rule-based patterns to detect:

- Company names
- Currencies / money amounts
- Stock tickers
- Economic indicators (GDP, inflation, interest rates, unemployment, etc.)
- Financial events (acquisitions, mergers, funding rounds, IPOs, earnings, ...)

## Project structure

- `app.py` – main Flask application with routes
- `ner_engine.py` – NER logic using spaCy and simple rules
- `data_loader.py` – helper for loading a sample FiNER dataset CSV
- `templates/index.html` – main UI page with a textarea and results section
- `static/style.css` – basic styling
- `requirements.txt` – Python dependencies

## Setup instructions

### 1. Create and activate a virtual environment

Using **PowerShell** on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

(If `python` does not work, try `py` instead.)

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Download the spaCy English model

```powershell
python -m spacy download en_core_web_sm
```

If you have a finance-specific spaCy model, you can edit
`ner_engine.py` and change the model name in `_load_spacy_model`.

### 4. (Optional) Prepare a FiNER sample file

If you have the FiNER dataset, place a small sample at:

- `data/finer_sample.csv`

Then you can experiment with it in a Python shell:

```powershell
python
>>> from data_loader import load_finer_sample
>>> df = load_finer_sample()
```

This will print the first few rows and show the columns. You can
connect those columns to the entity categories used in `ner_engine.py`.

### 5. Run the Flask app

From the project directory:

```powershell
python app.py
```

Then open your browser and go to:

- http://127.0.0.1:5000/

You should see the **Financial News Entity Extraction** page with a
sample article already filled in. Click **Extract Entities** to see
companies, currencies, stock tickers, economic indicators, and
financial events.

### 6. Sample input

The homepage already includes a sample Apple earnings news paragraph.
You can replace it with your own financial news text, such as:

> Tesla shares surged after the company reported record vehicle
> deliveries and announced plans for a new factory in Europe. The
> market is watching how rising interest rates and inflation might
> impact consumer demand in 2026.

## Notes

- This project is intentionally simple and is meant to be easy to read
  and present as a student project.
- For more accurate financial NER, you can fine-tune models or use
  specialized finance NLP packages, but the structure here will remain
  useful as a starting point.
