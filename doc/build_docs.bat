@echo off
REM Build script for libmodbuspy documentation (Windows)

echo Building libmodbuspy documentation...

REM Check if doxygen is installed
where doxygen >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Doxygen is not installed or not in PATH
    echo Please install Doxygen from https://www.doxygen.nl/download.html
    exit /b 1
)

REM Navigate to doc directory
cd /d "%~dp0"

REM Generate documentation
echo Running Doxygen...
doxygen Doxyfile

REM Check if generation was successful
if %ERRORLEVEL% EQU 0 (
    echo Documentation generated successfully!
    echo Open output\libmodbuspy\html\index.html in your web browser to view the documentation
) else (
    echo Error: Documentation generation failed
    exit /b 1
)