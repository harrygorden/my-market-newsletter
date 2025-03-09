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
      
      # Fetch data directly from the server
      print("Calling server to get data...")
      all_lines_data = anvil.server.call("get_all_lines_data")
      
      # Debug: Print what we got back from the server
      print(f"Received {len(all_lines_data)} items from server")
      if len(all_lines_data) > 0:
        print(f"Sample data: {all_lines_data[0]}")
        
        # Set the data directly to the DataGrid
        self.data_grid_all_lines.items = all_lines_data
        notification = Notification(f"Loaded {len(all_lines_data)} key levels", timeout=3)
        notification.show()
      else:
        # Show notification if no data
        notification = Notification(f"No data found in keylevelsraw table. Row count from debug: {debug_info.get('row_count', 0)}", timeout=5)
        notification.show()
        self.data_grid_all_lines.items = []
        
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in AllLines.refresh_data: {str(e)}")
      notification = Notification(f"Error loading data: {str(e)}", timeout=5)
      notification.show()
      
  def force_refresh_data(self):
    """Force a complete refresh of data directly from the server"""
    try:
      # Show a loading notification
      notification = Notification("Forcing data refresh...", timeout=3)
      notification.show()
      
      # Call the force refresh function on the server
      print("Calling force_refresh_all_lines...")
      all_lines_data = anvil.server.call("force_refresh_all_lines")
      
      # Debug: Print what we got back from the server
      print(f"Force refresh returned {len(all_lines_data)} items")
      if len(all_lines_data) > 0:
        print(f"First item: {all_lines_data[0]}")
        
        # Set the data directly to the DataGrid
        self.data_grid_all_lines.items = all_lines_data
        notification = Notification(f"Loaded {len(all_lines_data)} key levels from force refresh", timeout=3)
        notification.show()
      else:
        # Show notification if no data
        notification = Notification("No data found in keylevelsraw table after force refresh.", timeout=5)
        notification.show()
        self.data_grid_all_lines.items = []
        
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in force_refresh_data: {str(e)}")
      notification = Notification(f"Error during force refresh: {str(e)}", timeout=5)
      notification.show()
  
  def refresh_button_click(self, **event_args):
    """Called when the Refresh Data button is clicked"""
    # Clear any existing data
    self.data_grid_all_lines.items = []
    
    # Force a refresh from the server
    self.refresh_data()
    
  def force_refresh_button_click(self, **event_args):
    """Called when the Force Refresh button is clicked"""
    # Clear any existing data
    self.data_grid_all_lines.items = []
    
    # Call the force refresh method
    self.force_refresh_data()
    
  def debug_keylevelsraw(self):
    """Run a debug check on the keylevelsraw table"""
    try:
      # Show a loading notification
      notification = Notification("Running debug check...", timeout=2)
      notification.show()
      
      # Call the debug function
      debug_info = anvil.server.call("debug_keylevelsraw_table")
      
      # Print the debug info to the console
      print("=== DEBUG INFO FOR KEYLEVELSRAW TABLE ===")
      print(f"Row count: {debug_info.get('row_count', 0)}")
      print(f"Column names: {debug_info.get('column_names', [])}")
      
      # Display sample rows if available
      sample_rows = debug_info.get('sample_rows', [])
      if sample_rows:
        print("Sample rows:")
        for i, row in enumerate(sample_rows):
          print(f"Row {i+1}: {row}")
      
      # Check if there are any warnings
      warnings = debug_info.get('field_mapping_warnings', [])
      if warnings:
        print("Field mapping warnings:")
        for warning in warnings:
          print(f" - {warning}")
          
      # Display a notification with the row count
      notification = Notification(f"Debug complete. Found {debug_info.get('row_count', 0)} rows in keylevelsraw table.", timeout=5)
      notification.show()
      
      return debug_info
      
    except Exception as e:
      # Handle any errors
      print(f"Error debugging keylevelsraw table: {str(e)}")
      notification = Notification(f"Error debugging table: {str(e)}", timeout=5)
      notification.show()

  def debug_button_click(self, **event_args):
    """Called when the Debug Table button is clicked"""
    # Run the debug method
    self.debug_keylevelsraw()
