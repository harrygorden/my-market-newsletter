#!/usr/bin/env python3
"""
main.py
This is the orchestrator for the Newsletter Aggregator App.
It retrieves the latest newsletter email, checks for duplicates,
parses its contents, and then stores both raw and parsed data into Anvil Data Tables.
"""

import logging
from datetime import datetime
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from gmail_client import get_latest_newsletter
from email_parser import (
    clean_newsletter,
    parse_email,
)
from db_access import (
    newsletter_exists,
    insert_newsletter,
    insert_parsed_sections,
    delete_most_recent_records as db_delete_most_recent,
    extract_and_store_key_levels
)
from market_calendar import update_upcoming_events
from send_summary import send_summary_email


@anvil.server.background_task
@anvil.server.callable
def process_newsletter():
    try:
        print("=== Starting process_newsletter ===")
        # Retrieve the latest newsletter email
        print("Calling get_latest_newsletter...")
        newsletter = get_latest_newsletter()
        if not newsletter:
            print("No newsletter email found.")
            return
        print(f"Newsletter retrieved with subject: {newsletter.get('subject')}")

        # Convert the ISO format date to YYYYMMDD format
        print("Converting date format...")
        received_date = datetime.fromisoformat(newsletter.get("received_date"))
        newsletter_id = received_date.strftime("%Y%m%d")
        print(f"Generated newsletter_id: {newsletter_id}")

        # Skip if this newsletter has already been processed
        print("Checking for existing newsletter...")
        if newsletter_exists(newsletter_id):
            print(f"Newsletter '{newsletter_id}' already processed. Skipping.")
            return
        print("Newsletter is new, proceeding with processing")

        # Clean the newsletter content first
        print("Cleaning newsletter content...")
        cleaned_body = clean_newsletter(newsletter.get("raw_body"))
        print(f"Cleaned body length: {len(cleaned_body)}")
        print(f"First 100 characters of cleaned body: {cleaned_body[:100]}")
        print("Newsletter cleaning completed")

        # Parse the cleaned email to extract key sections and a summary
        print("Parsing email content...")
        parsed_data = parse_email(cleaned_body)
        print("Email parsing completed")

        # Save the newsletter data with both raw and cleaned content
        print("Saving newsletter data...")
        newsletter["cleaned_body"] = cleaned_body
        insert_newsletter(newsletter_id, newsletter)
        print("Newsletter data saved successfully")

        # Save the parsed sections and summary
        print("Saving parsed sections...")
        insert_parsed_sections(newsletter_id, parsed_data)
        print("Parsed sections saved successfully")
        
        # Extract and store key levels from both Trading Plan and Key Levels Detail sections
        print("Extracting and storing key levels...")
        key_levels_count = extract_and_store_key_levels(
            newsletter_id, 
            parsed_data.get("TradingPlanKeyLevels"),
            parsed_data.get("KeyLevelsDetail", [])
        )
        print(f"Extracted and stored {key_levels_count} key levels from the newsletter")
        
        # Update upcoming events
        print("Updating upcoming events...")
        update_upcoming_events(newsletter_id)
        print("Upcoming events updated successfully")

        # After successfully processing the newsletter
        print("Sending summary email...")
        send_summary_email()
        print("Summary email sent successfully")

        print("Newsletter processed successfully.")
        print("=== process_newsletter completed ===")

    except Exception as e:
        print(f"Error processing newsletter: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e.__dict__)}")
        raise


@anvil.server.callable
def delete_most_recent_records():
    """
    Deletes the most recent newsletter and its corresponding parsed sections.
    Returns the deleted newsletter_id or None if no records found.
    """
    try:
        print("=== Starting deletion of most recent records ===")
        
        newsletter_id, error = db_delete_most_recent()
        
        if error:
            print(error)
            return None
            
        if newsletter_id:
            print(f"Successfully deleted newsletter {newsletter_id} and its parsed sections")
        
        print("=== Deletion completed successfully ===")
        return newsletter_id
        
    except Exception as e:
        print(f"Error in delete_most_recent_records: {str(e)}")
        raise


@anvil.server.callable
def print_data_to_form():
    # Get the most recent summary from parsed_sections table
    latest_sections = app_tables.parsed_sections.search(
        tables.order_by("newsletter_id", ascending=False)
    )
    
    if latest_sections:
        latest = latest_sections[0]
        return {
            'summary': latest['summary'],
            'timing_detail': latest['timing_detail'],
            'upcoming_events': latest['upcoming_events']
        }
    return {
        'summary': "No summary available",
        'timing_detail': "No timing information available",
        'upcoming_events': "No upcoming events available"
    }


@anvil.server.callable
def get_all_lines_data():
    """
    Retrieves all rows from the keylevelsraw table for display in the AllLines form.
    
    Returns:
        list: A list of dictionaries representing each row in the keylevelsraw table
    """
    try:
        # Get all rows from the keylevelsraw table
        key_levels = app_tables.keylevelsraw.search()
        
        # Print debugging information about what was retrieved
        print(f"Retrieved {len(key_levels)} rows from keylevelsraw table")
        if len(key_levels) > 0:
            print(f"First row column names: {list(key_levels[0].keys())}")
            print(f"First row values: {list(key_levels[0].values())}")
        
        # Convert rows to a list of dictionaries for the data grid
        result = []
        for row in key_levels:
            result.append({
                "price": row.get("price_with_range") or row.get("price", ""),
                "major": row.get("severity", ""),
                "notes": row.get("note", ""),
                "vdline": row.get("vdline", ""),
                "vdline_type": row.get("vdline_type", "")
            })
        
        # Print debug info about the result
        print(f"Returning {len(result)} formatted rows")
        if len(result) > 0:
            print(f"First result item keys: {result[0].keys()}")
            print(f"First result item values: {list(result[0].values())}")
            
        # Return the list of dictionaries
        return result
    except Exception as e:
        print(f"Error retrieving data from keylevelsraw: {str(e)}")
        # Return an empty list in case of error
        return []


@anvil.server.background_task
@anvil.server.callable
def refresh_all_lines_data_bg():
    """
    Background task version of get_all_lines_data with enhanced logging.
    
    Returns:
        list: A list of dictionaries representing each row in the keylevelsraw table
    """
    try:
        print("=== Starting refresh_all_lines_data_bg background task ===")
        
        # Get all rows from the keylevelsraw table
        print("Querying keylevelsraw table...")
        key_levels = app_tables.keylevelsraw.search()
        
        # Print detailed debugging information
        row_count = len(key_levels)
        print(f"Retrieved {row_count} rows from keylevelsraw table")
        
        # Print all available tables for debugging
        all_tables = [table.__name__ for table in dir(app_tables) if not table.startswith('_')]
        print(f"Available tables: {all_tables}")
        
        # Print table schema for keylevelsraw
        if 'keylevelsraw' in all_tables:
            print("keylevelsraw table schema:")
            try:
                schema = app_tables.keylevelsraw.list_columns()
                print(f"Table columns: {schema}")
            except Exception as e:
                print(f"Error getting schema: {str(e)}")
        
        if row_count > 0:
            print("First row details:")
            first_row = key_levels[0]
            print(f"First row column names: {list(first_row.keys())}")
            print(f"First row values: {list(first_row.values())}")
            for key, value in first_row.items():
                print(f"  {key}: {value} (type: {type(value).__name__})")
        else:
            print("No rows found in keylevelsraw table. This may indicate:")
            print("1. The extract_and_store_key_levels function did not insert any data")
            print("2. The table exists but is empty")
            print("3. There might be permission issues accessing the table")
        
        # Convert rows to a list of dictionaries for the data grid
        print("Converting database rows to dictionary format for DataGrid...")
        result = []
        for row in key_levels:
            row_dict = {
                "price": row.get("price_with_range") or row.get("price", ""),
                "major": row.get("severity", ""),
                "notes": row.get("note", ""),
                "vdline": row.get("vdline", ""),
                "vdline_type": row.get("vdline_type", "")
            }
            result.append(row_dict)
            # Print for the first few rows to debug data transformation
            if len(result) <= 3:
                print(f"Transformed row {len(result)}: {row_dict}")
        
        # Print debug info about the result
        print(f"Returning {len(result)} formatted rows")
        if len(result) > 0:
            print(f"First result item keys: {result[0].keys()}")
            print(f"Sample data: {result[:3]}")
            
        print("=== refresh_all_lines_data_bg completed successfully ===")
        # Return the list of dictionaries
        return result
    except Exception as e:
        print(f"=== ERROR in refresh_all_lines_data_bg: {str(e)} ===")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Return an empty list in case of error to avoid crashing the client
        return {"error": str(e)}


@anvil.server.callable
def debug_keylevelsraw_table():
    """
    Debug function to directly check the contents of the keylevelsraw table
    and print detailed information about each row.
    
    Returns:
        dict: Debug information about the table
    """
    try:
        # Get all rows from the keylevelsraw table
        rows = app_tables.keylevelsraw.search()
        row_count = len(rows)
        
        print(f"=== DEBUG: keylevelsraw table ===")
        print(f"Found {row_count} rows in keylevelsraw table")
        
        # Get column names from the first row if available
        column_names = []
        if row_count > 0:
            column_names = list(rows[0].keys())
            print(f"Column names: {column_names}")
        
        # Print details of each row
        for i, row in enumerate(rows):
            print(f"Row {i+1}:")
            for col in column_names:
                print(f"  {col}: {row[col]}")
            print("---")
        
        return {
            "row_count": row_count,
            "column_names": column_names,
            "sample_rows": [{col: row[col] for col in column_names} for row in rows[:3]] if row_count > 0 else []
        }
        
    except Exception as e:
        print(f"Error in debug_keylevelsraw_table: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Launch the newsletter processing as a background task
    task = anvil.server.launch_background_task('process_newsletter') 