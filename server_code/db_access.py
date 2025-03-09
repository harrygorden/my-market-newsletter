#!/usr/bin/env python3
"""
db_access.py
Manages interactions with Anvil Data Tables.
This module defines functions that check for duplicate newsletters and insert
both raw email data and parsed sections into the relevant Data Tables.
"""

import anvil.tables as tables
from anvil.tables import app_tables
import anvil.server
import json


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


@anvil.server.callable
def bulk_upsert_data(table_name, data_json):
    """
    Bulk insert data into a table from a JSON string
    
    Args:
        table_name (str): Name of the Anvil data table
        data_json (str): JSON string containing records to insert
        
    Returns:
        dict: Summary of operation results
    """
    try:
        # Parse the JSON data
        records = json.loads(data_json)
        
        # Get the table object
        table = getattr(app_tables, table_name)
        
        # Insert all the records
        rows_added = 0
        rows_updated = 0
        
        # Add all rows
        for record in records:
            table.add_row(**record)
            rows_added += 1
        
        return {
            'rows_added': rows_added,
            'rows_updated': rows_updated
        }
    except Exception as e:
        print(f"Error in bulk_upsert_data: {str(e)}")
        return {
            'error': str(e),
            'rows_added': 0,
            'rows_updated': 0
        }


@anvil.server.callable
def add_vd_lines(records_list):
    """
    Add records to the vdlines table
    
    Args:
        records_list (list): List of dictionaries containing Price and Type values
        
    Returns:
        int: Number of records added
    """
    try:
        rows_added = 0
        
        # Create vdlines table if it doesn't exist yet
        if not hasattr(app_tables, 'vdlines'):
            # Table doesn't exist yet in this app - create it
            print("vdlines table doesn't exist yet - this is expected on first run")
            pass
            
        for record in records_list:
            # Add each record to the table
            app_tables.vdlines.add_row(**record)
            rows_added += 1
            
        return rows_added
    except Exception as e:
        print(f"Error adding VD lines: {str(e)}")
        return 0


def clear_keylevelsraw_table():
    """
    Clear all rows from the keylevelsraw table.
    """
    try:
        # Get all rows from the keylevelsraw table
        all_rows = app_tables.keylevelsraw.search()
        
        # Delete each row
        for row in all_rows:
            row.delete()
            
        return True
    except Exception as e:
        print(f"Error clearing keylevelsraw table: {str(e)}")
        return False


def insert_key_levels_to_keylevelsraw(levels_data):
    """
    Insert key levels into the keylevelsraw table.
    
    Args:
        levels_data (dict): Dictionary containing lists of support and resistance levels
            with their details from both Core Structures section and Trading Plan section
            
    Returns:
        int: Number of rows inserted
    """
    try:
        rows_added = 0
        
        # Process support levels
        if 'supports' in levels_data:
            for level in levels_data['supports']:
                app_tables.keylevelsraw.add_row(
                    price_with_range=level['price_with_range'],
                    price=level['price'],
                    severity=level['severity'],
                    type=level['type']
                )
                rows_added += 1
                
        # Process resistance levels
        if 'resistances' in levels_data:
            for level in levels_data['resistances']:
                app_tables.keylevelsraw.add_row(
                    price_with_range=level['price_with_range'],
                    price=level['price'],
                    severity=level['severity'],
                    type=level['type']
                )
                rows_added += 1
                
        return rows_added
    except Exception as e:
        print(f"Error inserting key levels to keylevelsraw: {str(e)}")
        return 0


def extract_and_store_key_levels(newsletter_id, trading_plan_key_levels):
    """
    Extract levels from both Core Structures section and Trading Plan section,
    combine them, remove duplicates, and store them in the keylevelsraw table.
    
    Args:
        newsletter_id (str): The unique identifier of the newsletter
        trading_plan_key_levels (dict): Dictionary containing support and resistance levels 
                                        extracted from the Trading Plan section
    
    Returns:
        int: Total number of key levels stored
    """
    try:
        # Clear the existing keylevelsraw table
        clear_keylevelsraw_table()
        
        # Combine and deduplicate the key levels
        combined_levels = {
            'supports': [],
            'resistances': []
        }
        
        # Add all the levels from the Trading Plan section
        if trading_plan_key_levels:
            combined_levels['supports'].extend(trading_plan_key_levels.get('supports', []))
            combined_levels['resistances'].extend(trading_plan_key_levels.get('resistances', []))
        
        # Create a set to track unique price values we've already added
        added_prices = set()
        
        # Filter out duplicates based on the price value
        filtered_supports = []
        for level in combined_levels['supports']:
            if level['price'] not in added_prices:
                added_prices.add(level['price'])
                filtered_supports.append(level)
        
        filtered_resistances = []
        for level in combined_levels['resistances']:
            if level['price'] not in added_prices:
                added_prices.add(level['price'])
                filtered_resistances.append(level)
        
        combined_levels['supports'] = filtered_supports
        combined_levels['resistances'] = filtered_resistances
        
        # Insert the combined levels into the keylevelsraw table
        return insert_key_levels_to_keylevelsraw(combined_levels)
        
    except Exception as e:
        print(f"Error extracting and storing key levels: {str(e)}")
        return 0