#!/usr/bin/env python3
"""
db_access.py
Manages interactions with Anvil Data Tables.
This module defines functions that check for duplicate newsletters and insert
both raw email data and parsed sections into the relevant Data Tables.
"""

import anvil.tables as tables
from anvil.tables import app_tables


def newsletter_exists(newsletter_id: str) -> bool:
    # Checks if a newsletter with the given newsletter_id already exists.
    result = app_tables.newsletters.get(newsletter_id=newsletter_id)
    return result is not None


def update_newsletter_cleaned_body(newsletter_id: str, cleaned_body: str, raw_body: str = None) -> None:
    """
    Updates the cleaned_body field of an existing newsletter or creates a new one if it doesn't exist.
    
    Args:
        newsletter_id (str): The unique identifier of the newsletter
        cleaned_body (str): The cleaned text content to save
        raw_body (str, optional): The raw body text, only used if creating a new record
    """
    newsletter = app_tables.newsletters.get(newsletter_id=newsletter_id)
    if newsletter:
        # Update only the cleaned_body field
        newsletter['cleaned_body'] = cleaned_body
    else:
        # If record doesn't exist, create new with minimal data
        app_tables.newsletters.add_row(
            newsletter_id=newsletter_id,
            raw_body=raw_body,
            cleaned_body=cleaned_body
        )


def insert_newsletter(newsletter_id: str, newsletter: dict) -> None:
    # Inserts the raw newsletter data into the 'newsletters' Data Table.
    app_tables.newsletters.add_row(
        newsletter_id=newsletter_id,
        subject=newsletter.get("subject"),
        raw_body=newsletter.get("raw_body"),
        received_date=newsletter.get("received_date"),
        cleaned_body=newsletter.get("cleaned_body")
    )


def insert_parsed_sections(newsletter_id: str, parsed_data: dict) -> None:
    # Inserts parsed sections into the 'parsed_sections' Data Table.
    app_tables.parsed_sections.add_row(
        newsletter_id=newsletter_id,
        market_summary=parsed_data.get("MarketSummary"),
        key_levels=parsed_data.get("KeyLevels"),
        key_levels_raw=parsed_data.get("KeyLevelsRaw"),
        trading_plan=parsed_data.get("TradingPlan"),
        plan_summary=parsed_data.get("PlanSummary"),
        summary=parsed_data.get("summary"),
        timing_detail=parsed_data.get("timing_detail")
    )


def delete_most_recent_records() -> tuple[str | None, str | None]:
    """
    Deletes the most recent newsletter and its corresponding parsed sections.
    Returns a tuple of (newsletter_id, error_message).
    newsletter_id will be None if no records found or error occurs.
    error_message will be None if operation succeeds.
    """
    try:
        # Get the most recent newsletter by received_date
        all_newsletters = app_tables.newsletters.search(
            tables.order_by("received_date", ascending=False)
        )
        
        if not all_newsletters:
            return None, "No newsletters found in the database"
            
        # Get the first (most recent) newsletter
        newsletter = all_newsletters[0]
        newsletter_id = newsletter['newsletter_id']
        
        # Delete the corresponding parsed sections first (foreign key constraint)
        parsed_section = app_tables.parsed_sections.get(newsletter_id=newsletter_id)
        if parsed_section:
            parsed_section.delete()
            
        # Delete the newsletter
        newsletter.delete()
        
        return newsletter_id, None
        
    except Exception as e:
        return None, f"Error deleting records: {str(e)}" 