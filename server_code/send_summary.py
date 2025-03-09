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
            text-align: center;
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
            display: block;
            padding: 12px;
            background-color: #f1f1f1;
            border-left: 4px solid #2c3e50;
            line-height: 1.8;
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
            padding-left: 0;
            list-style-type: none;
        }
        
        .event-day {
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .event-item {
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
        
        .trading-plan {
            font-family: Arial, sans-serif;
            font-size: 14px;
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
            <div>{{ summary }}</div>
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
    # Format key levels raw as separate lines
    raw_levels = summary_data.get('key_levels_raw', 'No key levels available')
    if raw_levels != 'No key levels available':
        levels_html = ''
        for level in raw_levels.split('\n'):
            if level.strip():
                levels_html += f'{level}<br>'
        key_levels_raw_html = levels_html
    else:
        key_levels_raw_html = raw_levels
    
    # Format upcoming events as a list with days highlighted
    upcoming_events = summary_data.get('upcoming_events', 'No upcoming events available')
    if upcoming_events != 'No upcoming events available':
        events_lines = upcoming_events.strip().split('\n')
        events_html = '<ul class="events-list">'
        
        current_day = None
        for line in events_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a day header (contains day and date in parentheses)
            if '(' in line and ')' in line and any(day in line for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                if current_day:  # Add spacing between days
                    events_html += '<li style="height: 10px;"></li>'
                current_day = line
                events_html += f'<li class="event-day">{line}</li>'
            else:
                events_html += f'<li class="event-item">{line}</li>'
        
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
    
    # Format trading plan with proper styling
    summary = summary_data.get('summary', 'No summary available')
    if summary != 'No summary available':
        # Split into sections
        parts = summary.split('TRADING PLAN')
        market_summary_html = parts[0].strip()
        
        if len(parts) > 1:
            trading_plan_html = f"""
            <div class="section-subtitle">Trading Plan</div>
            <div class="trading-plan">{parts[1].strip()}</div>
            """
            full_summary_html = f"""
            <div>{market_summary_html}</div>
            {trading_plan_html}
            """
        else:
            full_summary_html = f"<div>{market_summary_html}</div>"
    else:
        full_summary_html = "<p>No summary available</p>"
    
    # Replace template variables
    html_content = EMAIL_TEMPLATE.replace('{{ summary }}', full_summary_html)\
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
    
    # Format upcoming events with proper line breaks and highlighting days
    upcoming_events = latest['upcoming_events'] if latest['upcoming_events'] else ''
    if upcoming_events:
        # Process the events to format them better by day
        import re
        
        # Find day headers (e.g., "Tuesday (3/11)")
        day_pattern = re.compile(r'([A-Za-z]+)\s*\((\d+/\d+)\)')
        
        # Reorganize events by day
        days_and_events = {}
        current_day = None
        
        for line in upcoming_events.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a day header
            day_match = day_pattern.search(line)
            if day_match:
                day_name = day_match.group(1)
                day_date = day_match.group(2)
                current_day = f"{day_name} ({day_date})"
                days_and_events[current_day] = []
            elif current_day and " - " in line:
                days_and_events[current_day].append(line)
        
        # Format the reorganized events
        formatted_events_lines = []
        for day, events in days_and_events.items():
            formatted_events_lines.append(day)
            formatted_events_lines.extend(events)
            # Add an empty line between days for spacing
            if day != list(days_and_events.keys())[-1]:  # Not the last day
                formatted_events_lines.append("")
        
        formatted_events = '\n'.join(formatted_events_lines)
    else:
        formatted_events = 'No upcoming events available'
    
    # Format the summary to remove duplicate section headers and key levels information
    summary_text = latest['summary'] if latest['summary'] else ''
    if summary_text:
        # Find the real market summary section
        import re
        
        # Remove all KEY LEVELS sections
        lines = summary_text.split('\n')
        clean_lines = []
        
        # Skip state
        skip_mode = False
        
        for line in lines:
            # If we see KEY LEVELS, start skipping
            if 'KEY LEVELS' in line:
                skip_mode = True
                continue
                
            # If we see "This week was" or "MARKET SUMMARY", we've reached the actual summary
            if line.strip().startswith('This week was') or line.strip() == 'MARKET SUMMARY':
                skip_mode = False
            
            # Skip lines with price:description pattern (likely key level details)
            if re.match(r'^\d+:', line.strip()):
                continue
                
            # Skip lines that are just digits or digits with brackets (key levels)
            if re.match(r'^\d+(\s+\[\w+\s+at\s+\d+\])?$', line.strip()):
                continue
                
            if not skip_mode:
                # Remove section header
                line = line.replace('MARKET SUMMARY', '')
                if line.strip():
                    clean_lines.append(line.strip())
        
        # Include everything from the beginning to the end, including TRADING PLAN
        summary_text = '\n'.join(clean_lines)
        summary_text = summary_text.strip()
    
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