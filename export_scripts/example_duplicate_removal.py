#!/usr/bin/env python3
"""
Example usage of the CSV duplicate removal script

This script demonstrates how to use remove_duplicates.py programmatically
and provides examples of common use cases.
"""

import os
import sys
import csv
import tempfile
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from remove_duplicates import DuplicateRemover


def create_sample_csv():
    """Create a sample CSV file with duplicates for testing"""
    sample_data = [
        {'id': '1', 'name': 'John Doe', 'email': 'john@example.com', 'department': 'IT'},
        {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com', 'department': 'HR'},
        {'id': '3', 'name': 'John Doe', 'email': 'john@example.com', 'department': 'IT'},  # Duplicate email
        {'id': '4', 'name': 'Bob Johnson', 'email': 'bob@example.com', 'department': 'Finance'},
        {'id': '5', 'name': 'Jane Smith', 'email': 'jane.smith@example.com', 'department': 'HR'},  # Different email, same name
        {'id': '6', 'name': 'Alice Brown', 'email': 'alice@example.com', 'department': 'IT'},
        {'id': '7', 'name': 'John Doe', 'email': 'john.doe@example.com', 'department': 'IT'},  # Different email, same name
        {'id': '8', 'name': 'Charlie Wilson', 'email': 'charlie@example.com', 'department': 'Finance'},
        {'id': '9', 'name': 'Alice Brown', 'email': 'alice@example.com', 'department': 'IT'},  # Duplicate email
        {'id': '10', 'name': 'David Lee', 'email': 'david@example.com', 'department': 'HR'},
    ]
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    fieldnames = ['id', 'name', 'email', 'department']
    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in sample_data:
        writer.writerow(row)
    
    temp_file.close()
    return temp_file.name


def example_remove_duplicates_by_email():
    """Example: Remove duplicates based on email column"""
    print("=" * 60)
    print("EXAMPLE 1: Remove duplicates by email")
    print("=" * 60)
    
    # Create sample data
    input_file = create_sample_csv()
    output_file = input_file.replace('.csv', '_deduplicated_by_email.csv')
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Remove duplicates
    remover = DuplicateRemover()
    success = remover.remove_duplicates(
        input_file=input_file,
        output_file=output_file,
        column='email',
        keep_first=True,
        case_sensitive=True
    )
    
    if success:
        print("✓ Duplicate removal completed successfully!")
    else:
        print("✗ Duplicate removal failed!")
    
    # Clean up
    os.unlink(input_file)
    return output_file


def example_remove_duplicates_by_name():
    """Example: Remove duplicates based on name column (case insensitive)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Remove duplicates by name (case insensitive)")
    print("=" * 60)
    
    # Create sample data
    input_file = create_sample_csv()
    output_file = input_file.replace('.csv', '_deduplicated_by_name.csv')
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Remove duplicates
    remover = DuplicateRemover()
    success = remover.remove_duplicates(
        input_file=input_file,
        output_file=output_file,
        column='name',
        keep_first=True,
        case_sensitive=False  # Case insensitive
    )
    
    if success:
        print("✓ Duplicate removal completed successfully!")
    else:
        print("✗ Duplicate removal failed!")
    
    # Clean up
    os.unlink(input_file)
    return output_file


def example_keep_last_occurrence():
    """Example: Keep last occurrence of duplicates"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Keep last occurrence of duplicates")
    print("=" * 60)
    
    # Create sample data
    input_file = create_sample_csv()
    output_file = input_file.replace('.csv', '_deduplicated_keep_last.csv')
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Remove duplicates
    remover = DuplicateRemover()
    success = remover.remove_duplicates(
        input_file=input_file,
        output_file=output_file,
        column='email',
        keep_first=False,  # Keep last occurrence
        case_sensitive=True
    )
    
    if success:
        print("✓ Duplicate removal completed successfully!")
    else:
        print("✗ Duplicate removal failed!")
    
    # Clean up
    os.unlink(input_file)
    return output_file


def display_csv_preview(file_path: str, title: str, max_rows: int = 10):
    """Display a preview of CSV file contents"""
    print(f"\n{title}")
    print("-" * len(title))
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            if not rows:
                print("File is empty")
                return
            
            # Display headers
            headers = reader.fieldnames
            print("Headers:", ", ".join(headers))
            print()
            
            # Display rows
            for i, row in enumerate(rows[:max_rows]):
                print(f"Row {i+1}: {dict(row)}")
            
            if len(rows) > max_rows:
                print(f"... and {len(rows) - max_rows} more rows")
            
            print(f"Total rows: {len(rows)}")
            
    except Exception as e:
        print(f"Error reading file: {str(e)}")


def main():
    """Main function to run all examples"""
    print("CSV Duplicate Removal Examples")
    print("=" * 60)
    print("This script demonstrates various ways to use the remove_duplicates.py script")
    print("to remove duplicates from CSV files based on different columns and criteria.")
    print()
    
    # Run examples
    output1 = example_remove_duplicates_by_email()
    output2 = example_remove_duplicates_by_name()
    output3 = example_keep_last_occurrence()
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS PREVIEW")
    print("=" * 60)
    
    display_csv_preview(output1, "Deduplicated by Email (keep first):")
    display_csv_preview(output2, "Deduplicated by Name (case insensitive):")
    display_csv_preview(output3, "Deduplicated by Email (keep last):")
    
    print("\n" + "=" * 60)
    print("COMMAND LINE USAGE EXAMPLES")
    print("=" * 60)
    print("You can also use the script from the command line:")
    print()
    print("# Remove duplicates by email column:")
    print("python remove_duplicates.py data.csv --column email")
    print()
    print("# Remove duplicates by name (case insensitive):")
    print("python remove_duplicates.py data.csv --column name --case-insensitive")
    print()
    print("# Keep last occurrence instead of first:")
    print("python remove_duplicates.py data.csv --column email --keep-last")
    print()
    print("# Create backup and modify file in place:")
    print("python remove_duplicates.py data.csv --column id --backup --in-place")
    print()
    print("# Dry run to see what would happen:")
    print("python remove_duplicates.py data.csv --column email --dry-run")
    print()
    print("# Specify custom output file:")
    print("python remove_duplicates.py data.csv --column email --output clean_data.csv")
    
    # Clean up output files
    print(f"\nCleaning up example files...")
    for file_path in [output1, output2, output3]:
        try:
            os.unlink(file_path)
            print(f"Deleted: {file_path}")
        except:
            pass


if __name__ == "__main__":
    main()
