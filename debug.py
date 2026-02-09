import os
import django
import sys
import re
import datetime

# --- CONFIGURAZIONE ---
sys.path.append(os.getcwd())
try:
    with open('manage.py', 'r') as f:
        content = f.read()
        match = re.search(r"['\"]DJANGO_SETTINGS_MODULE['\"],\s*['\"](.+?)['\"]", content)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', match.group(1) if match else 'erp_scadenze.settings')
    django.setup()
except:
    sys.exit("❌ Errore config.")

from dbfread import DBF

# --- ANALISI CHIRURGICA OTTOBRE 2025 ---
TARGET_SKU = "900074330" 
FILE_TARGET = r"P:\Cdapos\25\MOVMAG.DBF"

print(f"--- 🔬 AUTOPSIA OTTOBRE 2025 (SKU: {TARGET_SKU}) ---")
print(f"{'DATA':<12} | {'TIPO':<4} | {'QTA':<5} | {'CAUSALE (020)':<13} | {'DOC (040)':<10} | {'RIFERIMENTO (140)'}")
print("-" * 100)

if os.path.exists(FILE_TARGET):
    table = DBF(FILE_TARGET, encoding='cp1252', ignore_missing_memofile=True)
    
    count_valid = 0
    count_ghost = 0
    
    for record in table:
        sku = str(record.get('MDM110', '')).strip()
        if sku != TARGET_SKU: continue

        tipo = str(record.get('MDM010', '')).strip().upper()
        if tipo != 'F': continue # Solo Fatture

        data = record.get('MDM030')
        if not isinstance(data, datetime.date): continue
        
        # FILTRIAMO SOLO OTTOBRE 2025 PER CAPIRE IL PROBLEMA
        if data.month != 10 or data.year != 2025: continue

        qta = record.get('MDM150')
        causale = str(record.get('MDM020', '')) # Scommetto che qui c'è la differenza!
        doc = str(record.get('MDM040', ''))
        desc = str(record.get('MDM140', ''))[:40] # Tagliamo se troppo lunga

        # Stampiamo tutto
        print(f"{str(data):<12} | {tipo:<4} | {qta:<5} | {causale:<13} | {doc:<10} | {desc}")