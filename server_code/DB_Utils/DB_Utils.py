#!/usr/bin/env python3
"""
DB_Utils.py
Utility functions for database operations with Anvil
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
import anvil.server
from datetime import datetime
import json

# Global variable to track connection status
_is_connected = False

def connect_to_anvil():
    """
    Connect to the Anvil server using the uplink key from environment variables
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    global _is_connected
    
    try:
        # Get the Anvil uplink key from environment variables
        uplink_key = os.getenv('ANVIL_UPLINK_KEY')
        
        if not uplink_key:
            raise ValueError("ANVIL_UPLINK_KEY not found in environment variables")
            
        # Connect to the Anvil server
        anvil.server.connect(uplink_key)
        _is_connected = True
        print("Connected to Anvil server successfully")
        return True
        
    except Exception as e:
        _is_connected = False
        print(f"Error connecting to Anvil server: {e}")
        return False

def is_connected():
    """
    Check if connection to Anvil server is established
    
    Returns:
        bool: True if connected, False otherwise
    """
    global _is_connected
    return _is_connected

def write_dataframe_to_table(df, table_name, primary_key=None, update_if_exists=True):
    """
    Write a pandas DataFrame to an Anvil data table
    
    Args:
        df (pandas.DataFrame): The DataFrame to upload
        table_name (str): Name of the Anvil data table
        primary_key (str, optional): Column to use as primary key for updates. Defaults to None.
        update_if_exists (bool, optional): Update existing records if primary_key matches. Defaults to True.
    
    Returns:
        dict: Summary of operation results
    """
    if not is_connected():
        connect_to_anvil()
    
    try:
        # Convert DataFrame to a list of dictionaries for simpler processing
        records = df.to_dict(orient='records')
        
        # Add timestamp field to each record as an actual datetime object
        timestamp = datetime.now()
        for record in records:
            record['last_updated'] = timestamp
        
        # Use the dedicated function for vdlines
        if table_name.lower() == "vdlines":
            rows_added = anvil.server.call('add_vd_lines', records)
            return {
                'status': 'success',
                'rows_added': rows_added,
                'rows_updated': 0,
                'total_processed': rows_added
            }
        else:
            # For other tables, this would need to be extended
            raise NotImplementedError(f"Table {table_name} not supported yet")
        
    except Exception as e:
        print(f"Error writing to Anvil table '{table_name}': {e}")
        return {
            'status': 'error',
            'message': str(e),
            'rows_added': 0,
            'rows_updated': 0
        }