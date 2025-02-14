from ._anvil_designer import TomorrowsPlanTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server


class TomorrowsPlan(TomorrowsPlanTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Call server function to get data
    data = anvil.server.call('print_data_to_form')
    
    # Update the rich text boxes with the data
    self.rich_text_summary.content = data['summary']
    self.rich_text_timing_detail.content = data['timing_detail']
    self.rich_text_upcoming_events.content = data['upcoming_events']

    # Any code you write here will run before the form opens.
