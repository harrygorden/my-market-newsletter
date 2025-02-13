import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import re
import spacy
#!/usr/bin/env python3
"""
email_parser.py
Updated to use spaCy for cleaning the email text (stored in newsletters.clean_body)
and improving section extraction for the parsed_sections table.
"""

# Load the spaCy model at module-level (for caching reasons)
try:
    import en_core_web_sm
    nlp = en_core_web_sm.load()
except Exception as e:
    print("Error loading spaCy model en_core_web_sm:", e)
    nlp = None


def clean_newsletter(raw_body: str) -> str:
    """
    Clean and optimize raw newsletter text using spaCy and regex.
    Normalizes whitespace and reassembles sentences.
    """
    # Normalize whitespace with regex
    cleaned = re.sub(r'\s+', ' ', raw_body).strip()
    
    # If spaCy is available, use it to segment and rebuild sentences
    if nlp:
        doc = nlp(cleaned)
        # Reassemble text from sentences to ensure proper spacing and punctuation.
        cleaned = " ".join([sent.text.strip() for sent in doc.sents])
    return cleaned


def parse_email(raw_body: str) -> dict:
    """
    Parses the raw newsletter email.
    This function cleans the raw text and then extracts sections via regex.
    The cleaning process uses spaCy for sentence segmentation.
    
    Returns a dictionary with the following keys:
      - cleaned_body : the optimized version of raw_body (to be stored in the newsletters table)
      - MarketSummary: extracted text following "Market Commentary:"
      - KeyLevels and KeyLevelsRaw: extracted text following "Key Signals:"
      - TradingPlan: extracted text following "Trading Plan:"
      - PlanSummary: the first sentence of the trading plan (using spaCy if available)
      - summary: a combined abbreviated summary of the Market Commentary and Trading Plan
    """
    # Clean the text
    cleaned_body = clean_newsletter(raw_body)
    parsed = {"cleaned_body": cleaned_body}

    # Extract "Market Commentary" section.
    market_match = re.search(
        r"Market Commentary:\s*(.*?)(?=Key Signals:|Trading Plan:|$)",
        cleaned_body,
        re.DOTALL | re.IGNORECASE
    )
    market_text = market_match.group(1).strip() if market_match else ""
    parsed["MarketSummary"] = market_text

    # Extract "Key Signals" section.
    key_signals_match = re.search(
        r"Key Signals:\s*(.*?)(?=Trading Plan:|Market Commentary:|$)",
        cleaned_body,
        re.DOTALL | re.IGNORECASE
    )
    key_signals_text = key_signals_match.group(1).strip() if key_signals_match else ""
    parsed["KeyLevels"] = key_signals_text
    parsed["KeyLevelsRaw"] = key_signals_text

    # Extract "Trading Plan" section.
    trading_plan_match = re.search(
        r"Trading Plan:\s*(.*)",
        cleaned_body,
        re.DOTALL | re.IGNORECASE
    )
    trading_plan_text = trading_plan_match.group(1).strip() if trading_plan_match else ""
    parsed["TradingPlan"] = trading_plan_text

    # Create a Plan Summary using spaCy sentence segmentation (fallback to regex if not available)
    if trading_plan_text:
        if nlp:
            doc = nlp(trading_plan_text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            plan_summary = sentences[0] if sentences else ""
        else:
            sentences = re.split(r'\.\s+', trading_plan_text)
            plan_summary = sentences[0] if sentences else ""
        parsed["PlanSummary"] = plan_summary
    else:
        parsed["PlanSummary"] = ""

    # Generate an abbreviated summary combining key insights from Market Commentary and Trading Plan.
    market_excerpt = (market_text[:50] + "...") if len(market_text) > 50 else market_text
    plan_excerpt = (trading_plan_text[:50] + "...") if len(trading_plan_text) > 50 else trading_plan_text
    parsed["summary"] = f"{market_excerpt} | {plan_excerpt}"

    return parsed 