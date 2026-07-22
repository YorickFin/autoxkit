<#
.SYNOPSIS
    Auto build autoxkit multi-version wheels

.DESCRIPTION
    Build wheels for Python 3.10-3.13, output to dist directory

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Versions "3.10","3.12"
    .\build.ps1 -CleanOnly
#>

param(
    [string[]]$Versions = @("3.10", "3.11", "3.12", "3.13"),
    [switch]$CleanOnly,
    [switch]$SkipPublish
)

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Command)
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

function Install-PythonVersions {
    param([string[]]$Versions)
    foreach ($ver in $Versions) {
        Write-Host "`n[INFO] Checking Python $ver installation..."
        $installed = uv python list --only-installed 2>$null | Select-String "cpython-$ver"
        if (-not $installed) {
            Write-Host "[INFO] Installing Python $ver..."
            uv python install $ver
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install Python $ver"
            }
        } else {
            Write-Host "[OK] Python $ver is already installed"
        }
    }
}

function Build-Wheels {
    param([string[]]$Versions)
    foreach ($ver in $Versions) {
        Write-Host "`n[INFO] Building Python $ver wheel..."
        uv build --python $ver --wheel --out-dir dist
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build Python $ver wheel"
        }
        Write-Host "[OK] Python $ver wheel built successfully"
    }
}

function Verify-Build {
    param([string[]]$Versions)
    Write-Host "`n[INFO] Verifying build artifacts..."
    $actualWheels = Get-ChildItem -Path "dist" -Filter "*.whl" -Name
    
    if ($actualWheels.Count -eq 0) {
        Write-Error "No wheel files found"
    }
    
    Write-Host "`nBuild artifacts:"
    foreach ($wheel in $actualWheels) {
        $size = (Get-Item "dist\$wheel").Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host ("  {0} ({1} MB)" -f $wheel, $sizeMB)
    }
    
    Write-Host ("`n[OK] Verification complete, {0} wheel files built" -f $actualWheels.Count)
}

function Publish-Wheels {
    Write-Host "`n[INFO] Publishing to PyPI..."
    uv publish
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Publish failed"
    }
    Write-Host "[OK] Publish successful"
}

Write-Host "======================================"
Write-Host "  autoxkit Multi-Version Build Script"
Write-Host "======================================"

if (-not (Test-CommandExists "uv")) {
    Write-Error "uv not found, please install first: https://github.com/astral-sh/uv"
}

Write-Host "[INFO] uv version: $(uv --version)"

if (-not $CleanOnly) {
    Write-Host "[INFO] Target Python versions: $($Versions -join ', ')"
    
    Install-PythonVersions -Versions $Versions
    
    Write-Host "`n[INFO] Cleaning old build artifacts..."
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
    }
    
    Build-Wheels -Versions $Versions
    
    Verify-Build -Versions $Versions
    
    if (-not $SkipPublish) {
        Write-Host "`n[WARN] About to publish to PyPI, press Enter to continue, Ctrl+C to cancel..."
        Read-Host
        Publish-Wheels
    } else {
        Write-Host "`n[INFO] Publish step skipped, artifacts are in dist/ directory"
    }
} else {
    Write-Host "[INFO] Clean mode, removing build artifacts only..."
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
        Write-Host "[OK] dist/ directory deleted"
    } else {
        Write-Host "[INFO] dist/ directory does not exist, nothing to clean"
    }
}

Write-Host "`n======================================"
Write-Host "  Build script execution complete"
Write-Host "======================================"
