import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from . import db_access
import re
import spacy
from datetime import datetime, timedelta
import pytz

"""
email_parser.py

This module handles the cleaning and parsing of newsletter emails. The cleaning process
follows these specific steps:

1. Initial Setup:
   - Adds "Market Summary" section at the beginning of the document
   - Removes email client headers (e.g., "View this email in browser")

2. Footer Removal:
   - Identifies and removes footer content by looking for markers like:
     * "Unsubscribe"
     * "Manage your subscription"
     * "You received this email"
   - Keeps only content before the first footer marker

3. Text Cleanup:
   - Standardizes line breaks (max 2 consecutive newlines)
   - Removes excessive whitespace and tabs
   - Removes decorative markers (sequences of *, -, =)
   - Standardizes paragraph spacing

4. Section Marking:
   - Wraps the following sections with <SECTION> tags:
     * Market Summary (added at start)
     * Market Commentary:
     * Key Signals:
     * Trading Plan:
     * Core Structures/Levels To Engage
     * In summary for tomorrow:
     * Trade Recap/Education
     * Important Housekeeping Notices
     * Closing (added before final two lines)
   
   - Special handling for "Trade Plan {Weekday}" headers:
     * Matches exact pattern "Trade Plan" followed by a weekday
     * Preserves the weekday in the section tag
     * Adds proper spacing around the section

5. Final Formatting:
   - Ensures consistent newline spacing between sections
   - Strips any trailing whitespace
   - Maintains proper paragraph structure throughout

The module also includes functionality to parse the cleaned text into structured data
for storage in Anvil Data Tables.
"""

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

def clean_newsletter(raw_body: str) -> str:
    """
    Cleans the raw newsletter text.
    
    Args:
        raw_body (str): The raw text content of the newsletter
        
    Returns:
        str: The cleaned newsletter text
        
    Cleaning steps:
        - Removes header content (e.g., "View this email in browser")
        - Removes footer content (e.g., unsubscribe links)
        - Removes decorative markers and excessive whitespace
        - Standardizes paragraph spacing
        - Wraps section headers in semantic markers
    """
    if not raw_body:
        return ""
    
    print(f"Original text length: {len(raw_body)}")
    print(f"First 100 chars of original: {raw_body[:100]}")
        
    # Remove header lines (common email client additions)
    cleaned = re.sub(r'^.*?View (this|the) (email|post) (in|on).*?\n', '', raw_body, 
                    flags=re.IGNORECASE | re.MULTILINE)
    print(f"After header removal length: {len(cleaned)}")
    
    # Add Market Summary at the beginning with SECTION tags
    cleaned = "\n\n<SECTION>Market Summary</SECTION>\n\n" + cleaned.lstrip()
    print("Added Market Summary header with section tags")
    
    # Add Closing section at the beginning too
    cleaned = cleaned + "\n\n<SECTION>Closing</SECTION>\n\n"
    print("Added Closing section with section tags")
    
    # Find the position of the first footer marker
    footer_markers = ['Unsubscribe', 'Manage your subscription', 'You received this email']
    footer_pos = len(cleaned)
    for marker in footer_markers:
        pos = cleaned.lower().find(marker.lower())
        if pos != -1 and pos < footer_pos:
            footer_pos = pos
    
    # Only keep content before the footer
    if footer_pos < len(cleaned):
        cleaned = cleaned[:footer_pos].strip()
    print(f"After footer removal length: {len(cleaned)}")
    print(f"Content after footer removal (first 100 chars): {cleaned[:100]}")
    
    # Remove excessive line breaks and whitespace, but preserve paragraph structure
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    print(f"After whitespace cleanup length: {len(cleaned)}")
    
    # Remove decorative markers, but be more specific
    cleaned = re.sub(r'[=\-*]{3,}[\n\s]*', '\n\n', cleaned)
    print(f"After marker removal length: {len(cleaned)}")
    
    # Split into paragraphs and rejoin with standardized spacing
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', cleaned) if p.strip()]
    cleaned = '\n\n'.join(paragraphs)
    print(f"After paragraph standardization length: {len(cleaned)}")
    
    # Mark section headers for better parsing
    section_headers = [
        'Market Commentary:',
        'Key Signals:',
        'Trading Plan:',
        'Core Structures/Levels To Engage',
        'In summary for tomorrow:',
        'Trade Recap/Education',
        'Important Housekeeping Notices'
    ]
    
    for header in section_headers:
        # First remove any excess newlines around the header
        cleaned = re.sub(
            f'\n{{2,}}{re.escape(header)}\n{{2,}}',
            f'\n\n{header}\n\n',
            cleaned
        )
        # Then wrap in section tags with exactly two newlines before and after
        cleaned = re.sub(
            f'([^\n])\n{{0,2}}{re.escape(header)}',
            r'\1\n\n<SECTION>' + header,
            cleaned
        )
        cleaned = re.sub(
            f'{re.escape(header)}\n{{0,2}}([^\n])',
            header + r'</SECTION>\n\n\1',
            cleaned
        )
        cleaned = re.sub(
            f'{re.escape(header)}$',
            header + r'</SECTION>\n\n',
            cleaned
        )
    
    # Handle Trade Plan sections with the same spacing
    weekdays = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday)'
    trade_plan_pattern = r'^\s*Trade\s+Plan\s+(' + weekdays + r')\s*$'
    
    # Debug print to see what we're looking for
    print("Looking for Trade Plan pattern:", trade_plan_pattern)
    
    # Find all matches first to debug
    matches = re.finditer(trade_plan_pattern, cleaned, flags=re.MULTILINE)
    for match in matches:
        print(f"Found Trade Plan match: '{match.group(0)}' at position {match.start()}")
    
    # Apply the substitution with exactly two newlines
    cleaned = re.sub(
        trade_plan_pattern,
        r'\n\n<SECTION>Trade Plan \1</SECTION>\n\n',
        cleaned,
        flags=re.MULTILINE
    )
    
    # Final cleanup of any remaining multiple newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Debug print to check if any Trade Plan lines remain unwrapped
    for line in cleaned.split('\n'):
        if 'Trade Plan' in line and '<SECTION>' not in line:
            print(f"WARNING: Unwrapped Trade Plan line found: '{line}'")
    
    final_text = cleaned.strip()
    print(f"Final cleaned text length: {len(final_text)}")
    print(f"Final text preview: {final_text[:200]}")
    
    return final_text

def find_nearby_vdlines(level, max_distance=3):
    """
    Find any vdlines that are within the specified distance of the given level
    
    Args:
        level (float): The price level to check
        max_distance (int): Maximum distance to consider a match (default: 3)
        
    Returns:
        str: Type of the matching vdline or None if no match found
    """
    try:
        # Convert level to float for numeric comparison
        level_float = float(level)
        
        # Query all vdlines from the app table
        all_vdlines = app_tables.vdlines.search()
        
        # Check each vdline to see if it's within the specified distance
        for vdline in all_vdlines:
            vdline_price = float(vdline['Price'])
            if abs(vdline_price - level_float) <= max_distance:
                return vdline['Type']
        
        return None
    except Exception as e:
        print(f"Error finding nearby vdlines: {e}")
        return None

def parse_email(raw_body: str) -> dict:
    parsed = {}

    # Extract Market Summary section
    market_summary_match = re.search(r'<SECTION>Market Summary</SECTION>\s*(.*?)(?=<SECTION>|$)', raw_body, re.DOTALL)
    parsed["MarketSummary"] = market_summary_match.group(1).strip() if market_summary_match else ""

    # Extract Core Structures/Levels section and process numbers
    levels_match = re.search(r'<SECTION>Core Structures/Levels To Engage</SECTION>\s*(.*?)(?=<SECTION>|$)', raw_body, re.DOTALL)
    if levels_match:
        levels_text = levels_match.group(1)
        # Extract lines starting with numbers followed by colon
        key_levels = []
        key_levels_raw = []
        for line in levels_text.split('\n'):
            if match := re.match(r'(\d+(?:\.\d+)?)\s*:', line):
                key_levels.append(line.strip())
                key_levels_raw.append(float(match.group(1)))  # Convert to float for proper numeric sorting
        # Sort key_levels_raw in descending order and convert back to strings
        key_levels_raw.sort(reverse=True)
        parsed["KeyLevels"] = '\n'.join(key_levels)
        
        # Format KeyLevelsRaw with nearby vdline information
        formatted_key_levels_raw = []
        for num in key_levels_raw:
            # Convert to int if the float has no decimal places, otherwise keep the float
            level_str = str(int(num)) if num.is_integer() else str(num)
            
            # Check if this level is near any vdline
            vdline_type = find_nearby_vdlines(num)
            if vdline_type:
                level_str = f"{level_str} ({vdline_type})"
                
            formatted_key_levels_raw.append(level_str)
            
        parsed["KeyLevelsRaw"] = '\n'.join(formatted_key_levels_raw)
    else:
        parsed["KeyLevels"] = ""
        parsed["KeyLevelsRaw"] = ""

    # Extract Trading Plan section
    trading_plan_match = re.search(r'<SECTION>Trade Plan \w+</SECTION>\s*(.*?)(?=<SECTION>|$)', raw_body, re.DOTALL)
    parsed["TradingPlan"] = trading_plan_match.group(1).strip() if trading_plan_match else ""

    # Extract Plan Summary (single line after "In summary for tomorrow:")
    summary_match = re.search(r'<SECTION>In summary for tomorrow:</SECTION>\s*([^\n]+)', raw_body)
    summary_text = summary_match.group(1).strip() if summary_match else ""
    parsed["PlanSummary"] = summary_text

    # Create combined summary with all sections
    summary_parts = []
    
    # Key Levels Raw
    summary_parts.append("KEY LEVELS RAW")
    summary_parts.append(parsed["KeyLevelsRaw"])
    
    # Key Levels
    summary_parts.append("\nKEY LEVELS DETAIL")
    summary_parts.append(parsed["KeyLevels"])
    
    # Market Summary
    summary_parts.append("\nMARKET SUMMARY")
    summary_parts.append(parsed["MarketSummary"])
    
    # Trading Plan
    summary_parts.append("\nTRADING PLAN")
    summary_parts.append(parsed["TradingPlan"])
    
    # Plan Summary
    summary_parts.append("\nPLAN SUMMARY")
    summary_parts.append(parsed["PlanSummary"])
    
    # Join all parts with a newline
    parsed["summary"] = '\n\n'.join(part for part in summary_parts if part)

    # Generate timing detail
    utc_now = datetime.now(pytz.UTC)
    central = pytz.timezone('America/Chicago')
    now = utc_now.astimezone(central)
    
    current_date = now.strftime("%A, %B %d, %Y")
    current_time = now.strftime("%H:%M")
    
    # Calculate next business day (keeping timezone awareness)
    next_day = now + timedelta(days=1)
    if next_day.weekday() >= 5:  # Saturday or Sunday
        days_to_add = 7 - next_day.weekday() + 1  # Days until Monday
        next_day = now + timedelta(days=days_to_add)
    
    next_date = next_day.strftime("%A, %B %d, %Y")
    
    timing_detail = (f"This summary was generated at {current_time} CST on {current_date}, "
                    f"in preparation for the trading session on {next_date}.")
    
    parsed["timing_detail"] = timing_detail

    return parsed 