"""
Configuration file for ACGI Contact Export Script
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ExportConfig:
    """Configuration for the contact export script"""
    
    # ACGI Credentials
    ACGI_USERNAME = os.getenv('ACGI_USERNAME', '')
    ACGI_PASSWORD = os.getenv('ACGI_PASSWORD', '')
    ACGI_ENVIRONMENT = os.getenv('ACGI_ENVIRONMENT')  # 'test' or 'prod'
    
    # Export Settings
    START_CUSTOMER_ID = int(os.getenv('EXPORT_START_ID', '1'))
    END_CUSTOMER_ID = int(os.getenv('EXPORT_END_ID', '30000'))
    BATCH_SIZE = int(os.getenv('EXPORT_BATCH_SIZE', '1000'))
    
    # API Settings
    REQUEST_TIMEOUT = int(os.getenv('EXPORT_TIMEOUT', '60'))
    REQUEST_DELAY = float(os.getenv('EXPORT_DELAY', '0.5'))  # Delay between requests in seconds
    
    # Output Settings
    OUTPUT_DIRECTORY = os.getenv('EXPORT_OUTPUT_DIR', 'export_scripts')
    INCLUDE_TIMESTAMP = os.getenv('EXPORT_INCLUDE_TIMESTAMP', 'true').lower() == 'true'
    
    # Logging Settings
    LOG_LEVEL = os.getenv('EXPORT_LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('EXPORT_LOG_FILE', 'export_scripts/contact_export.log')
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        if not cls.ACGI_USERNAME:
            errors.append("ACGI_USERNAME is required")
        
        if not cls.ACGI_PASSWORD:
            errors.append("ACGI_PASSWORD is required")
        
        if cls.START_CUSTOMER_ID < 1:
            errors.append("EXPORT_START_ID must be >= 1")
        
        if cls.END_CUSTOMER_ID < cls.START_CUSTOMER_ID:
            errors.append("EXPORT_END_ID must be >= EXPORT_START_ID")
        
        if cls.BATCH_SIZE < 1 or cls.BATCH_SIZE > 1000:
            errors.append("EXPORT_BATCH_SIZE must be between 1 and 1000")
        
        return errors
    
    @classmethod
    def get_credentials(cls):
        """Get ACGI credentials as a dictionary"""
        return {
            'userid': cls.ACGI_USERNAME,
            'password': cls.ACGI_PASSWORD,
            'environment': cls.ACGI_ENVIRONMENT
        }
