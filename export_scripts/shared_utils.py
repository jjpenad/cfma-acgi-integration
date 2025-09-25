#!/usr/bin/env python3
"""
Shared utilities for ACGI export scripts
"""

import os
import sys
import csv
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Add current directory to Python path first (for local config)
sys.path.insert(0, os.path.dirname(__file__))

# Import local config module first
from config import ExportConfig

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.acgi_client import ACGIClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = getattr(logging, ExportConfig.LOG_LEVEL.upper(), logging.INFO)

# Ensure log file directory exists
log_file_path = os.path.join(os.path.dirname(__file__), ExportConfig.LOG_FILE)
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BaseExporter:
    """Base class for all ACGI export scripts"""
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize the exporter
        
        Args:
            credentials: Dictionary containing ACGI credentials
        """
        self.credentials = credentials
        self.acgi_client = ACGIClient()
        self.base_url = "https://ams.cfma.org"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'ACGI-Export/1.0'
        })
        
        # Statistics
        self.total_processed = 0
        self.total_exported = 0
        self.total_errors = 0
        self.start_time = None
    
    def read_customer_ids_from_csv(self, csv_file_path: str, id_column: str = 'custId') -> List[str]:
        """
        Read customer IDs from a CSV file
        
        Args:
            csv_file_path: Path to the CSV file
            id_column: Name of the column containing customer IDs
            
        Returns:
            List of customer IDs
        """
        customer_ids = []
        
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                if id_column not in reader.fieldnames:
                    raise ValueError(f"Column '{id_column}' not found in CSV. Available columns: {reader.fieldnames}")
                
                for row in reader:
                    customer_id = row.get(id_column, '').strip()
                    if customer_id and customer_id.isdigit():
                        customer_ids.append(customer_id)
                
                logger.info(f"Read {len(customer_ids)} customer IDs from {csv_file_path}")
                return customer_ids
                
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    def get_element_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Safely get text from an XML element"""
        elem = parent.find(tag)
        return elem.text if elem is not None else None
    
    def write_to_csv(self, data: List[Dict[str, Any]], output_file: str, fieldnames: List[str]):
        """
        Write data to CSV file
        
        Args:
            data: List of dictionaries to write
            output_file: Output file path
            fieldnames: List of column names
        """
        if not data:
            logger.warning("No data to export")
            return
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                # Ensure all fieldnames are present in the row
                complete_row = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(complete_row)
        
        logger.info(f"Exported {len(data)} records to {output_file}")
    
    def print_summary(self, export_type: str):
        """Print export summary"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info("=" * 50)
            logger.info(f"{export_type.upper()} EXPORT SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Total customer IDs processed: {self.total_processed}")
            logger.info(f"Records exported: {self.total_exported}")
            logger.info(f"Errors encountered: {self.total_errors}")
            logger.info(f"Duration: {duration}")
            logger.info(f"Success rate: {(self.total_exported / self.total_processed * 100):.2f}%" if self.total_processed > 0 else "N/A")
            logger.info("=" * 50)


def validate_credentials() -> Dict[str, str]:
    """Validate and return ACGI credentials"""
    config_errors = ExportConfig.validate()
    if config_errors:
        logger.error("Configuration errors:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("Please check your .env file or environment variables")
        sys.exit(1)
    
    return ExportConfig.get_credentials()


def get_output_filename(export_type: str, timestamp: bool = True) -> str:
    """Generate output filename"""
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_type}_export_{timestamp_str}.csv"
    else:
        filename = f"{export_type}_export.csv"
    
    return os.path.join(ExportConfig.OUTPUT_DIRECTORY, filename)
