from datetime import datetime, timedelta
import anvil.tables as tables
from anvil.tables import app_tables

def get_upcoming_events(newsletter_id):
    """
    Gets upcoming market events based on the newsletter date.
    Returns formatted string of events for the remainder of the week,
    or next week if called on Friday.
    
    Args:
        newsletter_id (str): Newsletter ID in YYYYMMDD format
        
    Returns:
        str: Formatted string of upcoming events
    """
    # Convert newsletter_id to datetime
    newsletter_date = datetime.strptime(str(newsletter_id), "%Y%m%d")
    
    # Determine the date range to look up
    weekday = newsletter_date.weekday()  # Monday is 0, Sunday is 6
    
    # If it's Friday (4), get next week's events
    if weekday == 4:
        start_date = newsletter_date + timedelta(days=3)  # Start from Monday
        end_date = start_date + timedelta(days=4)  # Until Friday
    else:
        # For other days, get remaining days of current week
        start_date = newsletter_date + timedelta(days=1)  # Start from next day
        days_until_friday = 4 - weekday
        end_date = newsletter_date + timedelta(days=days_until_friday)
    
    # Format dates for query
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Query market calendar for events in date range
    # Get all events and filter in Python
    events = []
    for event in app_tables.marketcalendar.search(tables.order_by("date", "time")):
        if start_date_str <= event['date'] <= end_date_str:
            events.append(event)
    
    # Group events by date
    event_groups = {}
    for event in events:
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        if event_date not in event_groups:
            event_groups[event_date] = []
        event_groups[event_date].append({
            'time': event['time'],
            'event': event['event']
        })
    
    # Format the output
    output_parts = []
    for date in sorted(event_groups.keys()):
        # Format the date header (e.g., "Wednesday (2/12)")
        date_header = f"{date.strftime('%A')} ({date.strftime('%-m/%-d')})"
        output_parts.append(date_header + "\n")
        
        # Add each event for this date
        for event in event_groups[date]:
            output_parts.append(f"{event['time']} - {event['event']}")
        
        # Add blank line between dates
        output_parts.append("")
    
    # Join all parts with newlines and strip any extra whitespace
    return "\n".join(output_parts).strip()

def update_upcoming_events(newsletter_id):
    """
    Updates the upcoming_events field in the parsed_sections table
    for the given newsletter_id.
    
    Args:
        newsletter_id (str): Newsletter ID in YYYYMMDD format
    """
    upcoming_events = get_upcoming_events(newsletter_id)
    
    # Update the parsed_sections table
    row = app_tables.parsed_sections.get(newsletter_id=newsletter_id)
    if row:
        row['upcoming_events'] = upcoming_events 