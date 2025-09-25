#!/usr/bin/env python3
"""
ACGI Events Export Script

This script exports events from ACGI by reading customer IDs from a CSV file
and fetching event data for each customer using the EVTSSAWEBSVCLIB.GET_EVENT_INFO_XML endpoint.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from shared_utils import BaseExporter, validate_credentials, get_output_filename, logger
from config import ExportConfig

class EventsExporter(BaseExporter):
    """Export events from ACGI"""
    
    def get_customer_events(self, customer_id: str) -> Dict[str, Any]:
        """
        Get events for a specific customer
        
        Args:
            customer_id: Customer ID to fetch events for
            
        Returns:
            Dictionary containing success status and events data
        """
        try:
            result = self.acgi_client.get_customer_events(self.credentials, customer_id)
            
            if result['success']:
                events = result.get('events', {}).get('events', [])
                # Add customer ID to each event
                for event in events:
                    event['customerId'] = customer_id
                return {
                    'success': True,
                    'events': events
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'events': []
                }
                
        except Exception as e:
            logger.error(f"Error getting events for customer {customer_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
    
    def parse_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse event data for CSV export
        
        Args:
            event: Event data dictionary
            
        Returns:
            Parsed event data for CSV
        """
        return {
            'customerId': event.get('customerId', ''),
            'eventId': event.get('id', ''),
            'programName': event.get('programName', ''),
            'eventName': event.get('name', ''),
            'eventType': event.get('type', ''),
            'eventTypeDescr': event.get('typeDescr', ''),
            'status': event.get('status', ''),
            'startDate': event.get('startDt', ''),
            'endDate': event.get('endDt', ''),
            'deadlineDate': event.get('deadlineDt', ''),
            'requireSecondaryItem': event.get('requireSecondaryItem', ''),
            'locationName': event.get('locationNm', ''),
            'locationStreet1': event.get('locationStreet1', ''),
            'locationStreet2': event.get('locationStreet2', ''),
            'locationCity': event.get('locationCity', ''),
            'locationState': event.get('locationState', ''),
            'locationZip': event.get('locationZip', ''),
            'locationCountry': event.get('locationCountry', ''),
            'locationCountryDescr': event.get('locationCountryDescr', ''),
            'registerUrl': event.get('registerUrl', ''),
            'registrationStatus': event.get('registrationStatus', ''),
            'lastChangeDate': event.get('lastChangeDate', ''),
            'totalAttributes': len(event.get('attributes', [])),
            'totalRegistrationTypes': len(event.get('validRegistrationTypes', [])),
            'totalSponsors': len(event.get('sponsors', []))
        }
    
    def export_events_to_csv(self, csv_file_path: str, id_column: str = 'custId', output_file: str = None) -> str:
        """
        Export events to CSV
        
        Args:
            csv_file_path: Path to CSV file containing customer IDs
            id_column: Name of the column containing customer IDs
            output_file: Optional output file path
            
        Returns:
            Path to the created CSV file
        """
        if output_file is None:
            output_file = get_output_filename('events')
        
        self.start_time = datetime.now()
        logger.info(f"Starting events export to {output_file}")
        logger.info(f"Reading customer IDs from {csv_file_path}")
        
        # Read customer IDs from CSV
        customer_ids = self.read_customer_ids_from_csv(csv_file_path, id_column)
        
        if not customer_ids:
            logger.warning("No customer IDs found in CSV file")
            return output_file
        
        all_events = []
        
        for i, customer_id in enumerate(customer_ids, 1):
            logger.info(f"Processing customer {i}/{len(customer_ids)}: {customer_id}")
            
            # Get events for this customer
            result = self.get_customer_events(customer_id)
            
            if result['success']:
                events = result['events']
                all_events.extend(events)
                self.total_exported += len(events)
                logger.info(f"  Found {len(events)} events")
            else:
                self.total_errors += 1
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
            
            self.total_processed += 1
            
            # Add delay between requests
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Parse events for CSV
        parsed_events = [self.parse_event_data(event) for event in all_events]
        
        # Define CSV columns
        fieldnames = [
            'customerId', 'eventId', 'programName', 'eventName', 'eventType', 'eventTypeDescr',
            'status', 'startDate', 'endDate', 'deadlineDate', 'requireSecondaryItem',
            'locationName', 'locationStreet1', 'locationStreet2', 'locationCity', 'locationState',
            'locationZip', 'locationCountry', 'locationCountryDescr', 'registerUrl',
            'registrationStatus', 'lastChangeDate', 'totalAttributes', 'totalRegistrationTypes', 'totalSponsors'
        ]
        
        # Write to CSV
        self.write_to_csv(parsed_events, output_file, fieldnames)
        
        # Print summary
        self.print_summary("Events")
        
        return output_file


def main():
    """Main function to run the events export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export ACGI Events to CSV')
    parser.add_argument('csv_file', help='Path to CSV file containing customer IDs')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs (default: custId)')
    parser.add_argument('--output', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Validate credentials
    credentials = validate_credentials()
    
    # Create exporter and run export
    exporter = EventsExporter(credentials)
    
    try:
        output_file = exporter.export_events_to_csv(
            csv_file_path=args.csv_file,
            id_column=args.id_column,
            output_file=args.output
        )
        logger.info(f"Events export completed successfully: {output_file}")
    except KeyboardInterrupt:
        logger.info("Events export interrupted by user")
    except Exception as e:
        logger.error(f"Events export failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
