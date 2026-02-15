# setup_project_windows.ps1 - Script to set up the eip2nats project on Windows
# Requires: Visual Studio Build Tools (MSVC), Git, CMake, Python 3.7+
# Run from: Developer PowerShell for VS or with vcvarsall.bat loaded

param(
    [switch]$SkipVenv,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  eip2nats Project Setup (Windows)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Helper functions
# ============================================================

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Write-Step {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# ============================================================
# Step 0: Check system requirements
# ============================================================

Write-Host "Checking system requirements..." -ForegroundColor Yellow
Write-Host ""

# Git
if (Test-Command "git") {
    Write-Step "git found: $(git --version)"
} else {
    Write-Fail "git not found. Install from https://git-scm.com/download/win"
    exit 1
}

# CMake
if (Test-Command "cmake") {
    Write-Step "cmake found: $(cmake --version | Select-Object -First 1)"
} else {
    Write-Fail "cmake not found. Install from https://cmake.org/download/ or via Visual Studio Installer"
    exit 1
}

# Python
$pythonCmd = $null
if (Test-Command "python") {
    $pythonCmd = "python"
} elseif (Test-Command "python3") {
    $pythonCmd = "python3"
}

if ($pythonCmd) {
    $pyVersion = & $pythonCmd --version 2>&1
    Write-Step "$pythonCmd found: $pyVersion"
} else {
    Write-Fail "Python not found. Install from https://www.python.org/downloads/"
    exit 1
}

# MSVC (cl.exe)
$hasMSVC = Test-Command "cl"
if ($hasMSVC) {
    Write-Step "MSVC (cl.exe) found"
} else {
    Write-Warn "cl.exe not found in PATH"
    Write-Host ""
    Write-Host "  MSVC is not in the PATH. Options:" -ForegroundColor Yellow
    Write-Host "    1. Run this script from 'Developer PowerShell for VS'" -ForegroundColor Yellow
    Write-Host "    2. Run first: " -ForegroundColor Yellow -NoNewline
    Write-Host 'vcvarsall.bat x64' -ForegroundColor White
    Write-Host ""

    # Try to find vcvarsall.bat and load it
    $vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vsWhere) {
        $vsInstallPath = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
        if ($vsInstallPath) {
            $vcvarsall = Join-Path $vsInstallPath "VC\Auxiliary\Build\vcvarsall.bat"
            if (Test-Path $vcvarsall) {
                Write-Host "  Found Visual Studio at: $vsInstallPath" -ForegroundColor Cyan
                Write-Host "  Attempting to load MSVC environment..." -ForegroundColor Cyan

                # Load vcvarsall environment into PowerShell
                $envBefore = @{}
                Get-ChildItem Env: | ForEach-Object { $envBefore[$_.Name] = $_.Value }

                $tempFile = [System.IO.Path]::GetTempFileName()
                cmd /c "`"$vcvarsall`" x64 && set > `"$tempFile`""

                if (Test-Path $tempFile) {
                    Get-Content $tempFile | ForEach-Object {
                        if ($_ -match '^([^=]+)=(.*)$') {
                            $name = $matches[1]
                            $value = $matches[2]
                            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
                        }
                    }
                    Remove-Item $tempFile -Force
                }

                if (Test-Command "cl") {
                    Write-Step "MSVC environment loaded successfully"
                    $hasMSVC = $true
                } else {
                    Write-Fail "Could not load MSVC environment automatically"
                    exit 1
                }
            }
        }
    }

    if (-not $hasMSVC) {
        Write-Fail "Visual Studio Build Tools not found"
        Write-Host "  Install from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Yellow
        Write-Host "  Select: 'Desktop development with C++'" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Step "All system requirements are installed"
Write-Host ""

# ============================================================
# Step 1: Create virtual environment
# ============================================================

$VENV_DIR = "venv"

if (-not $SkipVenv) {
    if (Test-Path $VENV_DIR) {
        Write-Host "Virtual environment already exists in $VENV_DIR" -ForegroundColor Cyan
    } else {
        Write-Host "Creating virtual environment in $VENV_DIR..." -ForegroundColor Cyan
        & $pythonCmd -m venv $VENV_DIR
        Write-Step "Virtual environment created"
    }
}

# Always activate the venv (even with -SkipVenv, we need it active)
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
} else {
    Write-Fail "Activation script not found: $activateScript"
    exit 1
}

if (-not $SkipVenv) {
    # Upgrade pip (use python -m pip to avoid self-update issues on Windows)
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    & $pythonCmd -m pip install --upgrade pip

    # Install build dependencies
    Write-Host "Installing build dependencies..." -ForegroundColor Cyan
    & $pythonCmd -m pip install build pybind11 hatch twine
}

Write-Host ""

# ============================================================
# Steps 2-4: Build dependencies (nats.c, EIPScanner, binding)
# ============================================================

if (-not $SkipBuild) {
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Step 2: Build nats.c" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_nats.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error building nats.c"
        exit 1
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Step 3: Build EIPScanner" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_eipscanner.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error building EIPScanner"
        exit 1
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Step 4: Build Python binding" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_binding.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error building Python binding"
        exit 1
    }
}

Write-Host ""

# ============================================================
# Step 5: Create wheel
# ============================================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Step 5: Create wheel" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Verify that libraries exist
$libDir = "src\eip2nats\lib"
$dlls = Get-ChildItem -Path $libDir -Filter "*.dll" -ErrorAction SilentlyContinue
if (-not $dlls) {
    Write-Fail "No DLLs found in $libDir"
    exit 1
}

Write-Step "DLLs found:"
$dlls | ForEach-Object { Write-Host "    $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

# Verify that the Python module exists
$pydFiles = Get-ChildItem -Path "src\eip2nats" -Filter "eip_nats_bridge*.pyd" -ErrorAction SilentlyContinue
if (-not $pydFiles) {
    Write-Fail "Compiled Python module (.pyd) not found in src\eip2nats\"
    exit 1
}

Write-Step "Compiled Python module:"
$pydFiles | ForEach-Object { Write-Host "    $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

# Build wheel
& $pythonCmd -m build --wheel

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Fail "Error creating wheel"
    exit 1
}

Write-Host ""

# ============================================================
# Step 6: Install wheel in the venv
# ============================================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Step 6: Install wheel in the venv" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$wheelFile = Get-ChildItem -Path "dist" -Filter "eip2nats-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($wheelFile) {
    Write-Host "Installing $($wheelFile.Name) in the virtual environment..."
    & $pythonCmd -m pip install $wheelFile.FullName --force-reinstall

    if ($LASTEXITCODE -eq 0) {
        Write-Step "Wheel installed in the virtual environment"
    } else {
        Write-Fail "Error installing wheel"
        exit 1
    }
} else {
    Write-Fail "Wheel not found in dist\"
    exit 1
}

Write-Host ""

# ============================================================
# Final summary
# ============================================================

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Wheel created in: dist\" -ForegroundColor Cyan
Get-ChildItem dist\*.whl | ForEach-Object { Write-Host "  $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

Write-Host "The module is installed in the virtual environment" -ForegroundColor Cyan
Write-Host ""
Write-Host "To use the project:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  # Activate virtual environment:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Test:" -ForegroundColor White
Write-Host "  python -c `"import eip2nats; print(eip2nats.__version__)`"" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Use:" -ForegroundColor White
Write-Host "  python your_script.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Deactivate when done:" -ForegroundColor White
Write-Host "  deactivate" -ForegroundColor Gray
Write-Host ""
