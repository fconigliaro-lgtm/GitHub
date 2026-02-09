@echo off
title AVVIO SERVER SCADENZE (NON CHIUDERE)
color 1F

:: 1. Vai nella cartella
cd C:\erp_scadenze

:: 2. Attiva l'ambiente virtuale
call venv\Scripts\activate

echo.
echo ==============================================
echo   STO APRENDO IL SITO NEL BROWSER...
echo ==============================================
:: Aspetta 2 secondi e apre Chrome/Edge
timeout /t 2 >nul
start http://127.0.0.1:8000/dashboard/

echo.
echo ==============================================
echo   IL SERVER E' ATTIVO!
echo   Lascia questa finestra aperta mentre lavori.
echo ==============================================
echo.

:: 3. Avvia il server (aperto anche per il cellulare)
python manage.py runserver 0.0.0.0:8000