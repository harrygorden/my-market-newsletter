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
            margin-top: 10px;
        }
        
        .key-levels-raw {
            font-size: 1.1em;
            font-weight: bold;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 12px;
            background-color: #f1f1f1;
            border-left: 4px solid #2c3e50;
        }
        
        .key-levels-raw .level {
            margin-right: 10px;
            white-space: nowrap;
        }
        
        .key-levels-detail {
            margin-top: 15px;
            padding: 12px;
            border-left: 4px solid #4e6d8c;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        
        .events-list {
            margin: 0;
            padding-left: 15px;
        }
        
        .events-list li {
            margin-bottom: 5px;
        }
        
        .section-subtitle {
            font-weight: bold;
            color: #4e6d8c;
            margin-top: 15px;
            margin-bottom: 5px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 3px;
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
            <div>{{ upcoming_events }}</div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">Key Levels</h2>
            <div class="section-subtitle">Key Prices</div>
            <div class="key-levels-raw">{{ key_levels_raw }}</div>
            <div class="section-subtitle">Key Levels Detail</div>
            <div class="key-levels-detail">{{ key_levels }}</div>
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
    # Format key levels raw as HTML spans
    raw_levels = summary_data.get('key_levels_raw', 'No key levels available')
    if raw_levels != 'No key levels available':
        levels_html = ''
        for level in raw_levels.split('\n'):
            if level.strip():
                levels_html += f'<span class="level">{level}</span>'
        key_levels_raw_html = levels_html
    else:
        key_levels_raw_html = raw_levels
    
    # Format upcoming events as a list
    upcoming_events = summary_data.get('upcoming_events', 'No upcoming events available')
    if upcoming_events != 'No upcoming events available':
        events_lines = upcoming_events.strip().split('\n')
        events_html = '<ul class="events-list">'
        for line in events_lines:
            if line.strip():
                events_html += f'<li>{line.strip()}</li>'
        events_html += '</ul>'
    else:
        events_html = '<p>No upcoming events available</p>'
    
    # Format key levels details with better spacing
    key_levels_detail = summary_data.get('key_levels', 'No key levels details available')
    if key_levels_detail != 'No key levels details available':
        # Process each line to add proper spacing and formatting
        lines = key_levels_detail.split('\n')
        formatted_details = []
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('KEY LEVELS DETAIL'):
                level_parts = line.split(':', 1)
                if len(level_parts) == 2:
                    formatted_details.append(f'<strong>{level_parts[0].strip()}:</strong> {level_parts[1].strip()}')
            elif line and not line.startswith('KEY LEVELS DETAIL') and not line.startswith('KEY LEVELS RAW'):
                formatted_details.append(line)
        
        key_levels_detail_html = '<p>' + '</p><p>'.join(formatted_details) + '</p>'
    else:
        key_levels_detail_html = '<p>No key levels details available</p>'
    
    # Replace template variables
    html_content = EMAIL_TEMPLATE.replace('{{ summary }}', summary_data.get('summary', 'No summary available'))\
                                .replace('{{ timing_detail }}', summary_data.get('timing_detail', 'No timing information available'))\
                                .replace('{{ upcoming_events }}', events_html)\
                                .replace('{{ key_levels_raw }}', key_levels_raw_html)\
                                .replace('{{ key_levels }}', key_levels_detail_html)
    
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

    Market Summary:
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
        # Process raw key levels to keep price and vdline info together
        formatted_lines = []
        
        # Split by whitespace but preserve bracketed text together
        import re
        tokens = []
        current_raw = key_levels_raw
        
        # Extract prices with their associated vdline info
        bracket_pattern = re.compile(r'(\d+)(\s+\[\w+\s+at\s+\d+\])?')
        matches = bracket_pattern.findall(current_raw)
        
        for price, vdline_info in matches:
            if vdline_info:
                formatted_lines.append(f"{price}{vdline_info}")
            else:
                formatted_lines.append(price)
        
        formatted_raw = '\n'.join(formatted_lines)
    else:
        formatted_raw = 'No key levels available'
    
    # Format detailed levels
    if key_levels:
        # Remove the section headers from the content
        content = key_levels.replace('KEY LEVELS DETAIL', '').replace('KEY LEVELS RAW', '')
        
        # Clean up consecutive newlines and whitespace
        import re
        content = re.sub(r'\n+', '\n', content.strip())
        
        # Split by new lines, preserving price:description format
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
        
        formatted_levels = '\n'.join(formatted_lines)
    else:
        formatted_levels = 'No key levels details available'
    
    # Format upcoming events with proper line breaks
    upcoming_events = latest['upcoming_events'] if latest['upcoming_events'] else ''
    if upcoming_events:
        # Split events by day
        import re
        # Find day headers and format them
        events_list = []
        for line in upcoming_events.split('\n'):
            line = line.strip()
            if line:
                events_list.append(line)
        
        formatted_events = '\n'.join(events_list)
    else:
        formatted_events = 'No upcoming events available'
    
    # Format the summary to remove duplicate section headers
    summary_text = latest['summary'] if latest['summary'] else ''
    if summary_text:
        # Remove section headers that will already be in our email template
        summary_text = summary_text.replace('MARKET SUMMARY', '')
        
        # Remove any lines that start with KEY LEVELS as we'll handle those separately
        lines = summary_text.split('\n')
        cleaned_lines = []
        for line in lines:
            if not line.strip().startswith('KEY LEVELS'):
                cleaned_lines.append(line)
        
        summary_text = '\n'.join(cleaned_lines).strip()
    
    return {
        'summary': summary_text,
        'timing_detail': latest['timing_detail'],
        'upcoming_events': formatted_events,
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