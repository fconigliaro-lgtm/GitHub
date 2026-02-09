@echo off
cd /d C:\erp_scadenze

echo ==============================================
echo   GENERAZIONE MAPPA PROGETTO IN CORSO...
echo ==============================================

echo MAPPA COMPLETA DEL PROGETTO > mappa_progetto.txt
echo Generata il %date% alle %time% >> mappa_progetto.txt
echo. >> mappa_progetto.txt

:: 1. Fa l'albero di tutte le cartelle e file
tree /f /a >> mappa_progetto.txt

echo. >> mappa_progetto.txt
echo ============================================== >> mappa_progetto.txt
echo   ELENCO COMANDI GESTIONALI (MANAGEMENT) >> mappa_progetto.txt
echo ============================================== >> mappa_progetto.txt
echo. >> mappa_progetto.txt

:: 2. Cerca specificamente i file .py dentro le cartelle 'commands'
:: Questo ci serve per trovare i nomi esatti degli script di importazione
dir /s /b "*management\commands\*.py" >> mappa_progetto.txt

echo.
echo ==============================================
echo   FATTO!
echo   Il file "mappa_progetto.txt" e' stato creato.
echo   Aprilo, copia il contenuto e incollalo in chat.
echo ==============================================
pause