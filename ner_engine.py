"""NER engine for Financial News Entity Extraction.

This module uses spaCy to perform Named Entity Recognition (NER) on
financial or business news text and then maps spaCy entities + simple
rule-based patterns into custom finance-focused categories.
"""

from __future__ import annotations

from typing import Dict, List, Any

import re

import spacy


def _load_spacy_model(model_name: str = "en_core_web_sm"):
    """Load a spaCy model.

    For this project we default to ``en_core_web_sm``. If you have a
    finance-specific model (for example, one of the spaCy/FinBERT-based
    models), you can change the model name here.
    """

    try:
        nlp_model = spacy.load(model_name)
    except OSError as exc:
        raise RuntimeError(
            "spaCy model not found. Please install it with: "
            "`python -m spacy download en_core_web_sm`"
        ) from exc
    return nlp_model


# Load the model once at import time so requests are fast.
NLP = _load_spacy_model()


def perform_ner(text: str) -> Dict[str, Any]:
    """Run NER on input text and group entities into finance categories.

    Parameters
    ----------
    text : str
        Raw financial or business news text.

    Returns
    -------
    dict
        JSON-serializable dictionary with the following keys:

        - ``companies``: list of company names
        - ``currencies``: list of currency mentions or money amounts
        - ``stock_tickers``: list of detected stock ticker symbols
        - ``economic_indicators``: list of high-level macro indicators
        - ``financial_events``: list of dicts with ``text`` and ``subtype``
        - ``other_entities``: list of "entity (LABEL)" strings
    """

    doc = NLP(text)

    results: Dict[str, Any] = {
        "companies": [],
        "currencies": [],
        "stock_tickers": [],
        "economic_indicators": [],
        "financial_events": [],
        "other_entities": [],
    }

    # Helper sets to avoid duplicates
    seen_simple = {key: set() for key in ("companies", "currencies", "stock_tickers", "economic_indicators", "other_entities")}
    seen_events = set()

    # --- 1. Map spaCy entities to our custom buckets ---
    for ent in doc.ents:
        ent_text = ent.text.strip()
        if not ent_text:
            continue

        label = ent.label_

        # Companies: mostly ORG; optionally some GPE with company-like suffixes.
        if label == "ORG" or (
            label in {"GPE", "FAC"}
            and any(suffix in ent_text.lower() for suffix in [
                "corp", "inc", "ltd", "limited", "bank", "plc", "llc", "group", "fund", "capital",
            ])
        ):
            if ent_text not in seen_simple["companies"]:
                seen_simple["companies"].add(ent_text)
                results["companies"].append(ent_text)

        # Currencies / money amounts
        elif label == "MONEY":
            if ent_text not in seen_simple["currencies"]:
                seen_simple["currencies"].add(ent_text)
                results["currencies"].append(ent_text)

        else:
            # Keep other named entities for reference
            key = f"{ent_text} ({label})"
            if key not in seen_simple["other_entities"]:
                seen_simple["other_entities"].add(key)
                results["other_entities"].append(key)

    # --- 2. Simple regex-based stock ticker detection ---
    # Looks for sequences of 1-5 uppercase letters, which is common for US tickers.
    ticker_pattern = re.compile(r"\b[A-Z]{1,5}\b")
    non_ticker_stopwords = {"GDP", "CPI", "PMI", "CEO", "CFO", "IPO"}

    for match in ticker_pattern.finditer(text):
        ticker = match.group(0)
        if ticker in non_ticker_stopwords:
            continue
        if ticker not in seen_simple["stock_tickers"]:
            seen_simple["stock_tickers"].add(ticker)
            results["stock_tickers"].append(ticker)

    # --- 3. Economic indicators: keyword-based search ---
    lower_text = text.lower()

    econ_keywords = {
        "gdp": "GDP",
        "gross domestic product": "GDP",
        "inflation": "Inflation",
        "interest rate": "Interest rate",
        "interest rates": "Interest rates",
        "unemployment": "Unemployment",
        "jobless rate": "Unemployment",
        "cpi": "CPI",
        "consumer price index": "CPI",
        "pmi": "PMI",
        "purchasing managers' index": "PMI",
        "growth rate": "Growth rate",
    }

    for phrase, normalized_name in econ_keywords.items():
        if phrase in lower_text and normalized_name not in seen_simple["economic_indicators"]:
            seen_simple["economic_indicators"].add(normalized_name)
            results["economic_indicators"].append(normalized_name)

    # --- 4. Financial events: keyword-based with subtypes ---
    event_keywords = {
        "acquisition": "acquisition",
        "acquires": "acquisition",
        "acquired": "acquisition",
        "merger": "merger",
        "merge": "merger",
        "merged": "merger",
        "funding round": "funding",
        "series a": "funding",
        "series b": "funding",
        "series c": "funding",
        "investment round": "funding",
        "ipo": "ipo",
        "initial public offering": "ipo",
        "went public": "ipo",
        "earnings": "earnings",
        "earnings call": "earnings",
        "earnings report": "earnings",
        "dividend": "dividend",
        "bankruptcy": "bankruptcy",
        "filed for chapter": "bankruptcy",
    }

    for phrase, subtype in event_keywords.items():
        start = 0
        while True:
            idx = lower_text.find(phrase, start)
            if idx == -1:
                break
            snippet = text[idx : idx + len(phrase)]
            event_key = (snippet, subtype)
            if event_key not in seen_events:
                seen_events.add(event_key)
                results["financial_events"].append({"text": snippet, "subtype": subtype})
            start = idx + len(phrase)

    return results
