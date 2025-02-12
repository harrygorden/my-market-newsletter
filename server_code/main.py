#!/usr/bin/env python3
"""
main.py
This is the orchestrator for the Newsletter Aggregator App.
It retrieves the latest newsletter email, checks for duplicates,
parses its contents, and then stores both raw and parsed data into Anvil Data Tables.
"""

import logging
from gmail_client import get_latest_newsletter
from email_parser import parse_email
from db_access import newsletter_exists, insert_newsletter, insert_parsed_sections


def process_newsletter():
    try:
        # Retrieve the latest newsletter email
        newsletter = get_latest_newsletter()
        if not newsletter:
            logging.info("No newsletter email found.")
            return

        newsletter_id = newsletter.get("received_date")  # using the received_date as the identifier

        # Skip if this newsletter has already been processed
        if newsletter_exists(newsletter_id):
            logging.info(f"Newsletter '{newsletter_id}' already processed. Skipping.")
            return

        # Parse the raw email to extract key sections and a summary
        parsed_data = parse_email(newsletter.get("raw_body"))

        # Save the raw newsletter data
        insert_newsletter(newsletter_id, newsletter)

        # Save the parsed sections and summary
        insert_parsed_sections(newsletter_id, parsed_data)

        logging.info("Newsletter processed successfully.")

    except Exception as e:
        logging.error(f"Error processing newsletter: {e}")


if __name__ == "__main__":
    # This callable function runs through the entire process.
    process_newsletter() 