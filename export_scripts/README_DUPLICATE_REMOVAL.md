# CSV Duplicate Removal Script

This script removes duplicate rows from CSV files based on a specified column. It's designed to work with the ACGI export scripts and follows the same patterns and logging conventions.

## Features

- **Column-based duplicate detection**: Remove duplicates based on any column in your CSV
- **Flexible duplicate handling**: Choose to keep first or last occurrence
- **Case sensitivity options**: Handle case-sensitive or case-insensitive comparisons
- **Backup creation**: Automatically create backups before modifying files
- **In-place editing**: Modify files directly or create new output files
- **Dry run mode**: Preview changes without modifying files
- **Comprehensive logging**: Detailed logs with statistics and processing information
- **Error handling**: Robust error handling with informative messages

## Installation

The script requires Python 3.6+ and uses only standard library modules:

- `csv` - For CSV file handling
- `argparse` - For command-line argument parsing
- `logging` - For logging functionality
- `datetime` - For timestamps and duration tracking

No additional dependencies are required.

## Usage

### Command Line Interface

```bash
python remove_duplicates.py input_file.csv --column column_name [options]
```

### Basic Examples

```bash
# Remove duplicates based on email column
python remove_duplicates.py contacts.csv --column email

# Remove duplicates based on customer ID
python remove_duplicates.py customers.csv --column customerId

# Remove duplicates based on name (case insensitive)
python remove_duplicates.py contacts.csv --column name --case-insensitive

# Keep last occurrence instead of first
python remove_duplicates.py data.csv --column email --keep-last

# Create backup and modify file in place
python remove_duplicates.py data.csv --column id --backup --in-place

# Dry run to preview changes
python remove_duplicates.py data.csv --column email --dry-run

# Specify custom output file
python remove_duplicates.py data.csv --column email --output clean_data.csv
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--column` | `-c` | **Required.** Column name to check for duplicates |
| `--output` | `-o` | Output CSV file path (default: input_file_deduplicated.csv) |
| `--keep-last` | | Keep last occurrence instead of first (default: keep first) |
| `--case-insensitive` | | Treat values case-insensitively (default: case sensitive) |
| `--backup` | | Create backup of original file |
| `--in-place` | | Modify the input file in place (overwrites original) |
| `--dry-run` | | Show what would be done without making changes |

### Programmatic Usage

```python
from remove_duplicates import DuplicateRemover

# Create remover instance
remover = DuplicateRemover()

# Remove duplicates
success = remover.remove_duplicates(
    input_file='data.csv',
    output_file='clean_data.csv',
    column='email',
    keep_first=True,
    case_sensitive=True
)

if success:
    print("Duplicates removed successfully!")
```

## Examples

### Example 1: Remove Duplicate Emails

```bash
python remove_duplicates.py contacts.csv --column email
```

**Input (contacts.csv):**
```csv
id,name,email,department
1,John Doe,john@example.com,IT
2,Jane Smith,jane@example.com,HR
3,John Doe,john@example.com,IT
4,Bob Johnson,bob@example.com,Finance
```

**Output (contacts_deduplicated.csv):**
```csv
id,name,email,department
1,John Doe,john@example.com,IT
2,Jane Smith,jane@example.com,HR
4,Bob Johnson,bob@example.com,Finance
```

### Example 2: Case Insensitive Name Deduplication

```bash
python remove_duplicates.py contacts.csv --column name --case-insensitive
```

This will treat "John Doe", "john doe", and "JOHN DOE" as the same value.

### Example 3: Keep Last Occurrence

```bash
python remove_duplicates.py data.csv --column email --keep-last
```

If there are multiple rows with the same email, the script will keep the last occurrence instead of the first.

## Output and Logging

The script provides detailed logging information:

- **Console output**: Real-time progress and summary
- **Log file**: Detailed logs saved to `duplicate_removal.log`
- **Summary statistics**: Total rows, duplicates removed, processing time

### Sample Output

```
2024-01-15 10:30:15 - remove_duplicates - INFO - Processing 1000 rows from data.csv
2024-01-15 10:30:15 - remove_duplicates - INFO - Removing duplicates based on column: email
2024-01-15 10:30:15 - remove_duplicates - INFO - Keep first occurrence of duplicates
2024-01-15 10:30:15 - remove_duplicates - INFO - Case sensitive: True
2024-01-15 10:30:16 - remove_duplicates - INFO - Found 150 duplicate rows
2024-01-15 10:30:16 - remove_duplicates - INFO - Kept 850 unique rows
2024-01-15 10:30:16 - remove_duplicates - INFO - Successfully wrote 850 rows to clean_data.csv
============================================================
DUPLICATE REMOVAL SUMMARY
============================================================
Input file: data.csv
Output file: clean_data.csv
Total rows processed: 1000
Duplicate rows removed: 150
Unique rows kept: 850
Reduction: 15.00%
Processing time: 0:00:01.234567
============================================================
```

## Error Handling

The script handles various error conditions:

- **File not found**: Clear error message if input file doesn't exist
- **Invalid column**: Error if specified column doesn't exist in CSV
- **Empty files**: Handles empty CSV files gracefully
- **Permission errors**: Handles file permission issues
- **Encoding issues**: Uses UTF-8 encoding by default

## Integration with Export Scripts

This script is designed to work seamlessly with the existing ACGI export scripts:

- **Consistent logging**: Uses the same logging format and configuration
- **Error handling**: Follows the same error handling patterns
- **File naming**: Compatible with the export script naming conventions
- **Directory structure**: Works with the existing export directory structure

### Typical Workflow

1. Export data using existing export scripts
2. Use this script to clean duplicates from exported CSV files
3. Import cleaned data into target systems

```bash
# Export contacts
python export_contacts.py

# Remove duplicate contacts by email
python remove_duplicates.py contacts_export_20240115_103000.csv --column email

# Import cleaned contacts
python import_contacts.py contacts_export_20240115_103000_deduplicated.csv
```

## Performance Considerations

- **Memory usage**: The script loads the entire CSV into memory for processing
- **Large files**: For very large files (>1GB), consider splitting the file first
- **Processing time**: Depends on file size and number of duplicates
- **I/O operations**: Uses efficient CSV reading/writing with proper buffering

## Troubleshooting

### Common Issues

1. **Column not found**: Verify the column name exists in your CSV file
2. **Permission denied**: Ensure you have write permissions for output directory
3. **Empty output**: Check if your input file has data and headers
4. **Encoding issues**: Ensure your CSV file is UTF-8 encoded

### Debug Mode

Use `--dry-run` to preview changes without modifying files:

```bash
python remove_duplicates.py data.csv --column email --dry-run
```

This will show you exactly what would happen without making any changes.

## License

This script is part of the CFMA ACGI integration project and follows the same licensing terms.
