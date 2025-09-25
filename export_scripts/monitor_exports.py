#!/usr/bin/env python3
"""
Export Monitor

This script monitors running export processes and shows their progress.
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

def get_python_processes():
    """Get all running Python processes"""
    import platform
    
    try:
        if platform.system() == "Windows":
            # Windows: use tasklist
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            processes = []
            
            for line in lines[3:]:  # Skip header lines
                if 'python.exe' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        processes.append(pid)
            
            return processes
        else:
            # Linux/macOS: use ps
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            processes = []
            
            for line in lines[1:]:  # Skip header line
                if 'python' in line and 'monitor_exports.py' not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        processes.append(pid)
            
            return processes
            
    except Exception as e:
        print(f"Error getting processes: {e}")
        return []

def monitor_log_file(log_file, follow=True):
    """Monitor a log file for progress"""
    if not Path(log_file).exists():
        print(f"Log file '{log_file}' not found!")
        return
    
    print(f"Monitoring log file: {log_file}")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 60)
    
    try:
        if follow:
            # Follow the log file in real-time
            with open(log_file, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
        else:
            # Show last N lines
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:  # Show last 20 lines
                    print(line.rstrip())
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error monitoring log: {e}")

def show_export_status():
    """Show status of all export processes"""
    processes = get_python_processes()
    
    print(f"Export Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not processes:
        print("No Python processes running.")
        return
    
    print(f"Found {len(processes)} Python process(es):")
    for i, pid in enumerate(processes, 1):
        print(f"  {i}. PID: {pid}")
    
    # Look for log files
    log_files = list(Path('.').glob('*_background_*.log'))
    if log_files:
        print(f"\nFound {len(log_files)} log file(s):")
        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size = log_file.stat().st_size
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  - {log_file.name} ({size} bytes, modified: {mtime.strftime('%H:%M:%S')})")
    
    print("\nCommands:")
    print("  Monitor log: python monitor_exports.py --log <log_file>")
    print("  Show last lines: python monitor_exports.py --log <log_file> --no-follow")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Monitor export processes')
    parser.add_argument('--log', help='Log file to monitor')
    parser.add_argument('--no-follow', action='store_true', help='Show last lines instead of following')
    parser.add_argument('--status', action='store_true', help='Show export status')
    
    args = parser.parse_args()
    
    if args.log:
        monitor_log_file(args.log, follow=not args.no_follow)
    elif args.status:
        show_export_status()
    else:
        show_export_status()

if __name__ == "__main__":
    main()
