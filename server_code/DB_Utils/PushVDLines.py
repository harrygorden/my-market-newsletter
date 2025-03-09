#!/usr/bin/env python3
"""
PushVDLines.py
Script to upload VDLines data from CSV to Anvil app tables
"""

import os
import sys
import csv
import pandas as pd
from dotenv import load_dotenv
import anvil.server

# Import utility functions
from DB_Utils import connect_to_anvil, write_dataframe_to_table

def main():
    # Setup working directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Connect to Anvil server
    connect_to_anvil()
    
    # Path to the CSV file
    csv_file = "ES1VoodooLines.csv"
    
    try:
        # Read CSV file into pandas DataFrame
        print(f"Reading data from {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Display data summary
        print(f"Loaded {len(df)} records from CSV.")
        print(f"Columns found: {', '.join(df.columns)}")
        
        # Upload data to Anvil table
        print("Uploading data to Anvil 'VDLines' table...")
        result = write_dataframe_to_table(df, "vdlines")
        
        print(f"Upload complete. {result['rows_added']} rows added, {result['rows_updated']} rows updated.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()