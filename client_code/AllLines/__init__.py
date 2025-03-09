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

    # Refresh data when the form loads
    self.refresh_data()

  def refresh_data(self):
    """Refresh data from the server and populate the DataGrid"""
    try:
      # Fetch data from the server
      all_lines_data = anvil.server.call("get_all_lines_data")
      
      # Debug: Print what we got back from the server
      print(f"Received {len(all_lines_data)} items from server")
      if len(all_lines_data) > 0:
        print(f"Sample data: {all_lines_data[0]}")
      
      # Direct assignment to the DataGrid (bypassing the repeating panel)
      self.data_grid_all_lines.items = all_lines_data
      
      # Show notification if no data
      if len(all_lines_data) == 0:
        notification = Notification("No data found in the keylevelsraw table")
        notification.show()
        
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in AllLines.refresh_data: {str(e)}")
      notification = Notification(f"Error loading data: {str(e)}")
      notification.show()
