#!/usr/bin/env python3
"""
ACGI Event Registrations Export Script

This script exports event registrations from ACGI by reading customer IDs from a CSV file
and fetching event registration data for each customer using the EVTSSAWEBSVCLIB.GET_EVENTREG_INFO_XML endpoint.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from shared_utils import BaseExporter, validate_credentials, get_output_filename, logger
from config import ExportConfig

class EventRegistrationsExporter(BaseExporter):
    """Export event registrations and events from ACGI"""
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.events_cache = {}  # Cache to store unique events by ID
    
    def get_customer_event_registrations(self, customer_id: str) -> Dict[str, Any]:
        """
        Get event registrations for a specific customer
        
        Args:
            customer_id: Customer ID to fetch event registrations for
            
        Returns:
            Dictionary containing success status and registrations data
        """
        try:
            result = self.acgi_client.get_customer_registrations_to_events(self.credentials, customer_id)
            
            if result['success']:
                registrations = result.get('registrations', {}).get('registrations', [])
                # Add customer ID to each registration
                for registration in registrations:
                    registration['customerId'] = customer_id
                return {
                    'success': True,
                    'registrations': registrations
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'registrations': []
                }
                
        except Exception as e:
            logger.error(f"Error getting event registrations for customer {customer_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'registrations': []
            }
    
    def get_customer_events(self, customer_id: str) -> Dict[str, Any]:
        """
        Get events for a specific customer and cache them
        
        Args:
            customer_id: Customer ID to fetch events for
            
        Returns:
            Dictionary containing success status and events data
        """
        try:
            result = self.acgi_client.get_customer_events(self.credentials, customer_id)
            
            if result['success']:
                events = result.get('events', {}).get('events', [])
                # Cache events by ID to avoid duplicates
                for event in events:
                    event_id = event.get('id')
                    if event_id and event_id not in self.events_cache:
                        event['customerId'] = customer_id
                        self.events_cache[event_id] = event
                
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
    
    def parse_registration_data(self, registration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse event registration data for CSV export
        
        Args:
            registration: Event registration data dictionary
            
        Returns:
            Parsed registration data for CSV
        """
        return {
            'customerId': registration.get('customerId', ''),
            'registrationSerno': registration.get('regiSerno', ''),
            'eventId': registration.get('eventId', ''),
            'eventStatus': registration.get('eventStatus', ''),
            'registrationDate': registration.get('registrationDate', ''),
            'registrationType': registration.get('registrationType', ''),
            'registrationName': registration.get('registrationName', ''),
            'representing': registration.get('representing', ''),
            'billtoId': registration.get('billtoId', ''),
            'promoCode': registration.get('promoCd', ''),
            'purchaseOrder': registration.get('purchaseOrder', ''),
            'primaryItemId': registration.get('primItemId', ''),
            'primaryRegStatus': registration.get('primRegStatus', ''),
            'totalCharges': registration.get('totalCharges', ''),
            'totalPayment': registration.get('totalPayment', ''),
            'balance': registration.get('balance', ''),
            'eventName': registration.get('eventName', ''),
            'programName': registration.get('programName', ''),
            'primaryItemDescription': registration.get('primaryItemDescr', ''),
            'eventStartDate': registration.get('eventStartDt', ''),
            'eventEndDate': registration.get('eventEndDt', ''),
            'locationName': registration.get('locationName', ''),
            'locationStreet1': registration.get('locationStreet1', ''),
            'locationStreet2': registration.get('locationStreet2', ''),
            'locationCity': registration.get('locationCity', ''),
            'locationState': registration.get('locationState', ''),
            'locationZip': registration.get('locationZip', ''),
            'locationCountry': registration.get('locationCountry', ''),
            'locationCountryDescr': registration.get('locationCountryDescr', ''),
            'firstName': registration.get('firstName', ''),
            'lastName': registration.get('lastName', ''),
            'companyName': registration.get('companyName', ''),
            'email': registration.get('email', ''),
            'registrationStreet1': registration.get('evtRegStreet1', ''),
            'registrationStreet2': registration.get('evtRegStreet2', ''),
            'registrationStreet3': registration.get('evtRegStreet3', ''),
            'registrationCity': registration.get('evtRegCity', ''),
            'registrationState': registration.get('evtRegState', ''),
            'registrationZip': registration.get('evtRegZip', ''),
            'registrationCountry': registration.get('evtRegCountry', ''),
            'totalItems': len(registration.get('items', [])),
            'totalGuests': len(registration.get('guests', []))
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
    
    def export_event_registrations_to_csv(self, csv_file_path: str, id_column: str = 'custId', output_file: str = None) -> str:
        """
        Export event registrations and events to CSV
        
        Args:
            csv_file_path: Path to CSV file containing customer IDs
            id_column: Name of the column containing customer IDs
            output_file: Optional output file path for registrations
            
        Returns:
            Path to the created registrations CSV file
        """
        if output_file is None:
            output_file = get_output_filename('event_registrations')
        
        # Generate events output file name
        events_output_file = output_file.replace('event_registrations', 'events')
        
        self.start_time = datetime.now()
        logger.info(f"Starting event registrations and events export")
        logger.info(f"Registrations will be saved to: {output_file}")
        logger.info(f"Events will be saved to: {events_output_file}")
        logger.info(f"Reading customer IDs from {csv_file_path}")
        
        # Read customer IDs from CSV
        customer_ids = self.read_customer_ids_from_csv(csv_file_path, id_column)
        
        if not customer_ids:
            logger.warning("No customer IDs found in CSV file")
            return output_file
        
        batch_count = 0
        
        for i, customer_id in enumerate(customer_ids, 1):
            logger.info(f"Processing customer {i}/{len(customer_ids)}: {customer_id}")
            
            # Get event registrations for this customer
            reg_result = self.get_customer_event_registrations(customer_id)
            
            if reg_result['success']:
                registrations = reg_result['registrations']
                self.total_exported += len(registrations)
                logger.info(f"  Found {len(registrations)} event registrations")
                
                # Write registrations batch to CSV immediately
                if registrations:
                    parsed_registrations = [self.parse_registration_data(registration) for registration in registrations]
                    registration_fieldnames = [
                        'customerId', 'registrationSerno', 'eventId', 'eventStatus', 'registrationDate',
                        'registrationType', 'registrationName', 'representing', 'billtoId', 'promoCode',
                        'purchaseOrder', 'primaryItemId', 'primaryRegStatus', 'totalCharges', 'totalPayment',
                        'balance', 'eventName', 'programName', 'primaryItemDescription', 'eventStartDate',
                        'eventEndDate', 'locationName', 'locationStreet1', 'locationStreet2', 'locationCity',
                        'locationState', 'locationZip', 'locationCountry', 'locationCountryDescr',
                        'firstName', 'lastName', 'companyName', 'email', 'registrationStreet1',
                        'registrationStreet2', 'registrationStreet3', 'registrationCity', 'registrationState',
                        'registrationZip', 'registrationCountry', 'totalItems', 'totalGuests'
                    ]
                    self.write_batch_to_csv(parsed_registrations, output_file, registration_fieldnames, is_first_batch=(batch_count == 0))
            else:
                self.total_errors += 1
                logger.error(f"  Registration error: {reg_result.get('error', 'Unknown error')}")
            
            # Get events for this customer (will be cached to avoid duplicates)
            events_result = self.get_customer_events(customer_id)
            
            if events_result['success']:
                events = events_result['events']
                logger.info(f"  Found {len(events)} events (cached to avoid duplicates)")
            else:
                logger.error(f"  Events error: {events_result.get('error', 'Unknown error')}")
            
            self.total_processed += 1
            batch_count += 1
            
            # Add delay between requests
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Write cached events to CSV (all unique events)
        if self.events_cache:
            parsed_events = [self.parse_event_data(event) for event in self.events_cache.values()]
            event_fieldnames = [
                'eventId', 'programName', 'eventName', 'eventType', 'eventTypeDescr',
                'status', 'startDate', 'endDate', 'deadlineDate', 'requireSecondaryItem',
                'locationName', 'locationStreet1', 'locationStreet2', 'locationCity', 'locationState',
                'locationZip', 'locationCountry', 'locationCountryDescr', 'registerUrl',
                'registrationStatus', 'lastChangeDate', 'totalAttributes', 'totalRegistrationTypes', 'totalSponsors'
            ]
            self.write_to_csv(parsed_events, events_output_file, event_fieldnames)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("EXPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total customer IDs processed: {self.total_processed}")
        logger.info(f"Event registrations exported: {len(parsed_registrations)}")
        logger.info(f"Unique events exported: {len(parsed_events)}")
        logger.info(f"Errors encountered: {self.total_errors}")
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info(f"Duration: {duration}")
        logger.info(f"Registrations file: {output_file}")
        logger.info(f"Events file: {events_output_file}")
        logger.info("=" * 60)
        
        return output_file


def main():
    """Main function to run the event registrations and events export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export ACGI Event Registrations and Events to CSV')
    parser.add_argument('csv_file', help='Path to CSV file containing customer IDs')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs (default: custId)')
    parser.add_argument('--output', help='Output CSV file path for registrations (events will be saved to a separate file)')
    
    args = parser.parse_args()
    
    # Validate credentials
    credentials = validate_credentials()
    
    # Create exporter and run export
    exporter = EventRegistrationsExporter(credentials)
    
    try:
        output_file = exporter.export_event_registrations_to_csv(
            csv_file_path=args.csv_file,
            id_column=args.id_column,
            output_file=args.output
        )
        logger.info(f"Event registrations and events export completed successfully!")
        logger.info(f"Registrations file: {output_file}")
        events_file = output_file.replace('event_registrations', 'events')
        logger.info(f"Events file: {events_file}")
    except KeyboardInterrupt:
        logger.info("Event registrations and events export interrupted by user")
    except Exception as e:
        logger.error(f"Event registrations and events export failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
