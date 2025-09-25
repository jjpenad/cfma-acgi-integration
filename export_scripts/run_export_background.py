#!/usr/bin/env python3
"""
Background Export Runner

This script runs the export scripts in the background with proper logging and monitoring.
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path

def run_export_background(script_name, csv_file, output_file=None, id_column='custId', log_file=None):
    """
    Run an export script in the background
    
    Args:
        script_name: Name of the export script to run
        csv_file: Path to CSV file containing customer IDs
        output_file: Optional output file path
        id_column: Name of the column containing customer IDs
        log_file: Optional log file path
    """
    
    # Validate script exists
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"Error: Script '{script_name}' not found!")
        return False
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{script_name.replace('.py', '')}_background_{timestamp}.log"
    
    # Build command
    cmd = [sys.executable, script_name, csv_file]
    
    if output_file:
        cmd.extend(['--output', output_file])
    
    if id_column != 'custId':
        cmd.extend(['--id-column', id_column])
    
    print(f"Starting {script_name} in background...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Log file: {log_file}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Run the script in background
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        
    print(f"Process started with PID: {process.pid}")
    
    # Platform-specific monitoring commands
    import platform
    if platform.system() == "Windows":
        print(f"Check progress with: Get-Content {log_file} -Wait")
        print(f"Check if running with: tasklist | findstr python")
        print(f"To stop: taskkill /PID {process.pid}")
    else:
        print(f"Check progress with: tail -f {log_file}")
        print(f"Check if running with: ps aux | grep python")
        print(f"To stop: kill {process.pid}")
        
        return True
        
    except Exception as e:
        print(f"Error starting background process: {e}")
        return False

def run_all_exports_background(csv_file, output_dir=None, log_file=None):
    """
    Run all export scripts in background
    
    Args:
        csv_file: Path to CSV file containing customer IDs
        output_dir: Directory for output files
        log_file: Optional log file path
    """
    
    scripts = [
        'export_contacts.py',
        'export_events.py', 
        'export_event_registrations.py',
        'export_memberships.py',
        'export_purchased_products.py'
    ]
    
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"all_exports_background_{timestamp}.log"
    
    print(f"Starting all export scripts in background...")
    print(f"CSV file: {csv_file}")
    print(f"Log file: {log_file}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    processes = []
    
    for script in scripts:
        if Path(script).exists():
            cmd = [sys.executable, script, csv_file]
            if output_dir:
                cmd.extend(['--output', os.path.join(output_dir, f"{script.replace('.py', '')}_export.csv")])
            
            try:
                with open(log_file, 'a') as log:
                    log.write(f"\n{'='*60}\n")
                    log.write(f"Starting {script} at {datetime.now()}\n")
                    log.write(f"Command: {' '.join(cmd)}\n")
                    log.write(f"{'='*60}\n")
                    
                    process = subprocess.Popen(
                        cmd,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                
                processes.append((script, process))
                print(f"Started {script} with PID: {process.pid}")
                
                # Small delay between starting scripts
                time.sleep(2)
                
            except Exception as e:
                print(f"Error starting {script}: {e}")
        else:
            print(f"Warning: {script} not found, skipping...")
    
    print(f"\nAll processes started!")
    
    # Platform-specific monitoring commands
    import platform
    if platform.system() == "Windows":
        print(f"Check progress with: Get-Content {log_file} -Wait")
        print(f"Check if running with: tasklist | findstr python")
    else:
        print(f"Check progress with: tail -f {log_file}")
        print(f"Check if running with: ps aux | grep python")
    
    print(f"Process PIDs: {[p[1].pid for p in processes]}")
    
    return processes

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run export scripts in background')
    parser.add_argument('script', help='Export script to run (or "all" for all scripts)')
    parser.add_argument('csv_file', help='Path to CSV file containing customer IDs')
    parser.add_argument('--output', help='Output file path (for single script)')
    parser.add_argument('--output-dir', help='Output directory (for all scripts)')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    if args.script.lower() == 'all':
        run_all_exports_background(
            csv_file=args.csv_file,
            output_dir=args.output_dir,
            log_file=args.log_file
        )
    else:
        run_export_background(
            script_name=args.script,
            csv_file=args.csv_file,
            output_file=args.output,
            id_column=args.id_column,
            log_file=args.log_file
        )

if __name__ == "__main__":
    main()
