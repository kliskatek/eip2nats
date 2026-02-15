# setup_project_windows.ps1 - Script para configurar el proyecto eip2nats en Windows
# Requiere: Visual Studio Build Tools (MSVC), Git, CMake, Python 3.7+
# Ejecutar desde: Developer PowerShell for VS o con vcvarsall.bat cargado

param(
    [switch]$SkipVenv,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Configuracion de eip2nats Project (Windows)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Funciones auxiliares
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
# Paso 0: Verificar requisitos del sistema
# ============================================================

Write-Host "Verificando requisitos del sistema..." -ForegroundColor Yellow
Write-Host ""

# Git
if (Test-Command "git") {
    Write-Step "git encontrado: $(git --version)"
} else {
    Write-Fail "git no encontrado. Instalar desde https://git-scm.com/download/win"
    exit 1
}

# CMake
if (Test-Command "cmake") {
    Write-Step "cmake encontrado: $(cmake --version | Select-Object -First 1)"
} else {
    Write-Fail "cmake no encontrado. Instalar desde https://cmake.org/download/ o via Visual Studio Installer"
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
    Write-Step "$pythonCmd encontrado: $pyVersion"
} else {
    Write-Fail "Python no encontrado. Instalar desde https://www.python.org/downloads/"
    exit 1
}

# MSVC (cl.exe)
$hasMSVC = Test-Command "cl"
if ($hasMSVC) {
    Write-Step "MSVC (cl.exe) encontrado"
} else {
    Write-Warn "cl.exe no encontrado en PATH"
    Write-Host ""
    Write-Host "  MSVC no esta en el PATH. Opciones:" -ForegroundColor Yellow
    Write-Host "    1. Ejecutar este script desde 'Developer PowerShell for VS'" -ForegroundColor Yellow
    Write-Host "    2. Ejecutar primero: " -ForegroundColor Yellow -NoNewline
    Write-Host 'vcvarsall.bat x64' -ForegroundColor White
    Write-Host ""

    # Try to find vcvarsall.bat and load it
    $vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vsWhere) {
        $vsInstallPath = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
        if ($vsInstallPath) {
            $vcvarsall = Join-Path $vsInstallPath "VC\Auxiliary\Build\vcvarsall.bat"
            if (Test-Path $vcvarsall) {
                Write-Host "  Encontrado Visual Studio en: $vsInstallPath" -ForegroundColor Cyan
                Write-Host "  Intentando cargar entorno MSVC..." -ForegroundColor Cyan

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
                    Write-Step "Entorno MSVC cargado correctamente"
                    $hasMSVC = $true
                } else {
                    Write-Fail "No se pudo cargar el entorno MSVC automaticamente"
                    exit 1
                }
            }
        }
    }

    if (-not $hasMSVC) {
        Write-Fail "Visual Studio Build Tools no encontrado"
        Write-Host "  Instalar desde: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Yellow
        Write-Host "  Seleccionar: 'Desarrollo para escritorio con C++'" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Step "Todos los requisitos del sistema estan instalados"
Write-Host ""

# ============================================================
# Paso 1: Crear entorno virtual
# ============================================================

$VENV_DIR = "venv"

if (-not $SkipVenv) {
    if (Test-Path $VENV_DIR) {
        Write-Host "Entorno virtual ya existe en $VENV_DIR" -ForegroundColor Cyan
    } else {
        Write-Host "Creando entorno virtual en $VENV_DIR..." -ForegroundColor Cyan
        & $pythonCmd -m venv $VENV_DIR
        Write-Step "Entorno virtual creado"
    }
}

# Always activate the venv (even with -SkipVenv, we need it active)
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
} else {
    Write-Fail "No se encontro el script de activacion: $activateScript"
    exit 1
}

if (-not $SkipVenv) {
    # Actualizar pip (usar python -m pip para evitar problemas de auto-update en Windows)
    Write-Host "Actualizando pip..." -ForegroundColor Cyan
    & $pythonCmd -m pip install --upgrade pip

    # Instalar dependencias de build
    Write-Host "Instalando dependencias de build..." -ForegroundColor Cyan
    & $pythonCmd -m pip install build pybind11 hatch twine
}

Write-Host ""

# ============================================================
# Paso 2: Compilar dependencias (nats.c, EIPScanner, binding)
# ============================================================

if (-not $SkipBuild) {
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Paso 1: Compilar nats.c" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_nats.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error compilando nats.c"
        exit 1
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Paso 2: Compilar EIPScanner" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_eipscanner.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error compilando EIPScanner"
        exit 1
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Paso 3: Compilar binding Python" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    & $pythonCmd scripts/build_binding.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Fail "Error compilando binding Python"
        exit 1
    }
}

Write-Host ""

# ============================================================
# Paso 3: Crear wheel
# ============================================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Paso 4: Crear wheel" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que las librerias existen
$libDir = "src\eip2nats\lib"
$dlls = Get-ChildItem -Path $libDir -Filter "*.dll" -ErrorAction SilentlyContinue
if (-not $dlls) {
    Write-Fail "No se encontraron DLLs en $libDir"
    exit 1
}

Write-Step "DLLs encontradas:"
$dlls | ForEach-Object { Write-Host "    $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

# Verificar que el modulo Python existe
$pydFiles = Get-ChildItem -Path "src\eip2nats" -Filter "eip_nats_bridge*.pyd" -ErrorAction SilentlyContinue
if (-not $pydFiles) {
    Write-Fail "No se encontro el modulo Python compilado (.pyd) en src\eip2nats\"
    exit 1
}

Write-Step "Modulo Python compilado:"
$pydFiles | ForEach-Object { Write-Host "    $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

# Build wheel
& $pythonCmd -m build --wheel

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Fail "Error creando wheel"
    exit 1
}

Write-Host ""

# ============================================================
# Paso 5: Instalar wheel en el venv
# ============================================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Paso 5: Instalar wheel en el venv" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$wheelFile = Get-ChildItem -Path "dist" -Filter "eip2nats-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($wheelFile) {
    Write-Host "Instalando $($wheelFile.Name) en el entorno virtual..."
    & $pythonCmd -m pip install $wheelFile.FullName --force-reinstall

    if ($LASTEXITCODE -eq 0) {
        Write-Step "Wheel instalado en el entorno virtual"
    } else {
        Write-Fail "Error instalando wheel"
        exit 1
    }
} else {
    Write-Fail "No se encontro el wheel en dist\"
    exit 1
}

Write-Host ""

# ============================================================
# Resumen final
# ============================================================

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Configuracion Completa!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Wheel creado en: dist\" -ForegroundColor Cyan
Get-ChildItem dist\*.whl | ForEach-Object { Write-Host "  $($_.Name) ($([math]::Round($_.Length/1KB, 1)) KB)" }
Write-Host ""

Write-Host "El modulo esta instalado en el entorno virtual" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para usar el proyecto:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  # Activar entorno virtual:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Probar:" -ForegroundColor White
Write-Host "  python -c `"import eip2nats; print(eip2nats.__version__)`"" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Usar:" -ForegroundColor White
Write-Host "  python tu_script.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Desactivar cuando termines:" -ForegroundColor White
Write-Host "  deactivate" -ForegroundColor Gray
Write-Host ""
