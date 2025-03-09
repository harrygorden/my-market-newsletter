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

    # Call server function to get all lines data
    try:
      # Fetch data from the server
      all_lines_data = anvil.server.call("get_all_lines_data")
      
      # Debug: Print what we got back from the server
      print(f"Received {len(all_lines_data)} items from server")
      
      # Set the data directly to the DataGrid
      self.data_grid_all_lines.items = all_lines_data
      
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in AllLines initialization: {str(e)}")
      notification = Notification(f"Error loading data: {str(e)}")
      notification.show()

    # Any code you write here will run before the form opens.
