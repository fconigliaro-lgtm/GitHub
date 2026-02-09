@echo off
title Pubblica su GitHub
cd /d c:\erp_scadenze

echo.
echo === Pubblicazione modifiche su GitHub ===
echo.

git add .
git status
echo.
set /p MESSAGGIO="Messaggio commit (es: Fix dashboard): "
if "%MESSAGGIO%"=="" set MESSAGGIO=Aggiornamento
git commit -m "%MESSAGGIO%"
git push

echo.
echo === Fatto. Ora su PythonAnywhere: git pull e Reload Web. ===
pause
