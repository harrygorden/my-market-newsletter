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
    """
    Primary function that orchestrates the entire newsletter processing workflow.
    Retrieves the latest newsletter, checks for duplicates, processes content,
    and saves data to various tables.
    """
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
    """
    Retrieve the most recent summary, timing details, and upcoming events
    from the parsed_sections table for display.
    
    Returns:
        dict: Dictionary containing summary, timing detail, and upcoming events
    """
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


if __name__ == "__main__":
    # Launch the newsletter processing as a background task
    task = anvil.server.launch_background_task('process_newsletter')