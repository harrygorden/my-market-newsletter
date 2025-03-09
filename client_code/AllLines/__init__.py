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
      # Show a loading notification
      notification = Notification("Loading data...", timeout=3)
      notification.show()
      
      # First run the debug function to see what's in the database
      debug_info = anvil.server.call("debug_keylevelsraw_table")
      print(f"Debug info: {debug_info}")
      
      # Launch a background task to fetch data with enhanced logging
      print("Launching background task to refresh data...")
      self.bg_task = anvil.server.call_s("refresh_all_lines_data_bg")
      print(f"Background task started with ID: {self.bg_task}")
      
      # Show status notification
      notification = Notification("Background refresh task launched. Check logs for details.", timeout=3)
      notification.show()
      
      # Set up a timer to check on the task
      self.timer = Timer(interval=1, repeat=True, callback=self.check_refresh_task)
      self.timer.start()
      
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in AllLines.refresh_data: {str(e)}")
      notification = Notification(f"Error launching refresh task: {str(e)}", timeout=5)
      notification.show()
  
  def check_refresh_task(self, **event_args):
    """Check if the background refresh task has completed"""
    try:
      # Check if the task has completed
      if anvil.server.task_is_completed(self.bg_task):
        # Get the result
        result = anvil.server.get_task_result(self.bg_task)
        
        # Stop the timer
        self.timer.stop()
        
        # Check if we got an error
        if isinstance(result, dict) and 'error' in result:
          print(f"Background task returned an error: {result['error']}")
          notification = Notification(f"Error refreshing data: {result['error']}", timeout=5)
          notification.show()
          return
        
        # Debug: Print what we got back from the server
        print(f"Background task completed. Received {len(result)} items from server")
        if len(result) > 0:
          print(f"Sample data: {result[0]}")
          
          # Set the data directly to the DataGrid
          self.data_grid_all_lines.items = result
          notification = Notification(f"Loaded {len(result)} key levels", timeout=3)
          notification.show()
        else:
          # Show notification if no data
          notification = Notification("No data found in keylevelsraw table.", timeout=5)
          notification.show()
          self.data_grid_all_lines.items = []
    except Exception as e:
      # Handle any errors
      print(f"Error checking background task: {str(e)}")
      self.timer.stop()
      notification = Notification(f"Error checking refresh task: {str(e)}", timeout=5)
      notification.show()
      
  def refresh_button_click(self, **event_args):
    """Called when the Refresh Data button is clicked"""
    # Clear any existing data
    self.data_grid_all_lines.items = []
    
    # Force a refresh from the server
    self.refresh_data()
