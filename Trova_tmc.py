import os
from dbfread import DBF

# PERCORSO CHE MI HAI CONFERMATO
PATH_ART = r"P:\Cdapos\Archivi\art.dbf"

# Prodotti "Spia" presi dalle tue foto
TARGETS = {
    "159725027": 40,  # MASCARPONE -> Cerchiamo il campo che vale 40
    "159751081": 25   # YOGURT -> Cerchiamo il campo che vale 25
}

print(f"--- CACCIA AL TESORO IN {PATH_ART} ---")

if not os.path.exists(PATH_ART):
    print(f"❌ ERRORE: Non trovo il file in {PATH_ART}")
    exit()

try:
    table = DBF(PATH_ART, encoding='cp1252', ignore_missing_memofile=True)
    print("✅ File aperto. Scansione in corso...\n")
    
    trovati_count = 0
    
    for record in table:
        # Qlik lo chiama apr010, ma nel DBF di solito è ART010 o APR010
        # Proviamo a leggere il codice articolo in modo flessibile
        codice = str(record.get('ART010') or record.get('APR010') or '').strip()
        
        if codice in TARGETS:
            valore_atteso = TARGETS[codice]
            print(f"🔎 ANALISI PRODOTTO: {codice} (Deve avere TMC = {valore_atteso})")
            
            candidati = []
            for key, value in record.items():
                # Cerchiamo se il valore del campo è uguale a 40 o 25
                if value == valore_atteso:
                    print(f"  🎯 BINGO! Il campo '{key}' contiene {value}!")
                    candidati.append(key)
                # A volte sono salvati come 40.0
                elif isinstance(value, float) and value == float(valore_atteso):
                    print(f"  🎯 BINGO! Il campo '{key}' contiene {value}!")
                    candidati.append(key)
            
            if not candidati:
                print(f"  ⚠️ Nessun campo trovato con valore {valore_atteso}. Controlla i dati.")
            
            print("-" * 40)
            trovati_count += 1
            if trovati_count >= len(TARGETS):
                break

except Exception as e:
    print(f"❌ Errore: {e}")