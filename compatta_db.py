import sqlite3
import os

db_name = 'db.sqlite3'
size_before = os.path.getsize(db_name) / (1024 * 1024)

print(f"📦 Dimensione attuale: {size_before:.2f} MB")
print("⏳ Sto compattando il database (VACUUM)... attendere...")

try:
    conn = sqlite3.connect(db_name)
    conn.execute("VACUUM")
    conn.close()
    
    size_after = os.path.getsize(db_name) / (1024 * 1024)
    print(f"✅ FINITO! Nuova dimensione: {size_after:.2f} MB")
    print(f"📉 Hai risparmiato: {size_before - size_after:.2f} MB")
except Exception as e:
    print(f"❌ Errore: {e}")