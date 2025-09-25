# ACGI Contact Export Scripts

This directory contains scripts for exporting contact data from ACGI to various formats.

## Contact Export Script

The `export_contacts.py` script exports contacts from ACGI by querying customer IDs from 1 to 30000 in batches of 100 using the `CENSSAWEBSVCLIB.GET_CUST_INFO_XML` endpoint with bulk request enabled.

### Features

- **Batch Processing**: Processes customer IDs in batches of 100 for efficient API usage
- **Email Filtering**: Only exports contacts that have valid email addresses
- **Comprehensive Data**: Exports name, contact info, addresses, phones, and job information
- **CSV Output**: Exports data to CSV format with organized columns
- **Error Handling**: Robust error handling and logging
- **Progress Tracking**: Real-time progress updates and summary statistics

### Prerequisites

1. Python 3.7 or higher
2. Required packages (install with `pip install -r requirements.txt`)
3. Valid ACGI credentials

### Configuration

The script reads configuration from a `.env` file. You can create this file manually or use the setup script.

#### Quick Setup

Run the setup script to create your `.env` file:

```bash
cd export_scripts
python setup_env.py
```

This will prompt you for your ACGI credentials and create a `.env` file with all the necessary settings.

#### Manual Configuration

Create a `.env` file in the `export_scripts` directory:

```bash
# Required ACGI Credentials
ACGI_USERNAME=your_username
ACGI_PASSWORD=your_password
ACGI_ENVIRONMENT=test

# Optional Export Settings
EXPORT_START_ID=1
EXPORT_END_ID=30000
EXPORT_BATCH_SIZE=100
EXPORT_TIMEOUT=60
EXPORT_DELAY=0.5

# Optional Output Settings
EXPORT_OUTPUT_DIR=export_scripts
EXPORT_INCLUDE_TIMESTAMP=true

# Optional Logging Settings
EXPORT_LOG_LEVEL=INFO
EXPORT_LOG_FILE=export_scripts/contact_export.log
```

#### Environment Variables (Alternative)

You can also set environment variables instead of using a `.env` file:

```bash
# Required
export ACGI_USERNAME="your_username"
export ACGI_PASSWORD="your_password"
export ACGI_ENVIRONMENT="test"  # or "prod"

# Optional
export EXPORT_START_ID="1"
export EXPORT_END_ID="30000"
export EXPORT_BATCH_SIZE="100"
export EXPORT_TIMEOUT="60"
export EXPORT_DELAY="0.5"
export EXPORT_OUTPUT_DIR="export_scripts"
export EXPORT_LOG_LEVEL="INFO"
```

### Usage

#### Basic Usage

1. **Setup your credentials** (first time only):
   ```bash
   cd export_scripts
   python setup_env.py
   ```

2. **Run the export**:
   ```bash
   python export_contacts.py
   ```

#### Custom Range

Edit your `.env` file to change the range:
```bash
EXPORT_START_ID=1
EXPORT_END_ID=1000
```

Then run:
```bash
python export_contacts.py
```

#### With Environment Variables (Alternative)

You can override `.env` settings with environment variables:
```bash
export EXPORT_START_ID="1"
export EXPORT_END_ID="1000"
python export_contacts.py
```

### Output

The script generates:

1. **CSV File**: `contacts_export_YYYYMMDD_HHMMSS.csv` containing all contacts with emails
2. **Log File**: `contact_export.log` with detailed execution logs
3. **Console Output**: Real-time progress updates and summary statistics

### CSV Columns

The exported CSV includes the following columns:

- **Basic Info**: `custId`, `custType`, `loginId`
- **Name Fields**: `prefixName`, `firstName`, `middleName`, `lastName`, `suffixName`, `degreeName`, `informalName`, `displayName`
- **Email Info**: `Email` (preferred email), `Additional_Emails` (all other emails separated by semicolon)
- **Phone Info**: `primary_phone`, `primary_phone_type`, `primary_phone_number`
- **Address Info**: `primary_address_street1`, `primary_address_street2`, `primary_address_city`, `primary_address_state`, `primary_address_postalCode`, `primary_address_country`
- **Job Info**: `primary_job_employer`, `primary_job_title`
- **Counts**: `total_emails`, `total_phones`, `total_addresses`, `total_jobs`

### API Details

The script uses the ACGI `CENSSAWEBSVCLIB.GET_CUST_INFO_XML` endpoint with the following configuration:

- **Bulk Request**: `bulkRequest=true` for efficient batch processing
- **Comprehensive Details**: Includes roles, addresses, phones, emails, jobs, bio, aliases, etc.
- **Email Validation**: Only processes contacts with valid, non-bad email addresses

### Error Handling

The script includes comprehensive error handling:

- **API Errors**: Handles HTTP errors and timeouts
- **XML Parsing**: Gracefully handles malformed XML responses
- **Data Validation**: Skips invalid customer records
- **Logging**: Detailed logging for debugging and monitoring

### Performance

- **Batch Size**: 100 customer IDs per request (configurable)
- **Request Delay**: 0.5 seconds between requests (configurable)
- **Timeout**: 60 seconds per request (configurable)
- **Memory Efficient**: Processes data in batches to avoid memory issues

### Troubleshooting

#### Common Issues

1. **Authentication Errors**: Verify ACGI credentials are correct
2. **Timeout Errors**: Increase `EXPORT_TIMEOUT` value
3. **Rate Limiting**: Increase `EXPORT_DELAY` value
4. **Memory Issues**: Reduce `EXPORT_BATCH_SIZE`

#### Logs

Check the log file for detailed error information:

```bash
tail -f export_scripts/contact_export.log
```

### Example Output

```
2024-01-15 10:30:00 - INFO - Starting contact export to export_scripts/contacts_export_20240115_103000.csv
2024-01-15 10:30:00 - INFO - Processing customer IDs 1-30000 in batches of 100
2024-01-15 10:30:01 - INFO - Processing batch: 1-100
2024-01-15 10:30:02 - INFO - Batch 1-100: Found 45 customers with emails
...
2024-01-15 10:45:00 - INFO - ==================================================
2024-01-15 10:45:00 - INFO - EXPORT SUMMARY
2024-01-15 10:45:00 - INFO - ==================================================
2024-01-15 10:45:00 - INFO - Total customer IDs processed: 30000
2024-01-15 10:45:00 - INFO - Customers with emails exported: 12500
2024-01-15 10:45:00 - INFO - Errors encountered: 0
2024-01-15 10:45:00 - INFO - Duration: 0:15:00
2024-01-15 10:45:00 - INFO - Success rate: 41.67%
2024-01-15 10:45:00 - INFO - ==================================================
```

### CSV Sample

The exported CSV will have columns like:

| custId | firstName | lastName | Email | Additional_Emails | primary_phone | ... |
|--------|-----------|----------|-------|-------------------|---------------|-----|
| 12345 | John | Doe | john.doe@company.com | john.doe.personal@gmail.com; j.doe@oldcompany.com | (555) 123-4567 | ... |
| 12346 | Jane | Smith | jane.smith@company.com | | (555) 987-6543 | ... |

### Support

For issues or questions regarding the export scripts, please check the logs and configuration settings first. The script includes detailed error messages to help diagnose problems.
