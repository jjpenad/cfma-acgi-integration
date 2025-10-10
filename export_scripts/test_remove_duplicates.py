#!/usr/bin/env python3
"""
Test script for remove_duplicates.py

This script creates a test CSV file with duplicates and tests the duplicate removal functionality.
"""

import os
import sys
import csv
import tempfile
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from remove_duplicates import DuplicateRemover


def create_test_csv():
    """Create a test CSV file with duplicates"""
    test_data = [
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
    
    # Create temporary file in current directory for easier debugging
    test_file = 'test_data.csv'
    
    fieldnames = ['id', 'name', 'email', 'department']
    with open(test_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in test_data:
            writer.writerow(row)
    
    print(f"Created test file: {test_file}")
    print(f"File location: {os.path.abspath(test_file)}")
    return test_file


def test_duplicate_removal():
    """Test the duplicate removal functionality"""
    print("=" * 60)
    print("TESTING DUPLICATE REMOVAL SCRIPT")
    print("=" * 60)
    
    # Create test data
    input_file = create_test_csv()
    output_file = 'test_data_deduplicated.csv'
    
    print(f"\nInput file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Working directory: {os.getcwd()}")
    
    # Test duplicate removal by email
    print("\nTesting duplicate removal by email...")
    remover = DuplicateRemover()
    
    try:
        success = remover.remove_duplicates(
            input_file=input_file,
            output_file=output_file,
            column='email',
            keep_first=True,
            case_sensitive=True
        )
        
        if success:
            print("✓ Duplicate removal completed successfully!")
            
            # Verify results
            with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                print(f"✓ Output file contains {len(rows)} rows")
                
                # Check for duplicates
                emails = [row['email'] for row in rows]
                unique_emails = set(emails)
                if len(emails) == len(unique_emails):
                    print("✓ No duplicate emails found in output")
                else:
                    print(f"✗ Found duplicate emails: {len(emails) - len(unique_emails)} duplicates")
                
        else:
            print("✗ Duplicate removal failed!")
            
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        try:
            if os.path.exists(input_file):
                os.unlink(input_file)
                print(f"Cleaned up: {input_file}")
            if os.path.exists(output_file):
                os.unlink(output_file)
                print(f"Cleaned up: {output_file}")
        except Exception as e:
            print(f"Warning: Could not clean up test files: {str(e)}")


def test_command_line_interface():
    """Test the command line interface"""
    print("\n" + "=" * 60)
    print("TESTING COMMAND LINE INTERFACE")
    print("=" * 60)
    
    # Create test data
    input_file = create_test_csv()
    output_file = 'test_cli_output.csv'
    
    print(f"\nTesting command line interface...")
    print(f"Command: python remove_duplicates.py {input_file} --column email --output {output_file}")
    
    # Test dry run
    print("\nTesting dry run...")
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, 'remove_duplicates.py', 
            input_file, '--column', 'email', '--output', output_file, '--dry-run'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✓ Dry run completed successfully")
            print("Dry run output:")
            print(result.stdout)
        else:
            print(f"✗ Dry run failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            
    except Exception as e:
        print(f"✗ Error running command line test: {str(e)}")
    
    finally:
        # Clean up test files
        try:
            if os.path.exists(input_file):
                os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
        except Exception as e:
            print(f"Warning: Could not clean up test files: {str(e)}")


def main():
    """Main test function"""
    print("CSV Duplicate Removal Script Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    
    # Test programmatic usage
    test_duplicate_removal()
    
    # Test command line interface
    test_command_line_interface()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
