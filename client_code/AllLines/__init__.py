from ._anvil_designer import AllLinesTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
from datetime import datetime, timezone


class AllLines(AllLinesTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Call server function to get all lines data (you might need to create this function)
    try:
      # Here we assume you'll have a server function that returns line data for the grid
      # If you don't have one yet, you'll need to create it
      all_lines_data = anvil.server.call("get_all_lines_data")
      self.repeating_panel_1.items = all_lines_data
    except Exception as e:
      # Handle any errors loading the data
      notification = Notification(f"Error loading data: {str(e)}")
      notification.show()

    # Any code you write here will run before the form opens.
