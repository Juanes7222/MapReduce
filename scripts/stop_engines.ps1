# Stop all MapReduce engines (mappers and reducers)

Write-Output "=================================="
Write-Output "MapReduce Visual - Stopping Engines"
Write-Output "==================================`n"

# Find all processes running engine.py
$engines = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'engine\.py' }

if ($engines.Count -eq 0) {
    Write-Output "No engines running."
} else {
    Write-Output "Found $($engines.Count) engine(s) running:"
    
    foreach ($proc in $engines) {
        # Extract engine-id from command line
        if ($proc.CommandLine -match '--engine-id\s+(\S+)') {
            $engineId = $matches[1]
        } else {
            $engineId = "unknown"
        }
        
        Write-Output "  - PID $($proc.ProcessId): $engineId"
    }
    
    Write-Output "`nStopping all engines..."
    
    foreach ($proc in $engines) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            Write-Output "   Stopped PID $($proc.ProcessId)"
        } catch {
            Write-Output "   Failed to stop PID $($proc.ProcessId): $_"
        }
    }
    
    Write-Output "`n✓ All engines stopped successfully!"
}

Write-Output "==================================`n"
