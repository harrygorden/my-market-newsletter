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
      
      # Fetch data directly from the server
      print("Calling server to get keylevels data...")
      rows = anvil.server.call("get_keylevels")
      
      # Debug: Print what we got back from the server
      row_count = len(rows)
      print(f"Received {row_count} rows from server")
      
      if row_count > 0:
        # Print sample of first row for debugging
        first_row = rows[0]
        print(f"Sample data (first row):")
        print(f"  Column names: {list(first_row)}")
        for key, value in first_row.items():
          print(f"  {key}: {value}")
        
        # Map the database fields to what the UI expects
        # This handles the mapping from database field names to UI field names
        # (as noted in the memory about field mappings)
        items = []
        for row in rows:
          item = {
            # Use price_with_range if available, fall back to price if not
            "price": row.get("price_with_range") or row.get("price", ""),
            # Map severity to major
            "major": row.get("severity", ""),
            # Map note to notes
            "notes": row.get("note", ""),
            "vdline": row.get("vdline", ""),
            "vdline_type": row.get("vdline_type", "")
          }
          items.append(item)
        
        # Set the mapped items to the repeating panel
        self.repeating_panel_1.items = items
        print(f"Set {len(items)} items to repeating_panel_1")
        
        notification = Notification(f"Loaded {len(items)} key levels", timeout=3)
        notification.show()
      else:
        # Show notification if no data
        notification = Notification(f"No data found in keylevelsraw table. Row count: {row_count}", timeout=5)
        notification.show()
        # Clear the repeating panel
        self.repeating_panel_1.items = []
        
    except Exception as e:
      # Handle any errors loading the data
      print(f"Error in AllLines.refresh_data: {str(e)}")
      notification = Notification(f"Error loading data: {str(e)}", timeout=5)
      notification.show()
  
  def refresh_button_click(self, **event_args):
    """Called when the Refresh Data button is clicked"""
    # Clear any existing data
    self.repeating_panel_1.items = []
    
    # Force a refresh from the server
    self.refresh_data()
    
  def force_refresh_button_click(self, **event_args):
    """Called when the Force Refresh button is clicked"""
    # Clear any existing data
    self.repeating_panel_1.items = []
    
    # Call the refresh method - it will get fresh data from the server
    self.refresh_data()
    
  def debug_keylevelsraw(self):
    """Run a debug check on the keylevelsraw table"""
    try:
      # Show a loading notification
      notification = Notification("Running debug check...", timeout=2)
      notification.show()
      
      # Get the rows directly from the server
      rows = anvil.server.call("get_keylevels")
      row_count = len(rows)
      
      # Print debug info
      print("=== DEBUG INFO FOR keylevelsraw TABLE ===")
      print(f"Row count: {row_count}")
      
      if row_count > 0:
        # Get column names from first row
        first_row = rows[0]
        column_names = list(first_row)
        print(f"Column names: {column_names}")
        
        # Display sample rows
        print("Sample rows:")
        for i, row in enumerate(rows[:3]):  # Show first 3 rows
          print(f"Row {i+1}:")
          for col in column_names:
            print(f"  {col}: {row[col]}")
      else:
        print("No rows found in keylevelsraw table")
      
      # Display a notification with the row count
      notification = Notification(f"Debug complete. Found {row_count} rows in keylevelsraw table.", timeout=5)
      notification.show()
      
    except Exception as e:
      # Handle any errors
      print(f"Error debugging keylevelsraw table: {str(e)}")
      notification = Notification(f"Error debugging table: {str(e)}", timeout=5)
      notification.show()

  def debug_button_click(self, **event_args):
    """Called when the Debug Table button is clicked"""
    # Run the debug method
    self.debug_keylevelsraw()
