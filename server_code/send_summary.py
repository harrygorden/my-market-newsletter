#!/usr/bin/env python3
"""
send_summary.py
Handles sending newsletter summaries and upcoming market events via email
using Gmail integration in Anvil.
"""

import anvil.google.mail
import anvil.secrets
import anvil.server
import requests
from anvil.tables import app_tables
import anvil.tables as tables


# HTML template as a string constant
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Reset styles */
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f5f5f5;
        }
        
        /* Container */
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }
        
        /* Header */
        .header {
            background-color: #2c3e50;
            color: #ffffff;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        
        /* Content sections */
        .content-section {
            padding: 20px;
            margin: 15px 0;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        
        .section-title {
            color: #2c3e50;
            font-size: 18px;
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        /* Events section */
        .events-section {
            background-color: #f8f9fa;
        }
        
        /* Footer */
        .footer {
            margin-top: 20px;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #666666;
            border-top: 1px solid #e0e0e0;
        }
        
        /* Key Levels styling */
        .key-levels {
            font-family: monospace;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }
        
        .key-levels-raw {
            font-size: 1.1em;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Market Newsletter Summary</h1>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">Market Timing</h2>
            <p>{{ timing_detail }}</p>
        </div>
        
        <div class="content-section events-section">
            <h2 class="section-title">Upcoming Market Events</h2>
            <p>{{ upcoming_events }}</p>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">Key Levels</h2>
            <div class="key-levels key-levels-raw">{{ key_levels_raw }}</div>
            <div class="key-levels">{{ key_levels }}</div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">Market Summary</h2>
            <p>{{ summary }}</p>
        </div>
        
        <div class="footer">
            <p>This is an automated summary from your Market Newsletter Aggregator</p>
        </div>
    </div>
</body>
</html>
"""


def format_email_content(summary_data):
    """
    Formats the email content using the HTML template.
    """
    # Replace template variables
    html_content = EMAIL_TEMPLATE.replace('{{ summary }}', summary_data.get('summary', 'No summary available'))\
                                .replace('{{ timing_detail }}', summary_data.get('timing_detail', 'No timing information available'))\
                                .replace('{{ upcoming_events }}', summary_data.get('upcoming_events', 'No upcoming events available'))\
                                .replace('{{ key_levels_raw }}', summary_data.get('key_levels_raw', 'No key levels available'))\
                                .replace('{{ key_levels }}', summary_data.get('key_levels', 'No key levels details available'))
    
    # Plain text version
    text_content = f"""
    Market Newsletter Summary

    Market Timing:
    {summary_data.get('timing_detail', 'No timing information available')}

    Upcoming Market Events:
    {summary_data.get('upcoming_events', 'No upcoming events available')}

    Key Levels:
    {summary_data.get('key_levels_raw', 'No key levels available')}

    Key Levels Detail:
    {summary_data.get('key_levels', 'No key levels details available')}

    Summary:
    {summary_data.get('summary', 'No summary available')}

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
    
    # Format key levels if they exist
    key_levels_raw = latest['key_levels_raw'] if latest['key_levels_raw'] else ''
    key_levels = latest['key_levels'] if latest['key_levels'] else ''
    
    # Format raw levels (numbers) on separate lines
    if key_levels_raw:
        # Process raw key levels to keep price and type together
        tokens = [num.strip() for num in key_levels_raw.split() if num.strip()]
        formatted_lines = []
        
        i = 0
        while i < len(tokens):
            # Check if the current token is a number and the next token is in parentheses
            if i + 1 < len(tokens) and tokens[i].isdigit() and tokens[i+1].startswith('(') and tokens[i+1].endswith(')'):
                # Combine price with type
                formatted_lines.append(f"{tokens[i]} {tokens[i+1]}")
                i += 2
            else:
                # Handle single tokens (likely just a price)
                formatted_lines.append(tokens[i])
                i += 1
        
        formatted_raw = '\n'.join(formatted_lines)
    else:
        formatted_raw = 'No key levels available'
    
    # Format detailed levels (lines ending with colon)
    if key_levels:
        lines = key_levels.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.endswith(':'):
                formatted_lines.append(f'\n{line}')
            else:
                formatted_lines.append(line)
        formatted_levels = ' '.join(formatted_lines)
    else:
        formatted_levels = 'No key levels details available'
    
    return {
        'summary': latest['summary'],
        'timing_detail': latest['timing_detail'],
        'upcoming_events': latest['upcoming_events'],
        'key_levels_raw': formatted_raw,
        'key_levels': formatted_levels
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