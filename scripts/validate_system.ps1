<#
    MapReduce Visual - System Validation (PowerShell)
    Translated from scripts/validate_system.sh

    Usage: Run from repository root or scripts folder:
      pwsh ./scripts/validate_system.ps1

    This script checks:
      - Backend REST API
      - gRPC port
      - Frontend
      - Engines (via /api/stats)
      - Critical files existence
      - Optional end-to-end test job if engines present
#>

Clear-Host
Write-Host "========================================"
Write-Host "MapReduce Visual - System Validation"
Write-Host "========================================`n"

$global:ERRORS = 0

function Check-Result {
    param(
        [bool]$Success,
        [string]$Message
    )
    if ($Success) {
        Write-Host "✓ $Message" -ForegroundColor Green
    } else {
        Write-Host "✗ $Message" -ForegroundColor Red
        $global:ERRORS = $global:ERRORS + 1
    }
}

# Configuration
$ApiBase = 'http://localhost:8000/api/stats'
$FrontendUrl = 'http://localhost:3000'

# 1. Backend Coordinator (REST API)
Write-Host "1. Backend Coordinator (REST API)"
try {
    $resp = Invoke-WebRequest -Uri "$ApiBase/" -UseBasicParsing -Method GET -TimeoutSec 3 -ErrorAction Stop
    $ok = $true
} catch {
    $ok = $false
}
Check-Result -Success $ok -Message "REST API responding on port 8000"

# 2. gRPC Server (port 50051)
Write-Host "`n2. gRPC Server"
try {
    $conn = Test-NetConnection -ComputerName 'localhost' -Port 50051 -WarningAction SilentlyContinue
    $ok = $false
    if ($null -ne $conn) { $ok = $conn.TcpTestSucceeded }
} catch {
    $ok = $false
}
Check-Result -Success $ok -Message "gRPC server listening on port 50051"

# 3. Frontend
Write-Host "`n3. Frontend"
try {
    $f = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -Method GET -TimeoutSec 3 -ErrorAction Stop
    $ok = $true
} catch {
    $ok = $false
}
Check-Result -Success $ok -Message "React frontend accessible"

# 4. Engines (Workers)
Write-Host "`n4. Engines (Workers)"
$totalEngines = 0; $mappers = 0; $reducers = 0
try {
    $stats = Invoke-RestMethod -Uri "$ApiBase/stats" -Method GET -ErrorAction Stop -TimeoutSec 3
    if ($stats) {
        $totalEngines = $stats.total_engines
        $mappers = $stats.mappers
        $reducers = $stats.reducers
    }
} catch {
    # ignore — will report below
}

if ($totalEngines -gt 0) {
    Write-Host "  ✓ $totalEngines engines connected ($mappers mappers, $reducers reducers)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No engines connected. Run: ./scripts/start_engines.ps1" -ForegroundColor Yellow
}

# 5. Critical Files
Write-Host "`n5. Critical Files"
$repoRoot = Resolve-Path -Path (Join-Path $PSScriptRoot '..') -ErrorAction SilentlyContinue
if (-not $repoRoot) { $repoRoot = Resolve-Path -Path $PSScriptRoot -ErrorAction SilentlyContinue }

$serverPath = Join-Path $repoRoot 'backend\server.py'
$enginePath = Join-Path $repoRoot 'backend\engine.py'
$grpcStub = Join-Path $repoRoot 'backend\jobs_pb2.py'
$appJs = Join-Path $repoRoot 'frontend\src\App.js'

Check-Result -Success (Test-Path $serverPath) -Message "server.py exists"
Check-Result -Success (Test-Path $enginePath) -Message "engine.py exists"
Check-Result -Success (Test-Path $grpcStub) -Message "gRPC stubs generated"
Check-Result -Success (Test-Path $appJs) -Message "Frontend App.js exists"

# 6. End-to-End Test (Optional)
Write-Host "`n6. End-to-End Test (Optional)"
if ($totalEngines -gt 0) {
    Write-Host "Creating test job..."
    $body = @{ text = 'test job validation quick brown fox lazy dog'; balancing_strategy = 'round_robin' } | ConvertTo-Json
    try {
        $jobResp = Invoke-RestMethod -Uri "$ApiBase/jobs" -Method Post -Body $body -ContentType 'application/json' -ErrorAction Stop
        $jobId = $jobResp.job_id
    } catch {
        $jobId = $null
    }

    if ($jobId) {
        Check-Result -Success $true -Message "Test job created: $jobId"
        Write-Host "  Waiting for completion..."
        $status = $null
        for ($i = 0; $i -lt 15; $i++) {
            Start-Sleep -Seconds 1
            try {
                $j = Invoke-RestMethod -Uri "$ApiBase/jobs/$jobId" -Method GET -ErrorAction Stop
                $status = $j.status
            } catch {
                $status = $null
            }
            Write-Host -NoNewline "."
            if ($status -eq 'done') {
                Write-Host "`n"
                Check-Result -Success $true -Message "Job completed successfully"
                break
            }
        }
        if ($status -ne 'done') {
            Write-Host "`n⚠ Job still processing (status: $status)" -ForegroundColor Yellow
        }
    } else {
        Check-Result -Success $false -Message "Failed to create test job"
    }
} else {
    Write-Host "⚠ Skipping (no engines available)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n========================================"
if ($global:ERRORS -eq 0) {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
    Write-Host "`nSystem is ready to use:"
    Write-Host "  Frontend: https://visual-map-reduce.preview.emergentagent.com"
    Write-Host "  API Docs: http://localhost:8000/docs"
} else {
    Write-Host "✗ $global:ERRORS checks failed" -ForegroundColor Red
    Write-Host "`nTroubleshooting:"
    Write-Host "  1. Restart backend: sudo supervisorctl restart backend" -ForegroundColor Yellow
    Write-Host "  2. Start engines: ./scripts/start_engines.ps1" -ForegroundColor Yellow
    Write-Host "  3. Check logs: tail -f /var/log/supervisor/backend.*.log" -ForegroundColor Yellow
}
Write-Host "========================================"

exit $global:ERRORS
