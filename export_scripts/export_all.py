#!/usr/bin/env python3
"""
ACGI Master Export Script

This script runs all ACGI exports in sequence:
1. Export contacts (if contacts CSV doesn't exist)
2. Export events
3. Export event registrations
4. Export memberships
5. Export purchased products

All exports use the customer IDs from the contacts export.
"""

import os
import sys
import argparse
from datetime import datetime
from shared_utils import validate_credentials, logger

def run_export_script(script_name: str, csv_file: str, id_column: str = 'custId', output_file: str = None):
    """Run an export script"""
    import subprocess
    
    cmd = [sys.executable, script_name, csv_file, '--id-column', id_column]
    if output_file:
        cmd.extend(['--output', output_file])
    
    logger.info(f"Running {script_name}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✅ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {script_name} failed: {e.stderr}")
        return False

def main():
    """Main function to run all exports"""
    parser = argparse.ArgumentParser(description='Run all ACGI exports')
    parser.add_argument('--contacts-csv', help='Path to existing contacts CSV file (if not provided, will export contacts first)')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs (default: custId)')
    parser.add_argument('--skip-contacts', action='store_true', help='Skip contacts export (requires --contacts-csv)')
    parser.add_argument('--skip-events', action='store_true', help='Skip events export')
    parser.add_argument('--skip-event-registrations', action='store_true', help='Skip event registrations export')
    parser.add_argument('--skip-memberships', action='store_true', help='Skip memberships export')
    parser.add_argument('--skip-purchased-products', action='store_true', help='Skip purchased products export')
    parser.add_argument('--output-dir', help='Output directory for all exports')
    
    args = parser.parse_args()
    
    # Validate credentials
    credentials = validate_credentials()
    
    # Determine contacts CSV file
    if args.contacts_csv:
        contacts_csv = args.contacts_csv
        if not os.path.exists(contacts_csv):
            logger.error(f"Contacts CSV file not found: {contacts_csv}")
            sys.exit(1)
    else:
        if args.skip_contacts:
            logger.error("Cannot skip contacts export without providing --contacts-csv")
            sys.exit(1)
        
        # Export contacts first
        logger.info("No contacts CSV provided, exporting contacts first...")
        contacts_csv = f"export_scripts/contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        success = run_export_script('export_contacts.py', 'dummy', args.id_column, contacts_csv)
        if not success:
            logger.error("Contacts export failed, cannot continue")
            sys.exit(1)
    
    logger.info(f"Using contacts CSV: {contacts_csv}")
    
    # Set output directory
    output_dir = args.output_dir or 'export_scripts'
    
    # Run exports
    exports = [
        ('export_events.py', 'events', args.skip_events),
        ('export_event_registrations.py', 'event_registrations', args.skip_event_registrations),
        ('export_memberships.py', 'memberships', args.skip_memberships),
        ('export_purchased_products.py', 'purchased_products', args.skip_purchased_products)
    ]
    
    successful_exports = []
    failed_exports = []
    
    for script_name, export_type, skip in exports:
        if skip:
            logger.info(f"⏭️  Skipping {export_type} export")
            continue
        
        output_file = os.path.join(output_dir, f"{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        success = run_export_script(script_name, contacts_csv, args.id_column, output_file)
        if success:
            successful_exports.append(export_type)
        else:
            failed_exports.append(export_type)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Contacts CSV: {contacts_csv}")
    logger.info(f"Successful exports: {', '.join(successful_exports) if successful_exports else 'None'}")
    logger.info(f"Failed exports: {', '.join(failed_exports) if failed_exports else 'None'}")
    logger.info("=" * 60)
    
    if failed_exports:
        sys.exit(1)

if __name__ == "__main__":
    main()
