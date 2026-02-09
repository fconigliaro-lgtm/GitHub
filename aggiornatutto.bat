@echo off
:: =============================================================
:: SCRIPT AUTOMATICO AGGIORNAMENTO ERP - SUPERMERCATI CONIGLIARO
:: =============================================================

:: 1. Spostamento nella cartella del progetto
cd /d C:\erp_scadenze

:: 2. Setup Log
set LOGFILE=log_aggiornamento.txt
echo. >> %LOGFILE%
echo ------------------------------------------------------------- >> %LOGFILE%
echo [START] Inizio procedura: %date% %time% >> %LOGFILE%

:: 3. ESECUZIONE COMANDI DJANGO
:: Usiamo il python del virtual environment per sicurezza (venv\Scripts\python.exe)

:: A. Importazione Anagrafica Prodotti (Base)
echo [1/6] Importazione Prodotti (ART.DBF)... >> %LOGFILE%
venv\Scripts\python.exe manage.py import_dbf >> %LOGFILE% 2>&1

:: B. Aggiornamento Confezioni (Pezzi per Cartone)
echo [2/6] Aggiornamento Pezzi x Cartone... >> %LOGFILE%
venv\Scripts\python.exe manage.py update_pz_cartone >> %LOGFILE% 2>&1

:: C. Importazione Fornitori e Listini
echo [3/6] Importazione Fornitori e Listini... >> %LOGFILE%
venv\Scripts\python.exe manage.py import_fornitori >> %LOGFILE% 2>&1

:: D. Importazione Vendite Storiche
echo [4/6] Importazione Vendite... >> %LOGFILE%
venv\Scripts\python.exe manage.py import_vendite >> %LOGFILE% 2>&1

:: E. Importazione Acquisti Storici
echo [5/6] Importazione Acquisti... >> %LOGFILE%
venv\Scripts\python.exe manage.py import_acquisti >> %LOGFILE% 2>&1

:: F. Ricalcolo Giacenze (Importante per l'ordine automatico!)
echo [6/6] Ricalcolo Giacenze (Acquisti - Vendite)... >> %LOGFILE%
venv\Scripts\python.exe manage.py aggiorna_giacenze >> %LOGFILE% 2>&1

:: 4. Chiusura
echo [END] Procedura completata: %time% >> %LOGFILE%
echo ------------------------------------------------------------- >> %LOGFILE%

:: G. Pulizia Automatica (Disabilita roba vecchia dal 2025)
echo [7/7] Pulizia Prodotti/Fornitori Inattivi... >> %LOGFILE%
venv\Scripts\python.exe manage.py pulizia_automatica >> %LOGFILE% 2>&1

:: Se lo lanci a mano, questo ti permette di vedere se ha finito.
:: Se pianificato, non da fastidio.
timeout /t 5
exit