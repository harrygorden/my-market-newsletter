#!/usr/bin/env python3
"""
email_parser.py
Parses the raw newsletter email.
This module uses regex (and optionally spaCy or BeautifulSoup) to extract sections such as Market Commentary,
Key Signals and Trading Plan, and then builds a summary.
"""

import re

# Optionally, import spaCy for advanced NLP tasks if needed.
# import spacy
# try:
#     nlp = spacy.load("en_core_web_sm")
# except Exception:
#     nlp = None


def parse_email(raw_body: str) -> dict:
    parsed = {}

    # Extract "Market Commentary"
    market_commentary_match = re.search(r"Market Commentary:\s*(.*?)(?:\n{2,}|$)", raw_body, re.DOTALL)
    parsed["MarketSummary"] = market_commentary_match.group(1).strip() if market_commentary_match else ""

    # Extract "Key Signals" (used for KeyLevels and KeyLevelsRaw)
    key_signals_match = re.search(r"Key Signals:\s*(.*?)(?:\n{2,}|$)", raw_body, re.DOTALL)
    key_signals_text = key_signals_match.group(1).strip() if key_signals_match else ""
    parsed["KeyLevels"] = key_signals_text
    parsed["KeyLevelsRaw"] = key_signals_text

    # Extract "Trading Plan"
    trading_plan_match = re.search(r"Trading Plan:\s*(.*?)(?:\n{2,}|$)", raw_body, re.DOTALL)
    trading_plan_text = trading_plan_match.group(1).strip() if trading_plan_match else ""
    parsed["TradingPlan"] = trading_plan_text

    # Create a Plan Summary (e.g., the first sentence of the trading plan)
    if trading_plan_text:
        sentences = re.split(r'\.\s+', trading_plan_text)
        parsed["PlanSummary"] = sentences[0] if sentences else ""
    else:
        parsed["PlanSummary"] = ""

    # Generate an abbreviated summary combining key insights
    market_excerpt = parsed["MarketSummary"][:50] + "..." if len(parsed["MarketSummary"]) > 50 else parsed["MarketSummary"]
    plan_excerpt = parsed["TradingPlan"][:50] + "..." if len(parsed["TradingPlan"]) > 50 else parsed["TradingPlan"]
    parsed["summary"] = f"{market_excerpt} | {plan_excerpt}"

    return parsed 