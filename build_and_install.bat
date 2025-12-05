@echo off
REM ============================================================================
REM Script de Compilación e Instalación de DaveAgent
REM ============================================================================
REM Este script automatiza:
REM 1. Limpieza de builds anteriores
REM 2. Compilación del paquete
REM 3. Instalación del paquete
REM 4. Verificación de la instalación
REM ============================================================================

echo.
echo ========================================
echo  DaveAgent - Build and Install Script
echo ========================================
echo.

REM Guardar el directorio actual
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Colores para Windows (opcional, requiere ANSI support)
echo [36mPaso 1: Limpiando builds anteriores...[0m
echo.

REM Limpiar directorios de build anteriores
if exist "build\" (
    echo Eliminando directorio build/...
    rmdir /s /q "build"
)

if exist "dist\" (
    echo Eliminando directorio dist/...
    rmdir /s /q "dist"
)

if exist "*.egg-info\" (
    echo Eliminando archivos .egg-info...
    for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
)

if exist "src\*.egg-info\" (
    echo Eliminando archivos .egg-info en src/...
    for /d %%i in (src\*.egg-info) do rmdir /s /q "%%i"
)

echo [32m✓ Limpieza completada[0m
echo.

REM ============================================================================
echo [36mPaso 2: Verificando dependencias...[0m
echo.

REM Verificar si build está instalado
python -m pip show build >nul 2>&1
if errorlevel 1 (
    echo [33mInstalando python build...[0m
    python -m pip install build
    if errorlevel 1 (
        echo [31m✗ Error: No se pudo instalar build[0m
        pause
        exit /b 1
    )
) else (
    echo [32m✓ build ya está instalado[0m
)

echo.

REM ============================================================================
echo [36mPaso 3: Compilando el paquete...[0m
echo.
echo Esto puede tomar un momento...
echo.

python -m build
if errorlevel 1 (
    echo.
    echo [31m✗ Error: La compilación falló[0m
    echo.
    pause
    exit /b 1
)

echo.
echo [32m✓ Compilación exitosa[0m
echo.

REM ============================================================================
echo [36mPaso 4: Mostrando archivos compilados...[0m
echo.

if exist "dist\" (
    dir dist\*.whl dist\*.tar.gz 2>nul
    echo.
) else (
    echo [31m✗ Error: No se encontró el directorio dist/[0m
    pause
    exit /b 1
)

REM ============================================================================
echo [36mPaso 5: Instalando el paquete...[0m
echo.

REM Buscar el archivo .whl más reciente
for /f "delims=" %%i in ('dir /b /od dist\*.whl') do set "WHEEL_FILE=%%i"

if not defined WHEEL_FILE (
    echo [31m✗ Error: No se encontró archivo .whl en dist/[0m
    pause
    exit /b 1
)

echo Instalando %WHEEL_FILE%...
echo.

python -m pip install "dist\%WHEEL_FILE%" --force-reinstall
if errorlevel 1 (
    echo.
    echo [31m✗ Error: La instalación falló[0m
    echo.
    pause
    exit /b 1
)

echo.
echo [32m✓ Instalación completada[0m
echo.

REM ============================================================================
echo [36mPaso 6: Verificando la instalación...[0m
echo.

REM Verificar que daveagent-cli está instalado
python -m pip show daveagent-cli >nul 2>&1
if errorlevel 1 (
    echo [31m✗ Error: daveagent-cli no está instalado correctamente[0m
    pause
    exit /b 1
)

echo [32m✓ daveagent-cli está instalado[0m
echo.

REM Mostrar información del paquete
echo Información del paquete:
echo ------------------------
python -m pip show daveagent-cli | findstr "Name: Version: Location:"
echo.

REM Verificar que el comando CLI funciona
echo Verificando comando CLI...
daveagent --version >nul 2>&1
if errorlevel 1 (
    echo [33m⚠ Advertencia: El comando 'daveagent' no está disponible en PATH[0m
    echo   Puedes usar: python -m src.cli
) else (
    echo [32m✓ Comando 'daveagent' está disponible[0m
    echo.
    echo Ejecutando: daveagent --version
    daveagent --version
)

echo.

REM ============================================================================
echo.
echo [32m========================================[0m
echo [32m  ✓ PROCESO COMPLETADO EXITOSAMENTE[0m
echo [32m========================================[0m
echo.
echo Archivos generados:
echo   - dist\%WHEEL_FILE%
echo   - dist\*.tar.gz
echo.
echo Para usar:
echo   1. Comando directo: daveagent
echo   2. Como módulo: python -m src.cli
echo   3. Desde Python: python src/main.py
echo.
echo Para desinstalar:
echo   pip uninstall daveagent-cli
echo.

pause
