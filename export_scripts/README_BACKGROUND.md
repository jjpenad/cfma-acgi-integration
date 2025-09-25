# Background Export Scripts

This directory contains scripts to run export operations in the background with proper logging and monitoring.

## 📁 Files

- `run_export_background.py` - Python script to run exports in background (Cross-platform)
- `run_export_background.bat` - Windows batch file for background execution
- `run_export_background.ps1` - PowerShell script for background execution
- `run_export_background.sh` - Linux/Unix shell script for background execution
- `monitor_exports.py` - Monitor running export processes (Cross-platform)

## 🚀 Usage

### Method 1: Python Script (Recommended)

```bash
# Run single export script in background
python run_export_background.py export_event_registrations.py contacts_export.csv

# Run with custom output file
python run_export_background.py export_event_registrations.py contacts_export.csv --output my_export.csv

# Run all export scripts in background
python run_export_background.py all contacts_export.csv

# Run with custom log file
python run_export_background.py export_event_registrations.py contacts_export.csv --log-file my_export.log
```

### Method 2: Batch File

```bash
# Run export in background
run_export_background.bat export_event_registrations.py contacts_export.csv

# Run with output file
run_export_background.bat export_event_registrations.py contacts_export.csv my_output.csv
```

### Method 3: PowerShell (Windows)

```powershell
# Run export in background
.\run_export_background.ps1 -ScriptName "export_event_registrations.py" -CsvFile "contacts_export.csv"

# Run with output file
.\run_export_background.ps1 -ScriptName "export_event_registrations.py" -CsvFile "contacts_export.csv" -OutputFile "my_export.csv"

# Run with custom log file
.\run_export_background.ps1 -ScriptName "export_event_registrations.py" -CsvFile "contacts_export.csv" -LogFile "my_export.log"
```

### Method 4: Shell Script (Linux/Unix)

```bash
# Make executable first
chmod +x run_export_background.sh

# Run export in background
./run_export_background.sh export_event_registrations.py contacts_export.csv

# Run with output file
./run_export_background.sh export_event_registrations.py contacts_export.csv my_output.csv
```

## 📊 Monitoring

### Check Status
```bash
# Show export status
python monitor_exports.py --status

# Monitor specific log file
python monitor_exports.py --log export_event_registrations_background_20240925_110000.log

# Show last 20 lines of log
python monitor_exports.py --log export_event_registrations_background_20240925_110000.log --no-follow
```

### Manual Process Monitoring

**Windows:**
```bash
# Check Python processes
tasklist | findstr python

# Check specific process
tasklist /FI "PID eq 12345"

# Stop specific process
taskkill /PID 12345
```

**Linux/Unix:**
```bash
# Check Python processes
ps aux | grep python

# Check specific process
ps -p 12345

# Stop specific process
kill 12345
```

## 📝 Log Files

Log files are automatically created with timestamps:
- Format: `{script_name}_background_{timestamp}.log`
- Example: `export_event_registrations_background_20240925_110000.log`

## 🔧 Features

### Python Script Features
- ✅ Run single or all export scripts
- ✅ Automatic log file generation
- ✅ Process monitoring
- ✅ Error handling
- ✅ Custom output directories

### Batch File Features
- ✅ Simple Windows batch execution
- ✅ Automatic timestamping
- ✅ Log file creation
- ✅ Error checking

### PowerShell Features
- ✅ Background job execution
- ✅ Real-time monitoring
- ✅ Parameter validation
- ✅ Job management

## 📋 Examples

### Run Event Registrations Export
```bash
python run_export_background.py export_event_registrations.py contacts_export.csv
```

### Run All Exports
```bash
python run_export_background.py all contacts_export.csv --output-dir ./exports
```

### Monitor Progress
```bash
python monitor_exports.py --log export_event_registrations_background_20240925_110000.log
```

### Check Status
```bash
python monitor_exports.py --status
```

## ⚠️ Notes

1. **Background Execution**: Scripts run in background, so you can close the terminal
2. **Log Files**: All output is logged to timestamped files
3. **Process Management**: Use the monitor script to check progress
4. **Error Handling**: Errors are logged and can be monitored
5. **Resource Usage**: Multiple exports can run simultaneously

## 🛠️ Troubleshooting

### Script Not Starting
- Check if Python is in PATH
- Verify script files exist
- Check CSV file path

### No Output
- Check log files for errors
- Verify ACGI credentials
- Check network connectivity

### Process Not Found
- Use `tasklist | findstr python` to find processes
- Check if process completed successfully
- Look for error messages in log files
