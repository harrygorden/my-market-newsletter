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
    
    # Ensure the navigation panel is visible and properly initialized
    # This is crucial for the hamburger menu to appear correctly
    self.column_panel_1.visible = True
    
    # Add custom CSS to ensure the hamburger menu is always visible
    # Note: This accesses the Anvil JS runtime to add styles directly to the page
    anvil.js.call('eval', '''
      (function() {
        // Add a style to make hamburger menu more visible if needed
        var style = document.createElement('style');
        style.textContent = `
          .sidebar-toggle {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
          }
        `;
        document.head.appendChild(style);
        
        // Force the sidebar to be properly initialized on page load
        setTimeout(function() {
          var sidebarElements = document.querySelectorAll('.sidebar');
          if (sidebarElements.length > 0) {
            // Make sure the page layout knows there's a sidebar
            document.body.classList.add('has-sidebar');
          }
        }, 100);
      })();
    ''')
    
    # Set initial content for content_slot (load MarketSummary form by default)
    self.content_panel.add_component(MarketSummary(), slot='content_slot')

    # Any code you write here will run before the form opens.
    
  def outlined_button_link_marketsummary_click(self, **event_args):
    """This method is called when the Market Summary button is clicked"""
    # Clear the current content by removing all components from the panel
    self.content_panel.clear()
    # Add the MarketSummary form
    self.content_panel.add_component(MarketSummary(), slot='content_slot')

  def outlined_button_alllines_click(self, **event_args):
    """This method is called when the All Lines button is clicked"""
    # Clear the current content by removing all components from the panel
    self.content_panel.clear()
    # Add the AllLines form
    self.content_panel.add_component(AllLines(), slot='content_slot')
