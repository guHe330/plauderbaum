@echo off
setlocal
cd /d "%~dp0"
title Plauderbaum

if not exist ".venv\Scripts\python.exe" (
    echo First start: setting up. This takes a minute...
    py -3 -m venv .venv
    if errorlevel 1 goto fail
    ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check --require-hashes -r requirements.txt
    if errorlevel 1 goto fail
)

".venv\Scripts\python.exe" -m tutor
if errorlevel 1 pause
exit /b

:fail
echo.
echo Setup failed. Delete the .venv folder and try again.
pause
exit /b 1
