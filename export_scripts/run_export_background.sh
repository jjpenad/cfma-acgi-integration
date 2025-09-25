#!/bin/bash
# Background Export Runner - Linux/Unix Shell Script
# Usage: ./run_export_background.sh [script_name] [csv_file] [output_file]

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 [script_name] [csv_file] [output_file]"
    echo "Example: $0 export_event_registrations.py contacts_export.csv"
    exit 1
fi

SCRIPT_NAME="$1"
CSV_FILE="$2"
OUTPUT_FILE="$3"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${SCRIPT_NAME%.*}_background_${TIMESTAMP}.log"

# Change to script directory
cd "$(dirname "$0")"

# Check if script exists
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Error: Script '$SCRIPT_NAME' not found!"
    exit 1
fi

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file '$CSV_FILE' not found!"
    exit 1
fi

echo "Starting $SCRIPT_NAME in background..."
echo "Command: python $SCRIPT_NAME $CSV_FILE $OUTPUT_FILE"
echo "Log file: $LOG_FILE"
echo "Started at: $(date)"
echo "------------------------------------------------------------"

# Build command
CMD="python $SCRIPT_NAME $CSV_FILE"
if [ -n "$OUTPUT_FILE" ]; then
    CMD="$CMD --output $OUTPUT_FILE"
fi

# Run in background with logging
nohup $CMD > "$LOG_FILE" 2>&1 &
PID=$!

echo "Process started with PID: $PID"
echo "Check progress with: tail -f $LOG_FILE"
echo "Check if running with: ps aux | grep python"
echo "To stop: kill $PID"
echo ""
echo "Log file: $LOG_FILE"
if [ -n "$OUTPUT_FILE" ]; then
    echo "Output file: $OUTPUT_FILE"
fi
