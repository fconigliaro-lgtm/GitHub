import os
from dbfread import DBF

# La cartella dove cercare (quella con tutti i DBF)
PATH_ARCHIVI = r"P:\Cdapos\Archivi"

# Cosa stiamo cercando?
TARGET_NAME = "GRANAROLO" # Scrivilo in maiuscolo
TARGET_CODE = "671"       # Il codice che conosciamo

print(f"--- CACCIA AL FILE FORNITORI IN {PATH_ARCHIVI} ---")
print(f"Cerco file che contengano '{TARGET_NAME}' e il codice '{TARGET_CODE}'...\n")

# Lista dei file da ignorare per risparmiare tempo (sappiamo che non sono lì)
SKIP_FILES = ['art.dbf', 'movmag.dbf', 'vendpos.dbf', 'righe_mov.dbf']

found_files = []

# Scansioniamo tutti i file nella cartella
for filename in os.listdir(PATH_ARCHIVI):
    if not filename.lower().endswith('.dbf'):
        continue
    
    if filename.lower() in SKIP_FILES:
        continue

    filepath = os.path.join(PATH_ARCHIVI, filename)
    
    try:
        # Apriamo il file
        table = DBF(filepath, encoding='cp1252', ignore_missing_memofile=True)
        
        # Controlliamo solo i primi 2000 record per file (per fare veloce)
        # Se è l'anagrafica fornitori, Granarolo dovrebbe essere tra i primi
        for i, record in enumerate(table):
            if i > 2000: break 
            
            # Convertiamo tutto il record in una stringa unica per cercare "GRANAROLO"
            record_str = str(record).upper()
            
            if TARGET_NAME in record_str:
                print(f"\n🎯 TROVATO INDIZIO IN: {filename.upper()}")
                print("-" * 40)
                
                # Ora vediamo se c'è anche il codice 671 in qualche campo
                codice_trovato = False
                campo_codice = "???"
                campo_nome = "???"
                
                for key, value in record.items():
                    val_str = str(value).strip()
                    
                    if val_str == TARGET_CODE:
                        codice_trovato = True
                        campo_codice = key
                        print(f"  ✅ Trovato codice {TARGET_CODE} nel campo: {key}")
                    
                    if TARGET_NAME in str(value).upper():
                        campo_nome = key
                        print(f"  ✅ Trovato nome {TARGET_NAME} nel campo: {key}")

                if codice_trovato:
                    print(f"  🔥 BINGO! Questo sembra il file giusto!")
                    print(f"  👉 Usalo così: CODICE='{campo_codice}', NOME='{campo_nome}'")
                    found_files.append(filename)
                    break # Passiamo al prossimo file
                else:
                    print("  ⚠️ Trovato il nome ma non il codice 671 in questo record. Continuo a cercare...")

    except Exception as e:
        # Se un file è corrotto o bloccato, lo saltiamo
        pass

print("\n--- RICERCA COMPLETATA ---")
if found_files:
    print("File candidati trovati:", found_files)
else:
    print("Nessun file ovvio trovato. Controlla se il nome Granarolo è scritto diversamente.")