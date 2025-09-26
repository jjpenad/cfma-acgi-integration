#!/usr/bin/env python3
"""
ACGI Memberships Export Script

This script exports memberships from ACGI by reading customer IDs from a CSV file
and fetching membership data for each customer using the MEMSSAWEBSVCLIB.GET_MEMBERS_XML endpoint.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from shared_utils import BaseExporter, validate_credentials, get_output_filename, logger
from config import ExportConfig

class MembershipsExporter(BaseExporter):
    """Export memberships from ACGI"""
    
    def get_customer_memberships(self, customer_id: str) -> Dict[str, Any]:
        """
        Get memberships for a specific customer
        
        Args:
            customer_id: Customer ID to fetch memberships for
            
        Returns:
            Dictionary containing success status and memberships data
        """
        try:
            result = self.acgi_client.get_memberships_data(self.credentials, customer_id)
            
            if result['success']:
                memberships = result.get('memberships', {}).get('memberships', [])
                # Add customer ID to each membership
                for membership in memberships:
                    membership['customerId'] = customer_id
                return {
                    'success': True,
                    'memberships': memberships
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'memberships': []
                }
                
        except Exception as e:
            logger.error(f"Error getting memberships for customer {customer_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'memberships': []
            }
    
    def parse_membership_data(self, membership: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse membership data for CSV export
        
        Args:
            membership: Membership data dictionary
            
        Returns:
            Parsed membership data for CSV
        """
        return {
            'customerId': membership.get('customerId', ''),
            'subgroupId': membership.get('subgroupId', ''),
            'subgroupName': membership.get('subgroupName', ''),
            'classCode': membership.get('classCd', ''),
            'subclassCode': membership.get('subclassCd', ''),
            'status': membership.get('status', ''),
            'isActive': membership.get('isActive', False),
            'joinDate': membership.get('joinDate', ''),
            'expireDate': membership.get('expireDate', ''),
            'currentStatusReasonCode': membership.get('currentStatusReasonCd', ''),
            'currentStatusReasonNote': membership.get('currentStatusReasonNote', ''),
            'reinstateDate': membership.get('reinstateDate', ''),
            'terminateDate': membership.get('terminateDate', '')
        }
    
    def export_memberships_to_csv(self, csv_file_path: str, id_column: str = 'custId', output_file: str = None) -> str:
        """
        Export memberships to CSV
        
        Args:
            csv_file_path: Path to CSV file containing customer IDs
            id_column: Name of the column containing customer IDs
            output_file: Optional output file path
            
        Returns:
            Path to the created CSV file
        """
        if output_file is None:
            output_file = get_output_filename('memberships')
        
        self.start_time = datetime.now()
        logger.info(f"Starting memberships export to {output_file}")
        logger.info(f"Reading customer IDs from {csv_file_path}")
        
        # Read customer IDs from CSV
        customer_ids = self.read_customer_ids_from_csv(csv_file_path, id_column)
        
        if not customer_ids:
            logger.warning("No customer IDs found in CSV file")
            return output_file
        
        batch_count = 0
        
        for i, customer_id in enumerate(customer_ids, 1):
            logger.info(f"Processing customer {i}/{len(customer_ids)}: {customer_id}")
            
            # Get memberships for this customer
            result = self.get_customer_memberships(customer_id)
            
            if result['success']:
                memberships = result['memberships']
                self.total_exported += len(memberships)
                logger.info(f"  Found {len(memberships)} memberships")
                
                # Write memberships batch to CSV immediately
                if memberships:
                    parsed_memberships = [self.parse_membership_data(membership) for membership in memberships]
                    fieldnames = [
                        'customerId', 'subgroupId', 'subgroupName', 'classCode', 'subclassCode',
                        'status', 'isActive', 'joinDate', 'expireDate', 'currentStatusReasonCode',
                        'currentStatusReasonNote', 'reinstateDate', 'terminateDate'
                    ]
                    self.write_batch_to_csv(parsed_memberships, output_file, fieldnames, is_first_batch=(batch_count == 0))
                    batch_count += 1
            else:
                self.total_errors += 1
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
            
            self.total_processed += 1
            
            # Add delay between requests
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Print summary
        self.print_summary("Memberships")
        
        return output_file


def main():
    """Main function to run the memberships export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export ACGI Memberships to CSV')
    parser.add_argument('csv_file', help='Path to CSV file containing customer IDs')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs (default: custId)')
    parser.add_argument('--output', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Validate credentials
    credentials = validate_credentials()
    
    # Create exporter and run export
    exporter = MembershipsExporter(credentials)
    
    try:
        output_file = exporter.export_memberships_to_csv(
            csv_file_path=args.csv_file,
            id_column=args.id_column,
            output_file=args.output
        )
        logger.info(f"Memberships export completed successfully: {output_file}")
    except KeyboardInterrupt:
        logger.info("Memberships export interrupted by user")
    except Exception as e:
        logger.error(f"Memberships export failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
