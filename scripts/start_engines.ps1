param(
    [int]$NumMappers = 2,
    [int]$NumReducers = 2,
    # Allow caller override, but default to repository root's backend folder
    [string]$BackendDir = (Join-Path $PSScriptRoot '..\backend'),
    [string]$ApiUrl = 'https://visual-map-reduce.preview.emergentagent.com/api/engines'
)

# Resolve and validate BackendDir: if the default (scripts\..\backend) doesn't exist,
# try repo root / backend. Exit with a helpful error if backend cannot be found.
try {
    $resolved = Resolve-Path -Path $BackendDir -ErrorAction SilentlyContinue
    if (-not $resolved) {
        $candidate = Join-Path $PSScriptRoot '..\backend'
        $resolvedCandidate = Resolve-Path -Path $candidate -ErrorAction SilentlyContinue
        if ($resolvedCandidate) {
            $BackendDir = $resolvedCandidate.Path
        } else {
            # Try one level up (in case script is run from repo root)
            $alt = Join-Path $PSScriptRoot '..\..\backend'
            $resolvedAlt = Resolve-Path -Path $alt -ErrorAction SilentlyContinue
            if ($resolvedAlt) {
                $BackendDir = $resolvedAlt.Path
            } else {
                Write-Error "Backend directory not found. Expected at: $BackendDir or $candidate or $alt"
                return
            }
        }
    } else {
        $BackendDir = $resolved.Path
    }
} catch {
    Write-Error "Error resolving BackendDir: $_"
    return
}

Write-Output "=================================="
Write-Output "MapReduce Visual - Starting Engines"
Write-Output "==================================`n"

Write-Output "Backend dir: $BackendDir"
Write-Output "Stopping existing engines..."

# Find and stop processes that run engine.py (uses Win32_Process to access command line)
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'engine\.py' } |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
            Write-Output "  - Stopped PID $($_.ProcessId)"
        } catch {
            Write-Output "  - Failed to stop PID $($_.ProcessId): $_"
        }
    }

Start-Sleep -Seconds 2

# Start mappers
Write-Output "`nStarting $NumMappers mappers..."
for ($i = 1; $i -le $NumMappers; $i++) {
    $log = Join-Path $env:TEMP "mapper$i.log"
    $args = "engine.py --engine-id mapper-$i --role mapper --capacity 5"
$proc = Start-Process -FilePath python -ArgumentList $args -WorkingDirectory $BackendDir -RedirectStandardOutput $log -RedirectStandardError "$($log).err" -WindowStyle Hidden -PassThru
    Write-Output "  - mapper-$i started (PID: $($proc.Id)) -> $log"
}

# Start reducers
Write-Output "`nStarting $NumReducers reducers..."
for ($i = 1; $i -le $NumReducers; $i++) {
    $log = Join-Path $env:TEMP "reducer$i.log"
    $args = "engine.py --engine-id reducer-$i --role reducer --capacity 5"
$proc = Start-Process -FilePath python -ArgumentList $args -WorkingDirectory $BackendDir -RedirectStandardOutput $log -RedirectStandardError "$($log).err" -WindowStyle Hidden -PassThru
    Write-Output "  - reducer-$i started (PID: $($proc.Id)) -> $log"
}

Write-Output "`nWaiting for engines to register..."
Start-Sleep -Seconds 4

Write-Output "`nRegistered engines:"
try {
    $engines = Invoke-RestMethod -Uri $ApiUrl -ErrorAction Stop
    if ($null -eq $engines) {
        Write-Output "  No response or empty list."
    } else {
        Write-Output "  Total: $($engines.Count) engines"
        $mappers = $engines | Where-Object { $_.role -eq 'mapper' }
        $reducers = $engines | Where-Object { $_.role -eq 'reducer' }
        Write-Output "  - Mappers: $($mappers.Count)"
        Write-Output "  - Reducers: $($reducers.Count)"
        foreach ($e in $engines) {
            Write-Output "    $($e.engine_id) ($($e.role)): $($e.status)"
        }
    }
} catch {
    Write-Output "  Error checking engines: $_"
}

Write-Output "`n=================================="
Write-Output "✓ Engines started successfully!"
Write-Output ""
Write-Output "View logs:"
Write-Output "  Get-Content -Path (Join-Path $env:TEMP 'mapper*.log') -Tail 200 -Wait"
Write-Output "  Get-Content -Path (Join-Path $env:TEMP 'reducer*.log') -Tail 200 -Wait"
Write-Output ""
Write-Output "Stop engines:"
Write-Output "  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'engine\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
Write-Output "=================================="