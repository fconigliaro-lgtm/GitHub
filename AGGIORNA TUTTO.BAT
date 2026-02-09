@echo off
title AGGIORNAMENTO MAGAZZINO (Importa + Calcola + Pulisci)
color 0A

echo ================================================
echo   AVVIO PROCEDURA DI AGGIORNAMENTO DATI
echo ================================================
echo.

:: 1. Entra nella cartella del progetto
cd C:\erp_scadenze

:: 2. Attiva il "cervello" di Python
call venv\Scripts\activate

echo ------------------------------------------------
echo 1. IMPORTAZIONE NUOVI DATI (Fatture e Vendite)
echo ------------------------------------------------
python manage.py import_dbf

echo.
echo ------------------------------------------------
echo 2. CALCOLO GIACENZE (Scarico Vendite)
echo ------------------------------------------------
python manage.py aggiorna_giacenze

echo.
echo ------------------------------------------------
echo 3. PULIZIA DATI VECCHI (Fantasmi)
echo ------------------------------------------------
python manage.py pulisci_fantasmi

echo.
echo ================================================
echo   AGGIORNAMENTO COMPLETATO CON SUCCESSO!
echo   Ora puoi aggiornare la pagina web (F5).
echo ================================================
pause