# ACGI Export Scripts

This directory contains scripts for exporting various types of data from ACGI to CSV format. All scripts can read customer IDs from a CSV file (typically from the contacts export) and fetch related data.

## Available Export Scripts

### 1. Contact Export (`export_contacts.py`)
Exports customer contact information with email addresses.

**Usage:**
```bash
python export_contacts.py
```

**Output:** `contacts_export_YYYYMMDD_HHMMSS.csv`

### 2. Events Export (`export_events.py`)
Exports events for customers from the contacts CSV.

**Usage:**
```bash
python export_events.py contacts_export_20240115_103000.csv
python export_events.py contacts_export_20240115_103000.csv --id-column custId --output events.csv
```

**Output:** `events_export_YYYYMMDD_HHMMSS.csv`

### 3. Event Registrations Export (`export_event_registrations.py`)
Exports event registrations for customers from the contacts CSV.

**Usage:**
```bash
python export_event_registrations.py contacts_export_20240115_103000.csv
python export_event_registrations.py contacts_export_20240115_103000.csv --id-column custId --output event_registrations.csv
```

**Output:** `event_registrations_export_YYYYMMDD_HHMMSS.csv`

### 4. Memberships Export (`export_memberships.py`)
Exports memberships for customers from the contacts CSV.

**Usage:**
```bash
python export_memberships.py contacts_export_20240115_103000.csv
python export_memberships.py contacts_export_20240115_103000.csv --id-column custId --output memberships.csv
```

**Output:** `memberships_export_YYYYMMDD_HHMMSS.csv`

### 5. Purchased Products Export (`export_purchased_products.py`)
Exports purchased products/orders for customers from the contacts CSV.

**Usage:**
```bash
python export_purchased_products.py contacts_export_20240115_103000.csv
python export_purchased_products.py contacts_export_20240115_103000.csv --id-column custId --output purchased_products.csv
```

**Output:** `purchased_products_export_YYYYMMDD_HHMMSS.csv`

### 6. Master Export Script (`export_all.py`)
Runs all exports in sequence.

**Usage:**
```bash
# Export everything (contacts first, then all related data)
python export_all.py

# Use existing contacts CSV
python export_all.py --contacts-csv contacts_export_20240115_103000.csv

# Skip certain exports
python export_all.py --skip-events --skip-memberships

# Custom output directory
python export_all.py --output-dir /path/to/output
```

## Common Arguments

All export scripts (except contacts) accept these arguments:

- `csv_file`: Path to CSV file containing customer IDs
- `--id-column`: Name of the column containing customer IDs (default: `custId`)
- `--output`: Output CSV file path (optional)

## CSV Column Mappings

### Contacts Export
- **Basic Info**: `custId`, `custType`, `loginId`
- **Name Fields**: `prefixName`, `firstName`, `middleName`, `lastName`, etc.
- **Email Info**: `Email` (preferred), `Additional_Emails` (others)
- **Contact Info**: `primary_phone`, `primary_address_*`, `primary_job_*`

### Events Export
- **Event Info**: `eventId`, `eventName`, `programName`, `eventType`
- **Dates**: `startDate`, `endDate`, `deadlineDate`
- **Location**: `locationName`, `locationCity`, `locationState`, etc.
- **Registration**: `registerUrl`, `registrationStatus`

### Event Registrations Export
- **Registration Info**: `registrationSerno`, `registrationType`, `registrationName`
- **Financial**: `totalCharges`, `totalPayment`, `balance`
- **Event Details**: `eventName`, `programName`, `eventStartDate`, `eventEndDate`
- **Contact**: `firstName`, `lastName`, `email`, `companyName`

### Memberships Export
- **Membership Info**: `subgroupId`, `subgroupName`, `classCode`, `status`
- **Dates**: `joinDate`, `expireDate`, `reinstateDate`, `terminateDate`
- **Status**: `isActive`, `currentStatusReasonCode`, `currentStatusReasonNote`

### Purchased Products Export
- **Product Info**: `productId`, `productName`, `productType`
- **Physical**: `length`, `width`, `height`, `weight`
- **Order Info**: `orderDate`, `orderStatus`, `orderSerno`, `quantity`
- **Financial**: `defaultUnitCost`, `invoiceBalance`, `priceProfile`

## Workflow Examples

### Complete Export Workflow
```bash
# 1. Setup credentials (first time only)
python setup_env.py

# 2. Export everything
python export_all.py

# This will create:
# - contacts_export_YYYYMMDD_HHMMSS.csv
# - events_export_YYYYMMDD_HHMMSS.csv
# - event_registrations_export_YYYYMMDD_HHMMSS.csv
# - memberships_export_YYYYMMDD_HHMMSS.csv
# - purchased_products_export_YYYYMMDD_HHMMSS.csv
```

### Selective Export Workflow
```bash
# 1. Export contacts first
python export_contacts.py

# 2. Export specific data types
python export_events.py contacts_export_20240115_103000.csv
python export_memberships.py contacts_export_20240115_103000.csv
```

### Custom Customer List
```bash
# Create a custom CSV with specific customer IDs
echo "custId" > custom_customers.csv
echo "12345" >> custom_customers.csv
echo "67890" >> custom_customers.csv

# Export data for these specific customers
python export_events.py custom_customers.csv
python export_memberships.py custom_customers.csv
```

## Configuration

All scripts use the same configuration from `.env` file:

```bash
# Required
ACGI_USERNAME=your_username
ACGI_PASSWORD=your_password
ACGI_ENVIRONMENT=test

# Optional
EXPORT_START_ID=1
EXPORT_END_ID=30000
EXPORT_BATCH_SIZE=100
EXPORT_TIMEOUT=60
EXPORT_DELAY=0.5
EXPORT_OUTPUT_DIR=export_scripts
EXPORT_LOG_LEVEL=INFO
```

## Error Handling

- **API Errors**: All scripts handle HTTP errors and timeouts gracefully
- **Data Validation**: Invalid customer records are skipped with logging
- **File Errors**: Missing CSV files or invalid columns are reported clearly
- **Progress Tracking**: Real-time progress updates and summary statistics

## Performance

- **Batch Processing**: All scripts process customers one at a time with configurable delays
- **Memory Efficient**: Data is processed in streams to avoid memory issues
- **Progress Logging**: Detailed logging for monitoring and debugging
- **Resumable**: Failed exports can be resumed by running the script again

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration Errors**: Check your `.env` file
   ```bash
   python test_config.py
   ```

3. **CSV File Errors**: Verify the CSV file exists and has the correct column
   ```bash
   python -c "import csv; print(list(csv.DictReader(open('your_file.csv')))[0].keys())"
   ```

4. **API Errors**: Check your ACGI credentials and network connection

### Logs

Check the log file for detailed error information:
```bash
tail -f export_scripts/contact_export.log
```

## Support

For issues or questions:
1. Check the logs for error details
2. Verify your configuration settings
3. Test with a small subset of customer IDs first
4. Ensure your ACGI credentials are valid and have proper permissions
