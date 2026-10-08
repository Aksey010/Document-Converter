@echo off
cd /d "%~dp0"
title Document Converter

echo  ============================================
echo     Document Converter - Starting Application
echo  ============================================
echo.

REM Check if Python is available (prefer py launcher)
where /q py
if errorlevel 1 (
    where /q python
    if errorlevel 1 (
        echo ERROR: Python not found in PATH.
        echo Install Python 3.9+ from https://python.org
        echo.
        pause
        exit /b 1
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

REM Check Python version
%PY_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.9 or higher required.
    %PY_CMD% --version 2>nul
    echo.
    pause
    exit /b 1
)

echo Python found:
%PY_CMD% --version 2>nul
echo.

REM Create virtual environment if not exists
if not exist venv_converter\Scripts\python.exe (
    echo First run: creating virtual environment...
    %PY_CMD% -m venv venv_converter
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Upgrading pip...
    venv_converter\Scripts\python.exe -m pip install -q --upgrade pip
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    venv_converter\Scripts\python.exe -m pip install -q -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        echo Check your internet connection and requirements.txt
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
    echo.
) else (
    echo Virtual environment found.
    echo.
)

REM Check for DJVU tools
ddjvu --version >nul 2>nul
if errorlevel 1 goto DJVU_NOT_FOUND
echo DJVU tools found: ddjvu
echo.
goto DJVU_CHECK_END

:DJVU_NOT_FOUND
echo NOTE: djvulibre (ddjvu) not found in PATH.
echo DJVU conversion will not be available.
echo Install from https://djvu.sourceforge.net/ for DJVU support.
echo.

:DJVU_CHECK_END

REM Check for wkhtmltopdf (for HTML to PDF)
wkhtmltopdf --version >nul 2>nul
if errorlevel 1 goto WKHTML_NOT_FOUND
echo wkhtmltopdf found - HTML to PDF enabled
echo.
goto WKHTML_CHECK_END

:WKHTML_NOT_FOUND
echo NOTE: wkhtmltopdf not found in PATH.
echo HTML to PDF will use fallback (text extraction only).
echo Install from https://wkhtmltopdf.org/ for full HTML to PDF support.
echo.

:WKHTML_CHECK_END

REM Start the web server
echo Starting Document Converter web panel...
echo Panel will be available: http://localhost:8080
echo.
echo Press Ctrl+C to stop
echo  ============================================
echo.

REM Open browser after a short delay (server needs time to start)
start /b "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8080"

venv_converter\Scripts\python.exe main.py

echo.
echo Application stopped.
pause