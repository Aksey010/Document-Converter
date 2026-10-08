@echo off
ddjvu --version >nul 2>nul
if errorlevel 1 (
    echo NOTE: not found
    echo.
) else (
    echo FOUND
    echo.
)