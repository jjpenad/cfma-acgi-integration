#!/usr/bin/env python3
"""
CSV Duplicate Removal Script

This script removes duplicate rows from CSV files based on a specified column.
It preserves the first occurrence of each unique value in the specified column.

Usage:
    python remove_duplicates.py input_file.csv --column column_name [options]
"""

import os
import sys
import csv
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Set
from collections import OrderedDict

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('duplicate_removal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DuplicateRemover:
    """Remove duplicates from CSV files based on a specified column"""
    
    def __init__(self):
        self.total_rows = 0
        self.duplicate_rows = 0
        self.unique_rows = 0
        self.start_time = None
    
    def remove_duplicates(self, input_file: str, output_file: str, column: str, 
                         keep_first: bool = True, case_sensitive: bool = True) -> bool:
        """
        Remove duplicates from CSV file based on specified column
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            column: Column name to check for duplicates
            keep_first: If True, keep first occurrence; if False, keep last occurrence
            case_sensitive: If True, treat values case-sensitively
            
        Returns:
            True if successful, False otherwise
        """
        self.start_time = datetime.now()
        
        try:
            # Validate input file exists
            if not os.path.exists(input_file):
                logger.error(f"Input file not found: {input_file}")
                return False
            
            # Read CSV and validate column exists
            rows_data, fieldnames = self._read_csv(input_file)
            if not rows_data:
                logger.error("No data found in input file")
                return False
            
            if column not in fieldnames:
                logger.error(f"Column '{column}' not found in CSV. Available columns: {fieldnames}")
                return False
            
            logger.info(f"Processing {len(rows_data)} rows from {input_file}")
            logger.info(f"Removing duplicates based on column: {column}")
            logger.info(f"Keep {'first' if keep_first else 'last'} occurrence of duplicates")
            logger.info(f"Case sensitive: {case_sensitive}")
            
            # Remove duplicates
            unique_rows = self._remove_duplicates_from_data(
                rows_data, column, keep_first, case_sensitive
            )
            
            # Write output file
            self._write_csv(unique_rows, fieldnames, output_file)
            
            # Print summary
            self._print_summary(input_file, output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return False
    
    def _read_csv(self, file_path: str) -> tuple[List[Dict[str, Any]], List[str]]:
        """Read CSV file and return rows data and fieldnames"""
        rows_data = []
        fieldnames = []
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
                
                if not fieldnames:
                    logger.error("CSV file has no headers")
                    return [], []
                
                for row in reader:
                    rows_data.append(row)
                
                logger.info(f"Successfully read {len(rows_data)} rows from {file_path}")
                return rows_data, fieldnames
                
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            return [], []
    
    def _remove_duplicates_from_data(self, rows_data: List[Dict[str, Any]], 
                                   column: str, keep_first: bool, 
                                   case_sensitive: bool) -> List[Dict[str, Any]]:
        """Remove duplicates from rows data based on specified column"""
        seen_values: Set[str] = set()
        unique_rows = []
        
        # Use OrderedDict to maintain order while tracking duplicates
        if keep_first:
            # Process rows in order, keeping first occurrence
            for row in rows_data:
                value = str(row.get(column, '')).strip()
                
                if not case_sensitive:
                    value = value.lower()
                
                if value not in seen_values:
                    seen_values.add(value)
                    unique_rows.append(row)
                else:
                    self.duplicate_rows += 1
        else:
            # Process rows in reverse order, keeping last occurrence
            for row in reversed(rows_data):
                value = str(row.get(column, '')).strip()
                
                if not case_sensitive:
                    value = value.lower()
                
                if value not in seen_values:
                    seen_values.add(value)
                    unique_rows.insert(0, row)  # Insert at beginning to maintain order
                else:
                    self.duplicate_rows += 1
        
        self.total_rows = len(rows_data)
        self.unique_rows = len(unique_rows)
        
        logger.info(f"Found {self.duplicate_rows} duplicate rows")
        logger.info(f"Kept {self.unique_rows} unique rows")
        
        return unique_rows
    
    def _write_csv(self, rows_data: List[Dict[str, Any]], 
                  fieldnames: List[str], output_file: str):
        """Write rows data to CSV file"""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:  # Only create directory if there's a path
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in rows_data:
                    # Ensure all fieldnames are present in the row
                    complete_row = {field: row.get(field, '') for field in fieldnames}
                    writer.writerow(complete_row)
            
            logger.info(f"Successfully wrote {len(rows_data)} rows to {output_file}")
            
        except Exception as e:
            logger.error(f"Error writing CSV file: {str(e)}")
            logger.error(f"Output file path: {output_file}")
            logger.error(f"Output directory: {os.path.dirname(output_file)}")
            raise
    
    def _print_summary(self, input_file: str, output_file: str):
        """Print processing summary"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            
            logger.info("=" * 60)
            logger.info("DUPLICATE REMOVAL SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Input file: {input_file}")
            logger.info(f"Output file: {output_file}")
            logger.info(f"Total rows processed: {self.total_rows}")
            logger.info(f"Duplicate rows removed: {self.duplicate_rows}")
            logger.info(f"Unique rows kept: {self.unique_rows}")
            logger.info(f"Reduction: {(self.duplicate_rows / self.total_rows * 100):.2f}%" if self.total_rows > 0 else "N/A")
            logger.info(f"Processing time: {duration}")
            logger.info("=" * 60)


def create_backup(input_file: str) -> str:
    """Create a backup of the input file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{input_file}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(input_file, backup_file)
        logger.info(f"Backup created: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return ""


def main():
    """Main function to handle command line arguments and execute duplicate removal"""
    parser = argparse.ArgumentParser(
        description="Remove duplicates from CSV files based on a specified column",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_duplicates.py data.csv --column email
  python remove_duplicates.py data.csv --column customerId --output clean_data.csv
  python remove_duplicates.py data.csv --column name --keep-last --case-insensitive
  python remove_duplicates.py data.csv --column id --backup --in-place
        """
    )
    
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('--column', '-c', required=True, 
                       help='Column name to check for duplicates')
    parser.add_argument('--output', '-o', 
                       help='Output CSV file path (default: input_file_deduplicated.csv)')
    parser.add_argument('--keep-last', action='store_true',
                       help='Keep last occurrence instead of first (default: keep first)')
    parser.add_argument('--case-insensitive', action='store_true',
                       help='Treat values case-insensitively (default: case sensitive)')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup of original file')
    parser.add_argument('--in-place', action='store_true',
                       help='Modify the input file in place (overwrites original)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Determine output file
    if args.in_place:
        output_file = args.input_file
        if args.output:
            logger.warning("--output ignored when using --in-place")
    elif args.output:
        output_file = args.output
    else:
        # Generate default output filename
        base_name = os.path.splitext(args.input_file)[0]
        output_file = f"{base_name}_deduplicated.csv"
    
    # Validate output file path
    if not output_file or not output_file.strip():
        logger.error("Invalid output file path")
        sys.exit(1)
    
    # Convert to absolute path to avoid issues with relative paths
    output_file = os.path.abspath(output_file)
    
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            logger.error("Failed to create backup. Aborting.")
            sys.exit(1)
    
    # Dry run mode
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        logger.info(f"Would process: {args.input_file}")
        logger.info(f"Would output to: {output_file}")
        logger.info(f"Would remove duplicates based on column: {args.column}")
        logger.info(f"Would keep {'last' if args.keep_last else 'first'} occurrence")
        logger.info(f"Case sensitive: {not args.case_insensitive}")
        return
    
    # Process the file
    remover = DuplicateRemover()
    success = remover.remove_duplicates(
        input_file=args.input_file,
        output_file=output_file,
        column=args.column,
        keep_first=not args.keep_last,
        case_sensitive=not args.case_insensitive
    )
    
    if success:
        logger.info("Duplicate removal completed successfully!")
        sys.exit(0)
    else:
        logger.error("Duplicate removal failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
