from ._anvil_designer import RowTemplate1Template
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate1(RowTemplate1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def form_refreshing_data_bindings(self, **event_args):
    """
    This method is called when the RepeatingPanel refreshes its data bindings.
    It sets the text of each label component based on the corresponding item data.
    """
    # Get the current item's data
    item = self.item
    
    # Map the item data to the label components
    if item:
      # Set the price label
      self.price_label.text = str(item.get('price', ''))
      
      # Set the major label (which comes from severity in the database)
      major_value = item.get('major', '')
      self.major_label.text = str(major_value)
      
      # If it's a major level, make it bold and a different color
      if major_value and str(major_value).lower() in ['1', 'true', 'yes', 'major']:
        self.major_label.text = "✓"
        self.major_label.foreground = '#4CAF50'  # Green color for major levels
        self.price_label.foreground = '#4CAF50'  # Make price green too for major levels
      else:
        self.major_label.text = ""
        self.major_label.foreground = None
        self.price_label.foreground = None
      
      # Set the notes label
      self.notes_label.text = str(item.get('notes', ''))
      
      # Set the vdline label
      self.vdline_label.text = str(item.get('vdline', ''))
      
      # Set the vdline_type label
      self.vdline_type_label.text = str(item.get('vdline_type', ''))