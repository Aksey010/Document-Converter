@echo off
set DJVU_URL=https://djvu.sourceforge.net/
ddjvu --version >nul 2>nul
if errorlevel 1 (
    echo NOTE: djvulibre (ddjvu) not found in PATH.
    echo DJVU conversion will not be available.
    echo Install from %DJVU_URL% for DJVU support.
    echo.
) else (
    echo DJVU tools found: ddjvu
    echo.
)