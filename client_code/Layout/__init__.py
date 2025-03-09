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

    # Set initial content for content_slot (load MarketSummary form by default)
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
