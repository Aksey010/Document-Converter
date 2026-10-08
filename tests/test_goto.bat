@echo off
ddjvu --version >nul 2>nul
if errorlevel 1 goto DJVU_NOT_FOUND
echo DJVU tools found: ddjvu
goto END_CHECK

:DJVU_NOT_FOUND
echo NOTE: djvulibre (ddjvu) not found in PATH.
echo DJVU conversion will not be available.
echo Install from https://djvu.sourceforge.net/ for DJVU support.

:END_CHECK