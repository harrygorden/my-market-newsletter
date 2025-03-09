from ._anvil_designer import LayoutTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
from datetime import datetime, timezone
# Import the forms for the content slot
from ..MarketSummary import MarketSummary
from ..AllLines import AllLines


class Layout(LayoutTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Call server function to get data
    data = anvil.server.call('print_data_to_form')
    
    # Update the rich text boxes with the data
    self.rich_text_summary.content = data['summary']
    self.rich_text_timing_detail.content = data['timing_detail']
    self.rich_text_upcoming_events.content = data['upcoming_events']

    # Update label text based on day/time
    current_time = datetime.now(timezone.utc)
    current_weekday = current_time.weekday()  # Monday is 0, Sunday is 6
    current_hour = current_time.hour

    # Check if it's between Friday 23:00 UTC and Monday 23:00 UTC
    if (current_weekday == 4 and current_hour >= 23) or \
       current_weekday in [5, 6] or \
       (current_weekday == 0 and current_hour < 23):
        self.label_market_events.text = "Next Week's Events"
    else:
        self.label_market_events.text = "This Week's Remaining Events"

    # Set initial content for content_slot (optional)
    self.content_panel.add_component(MarketSummary(), slot='content_slot')

    # Any code you write here will run before the form opens.
    
  def outlined_button_link_marketsummary_click(self, **event_args):
    """This method is called when the Market Summary button is clicked"""
    # Clear the current content in the slot and add the MarketSummary form
    self.content_panel.clear_slot('content_slot')
    self.content_panel.add_component(MarketSummary(), slot='content_slot')

  def outlined_button_alllines_click(self, **event_args):
    """This method is called when the All Lines button is clicked"""
    # Clear the current content in the slot and add the AllLines form
    self.content_panel.clear_slot('content_slot')
    self.content_panel.add_component(AllLines(), slot='content_slot')
