import csv
import os
import zipfile
import datetime
import requests # <--- NUOVA LIBRERIA
from dbfread import DBF

# --- CONFIGURAZIONE ---
PERCORSO_DATI = r"P:\Cdapos"
ANNI_DA_ESPORTARE = ["26"] # Mettiamo solo l'anno corrente per essere veloci
OUTPUT_ZIP = "dati_light.zip"

# DATI SITO (Metti i tuoi!)
URL_SITO = "https://federicoconigliaro.pythonanywhere.com/api/aggiorna/"
TOKEN_SEGRETO = "SuperSegreto123!" # Deve essere uguale a settings.py

def scrivi_csv(dbf_path, csv_path, campi, filtro_anno=False):
    if not os.path.exists(dbf_path): return False
    print(f"   Elaboro: {os.path.basename(dbf_path)}...")
    try:
        table = DBF(dbf_path, encoding='cp1252', ignore_missing_memofile=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(campi)
            for r in table:
                row = []
                for c in campi:
                    val = r.get(c)
                    if isinstance(val, datetime.date): val = val.strftime('%Y-%m-%d')
                    row.append(val)
                writer.writerow(row)
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    print("🚀 1. ESTRAZIONE DATI...")
    files = []

    # Archivi
    path_art = os.path.join(PERCORSO_DATI, "Archivi", "ART.DBF")
    path_acf = os.path.join(PERCORSO_DATI, "Archivi", "ACF.DBF")
    
    # Gestione maiuscole/minuscole
    if not os.path.exists(path_art): path_art = path_art.lower()
    if not os.path.exists(path_acf): path_acf = path_acf.lower()

    if scrivi_csv(path_acf, "acf.csv", ["ACF020", "ACF030"]): files.append("acf.csv")
    if scrivi_csv(path_art, "art.csv", ["ART010", "APR010", "APR050", "APR200", "APR080"]): files.append("art.csv")

    # Vendite Anno Corrente
    for anno in ANNI_DA_ESPORTARE:
        path_vend = os.path.join(PERCORSO_DATI, anno, "VENDPOS.DBF")
        path_mov = os.path.join(PERCORSO_DATI, anno, "MOVMAG.DBF")
        
        if scrivi_csv(path_vend, f"vendite_{anno}.csv", ["V010", "V020", "V040", "IDRIGA"]):
            files.append(f"vendite_{anno}.csv")
        if scrivi_csv(path_mov, f"movimenti_{anno}.csv", ["MDM010", "MDM030", "MDM110", "MDM140", "MDM150"]):
            files.append(f"movimenti_{anno}.csv")

    print("\n📦 2. CREAZIONE ZIP...")
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file)
            os.remove(file)

    print("\n📡 3. INVIO AL SITO...")
    try:
        with open(OUTPUT_ZIP, 'rb') as f:
            risposta = requests.post(
                URL_SITO, 
                files={'file_zip': f},
                headers={'Authorization': TOKEN_SEGRETO}
            )
        
        if risposta.status_code == 200:
            print("✅ SUCCESSO! Il sito ha risposto:", risposta.json()['message'])
        else:
            print("❌ ERRORE DAL SITO:", risposta.text)
            
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
    
    # Pulizia finale (opzionale, se vuoi tenere lo zip togli questa riga)
    # os.remove(OUTPUT_ZIP)

if __name__ == "__main__":
    main()