#!/usr/bin/env python3
"""
send_summary.py
Handles sending newsletter summaries and upcoming market events via email
using Gmail integration in Anvil.
"""

import anvil.google.mail
import anvil.secrets
from anvil.tables import app_tables
import anvil.tables as tables


def format_email_content(summary_data):
    """
    Formats the email content with HTML styling.
    """
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Market Newsletter Summary</h2>
        
        <h3>Summary</h3>
        <p>{summary_data.get('summary', 'No summary available')}</p>
        
        <h3>Market Timing</h3>
        <p>{summary_data.get('timing_detail', 'No timing information available')}</p>
        
        <h3>Upcoming Market Events</h3>
        <p>{summary_data.get('upcoming_events', 'No upcoming events available')}</p>
        
        <hr>
        <p style="font-size: 0.8em; color: #666;">
            This is an automated summary from your Market Newsletter Aggregator
        </p>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Market Newsletter Summary

    Summary:
    {summary_data.get('summary', 'No summary available')}

    Market Timing:
    {summary_data.get('timing_detail', 'No timing information available')}

    Upcoming Market Events:
    {summary_data.get('upcoming_events', 'No upcoming events available')}

    --
    This is an automated summary from your Market Newsletter Aggregator
    """
    
    return html_content, text_content


def get_latest_summary():
    """
    Retrieves the most recent summary from the parsed_sections table.
    """
    latest_sections = app_tables.parsed_sections.search(
        tables.order_by("newsletter_id", ascending=False)
    )
    
    if not latest_sections:
        return None
        
    latest = latest_sections[0]
    return {
        'summary': latest['summary'],
        'timing_detail': latest['timing_detail'],
        'upcoming_events': latest['upcoming_events']
    }


@anvil.server.callable
def send_summary_email():
    """
    Sends the latest newsletter summary and upcoming events via email.
    Uses Gmail integration and retrieves recipient addresses from Anvil secrets.
    """
    try:
        # Get the latest summary data
        summary_data = get_latest_summary()
        if not summary_data:
            print("No summary data available to send")
            return False
            
        # Get email addresses from secrets
        to_address = anvil.secrets.get_secret('recipient_email')
        bcc_addresses = anvil.secrets.get_secret('recipient_bcc')
        
        # Format the email content
        html_content, text_content = format_email_content(summary_data)
        
        # Send the email
        anvil.google.mail.send(
            to=to_address,
            bcc=bcc_addresses,
            subject="Market Newsletter Summary",
            html=html_content,
            text=text_content
        )
        
        print("Summary email sent successfully")
        return True
        
    except Exception as e:
        print(f"Error sending summary email: {str(e)}")
        raise 