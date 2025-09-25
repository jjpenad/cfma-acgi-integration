# Background Export Runner - PowerShell Version
# Usage: .\run_export_background.ps1 -ScriptName "export_event_registrations.py" -CsvFile "contacts_export.csv"

param(
    [Parameter(Mandatory=$true)]
    [string]$ScriptName,
    
    [Parameter(Mandatory=$true)]
    [string]$CsvFile,
    
    [string]$OutputFile = "",
    [string]$IdColumn = "custId",
    [string]$LogFile = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

try {
    # Change to script directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $ScriptDir
    
    # Generate log file name if not provided
    if ([string]::IsNullOrEmpty($LogFile)) {
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $LogFile = "$($ScriptName.Replace('.py', ''))_background_$Timestamp.log"
    }
    
    # Check if script exists
    if (-not (Test-Path $ScriptName)) {
        Write-Error "Script '$ScriptName' not found!"
        exit 1
    }
    
    # Check if CSV file exists
    if (-not (Test-Path $CsvFile)) {
        Write-Error "CSV file '$CsvFile' not found!"
        exit 1
    }
    
    Write-Host "Starting $ScriptName in background..." -ForegroundColor Green
    Write-Host "CSV file: $CsvFile" -ForegroundColor Yellow
    Write-Host "Log file: $LogFile" -ForegroundColor Yellow
    Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor Gray
    
    # Build command
    $Command = "python", $ScriptName, $CsvFile
    
    if (-not [string]::IsNullOrEmpty($OutputFile)) {
        $Command += "--output", $OutputFile
    }
    
    if ($IdColumn -ne "custId") {
        $Command += "--id-column", $IdColumn
    }
    
    Write-Host "Command: $($Command -join ' ')" -ForegroundColor Cyan
    
    # Start background job
    $Job = Start-Job -ScriptBlock {
        param($Cmd, $Log)
        & $Cmd[0] $Cmd[1..($Cmd.Length-1)] | Out-File -FilePath $Log -Append
    } -ArgumentList $Command, $LogFile
    
    Write-Host "Job started with ID: $($Job.Id)" -ForegroundColor Green
    Write-Host "Check progress with: Get-Content '$LogFile' -Wait" -ForegroundColor Cyan
    Write-Host "Check job status with: Get-Job" -ForegroundColor Cyan
    Write-Host "Get job output with: Receive-Job $($Job.Id)" -ForegroundColor Cyan
    Write-Host "Stop job with: Stop-Job $($Job.Id)" -ForegroundColor Cyan
    
    # Optional: Wait and show initial output
    Write-Host "`nWaiting 5 seconds for initial output..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    if (Test-Path $LogFile) {
        Write-Host "`nInitial output:" -ForegroundColor Green
        Get-Content $LogFile -Tail 10
    }
    
    Write-Host "`nExport is running in background!" -ForegroundColor Green
    Write-Host "Log file: $LogFile" -ForegroundColor Yellow
    
} catch {
    Write-Error "Error: $($_.Exception.Message)"
    exit 1
}
