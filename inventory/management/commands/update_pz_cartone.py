import os
from django.core.management.base import BaseCommand
from dbfread import DBF
from inventory.models import Prodotto

class Command(BaseCommand):
    help = 'Aggiorna Pezzi x Cartone e Giacenza da ART.DBF (Ricerca Automatica)'

    def handle(self, *args, **kwargs):
        # ELENCO POSSIBILI PERCORSI (L'ordine conta: usa il primo che trova)
        POSSIBLE_PATHS = [
            r"P:\Cdapos\ARCHIVI\ART.DBF",   # <--- ECCOLO! Corretto come mi hai detto
            r"P:\Cdapos\ART.DBF",           
            r"P:\Cdapos\DATI\ART.DBF",      
            r"P:\Cdapos\26\ART.DBF",        
        ]

        target_path = None
        for path in POSSIBLE_PATHS:
            if os.path.exists(path):
                target_path = path
                break
        
        if not target_path:
            print("❌ ERRORE: Non ho trovato il file ART.DBF in nessuna di queste cartelle:")
            for p in POSSIBLE_PATHS:
                print(f"   - {p}")
            return

        print(f"--- 🚀 INIZIO AGGIORNAMENTO DATI DA: {target_path} ---")

        # Carichiamo i prodotti in memoria
        print("📥 Caricamento database Django in memoria...")
        prodotti_db = {p.sku: p for p in Prodotto.objects.all()}
        print(f"📦 Prodotti nel sistema: {len(prodotti_db)}")

        aggiornati = 0
        totale_scan = 0
        buffer_update = []

        try:
            table = DBF(target_path, encoding='cp1252', ignore_missing_memofile=True)
            
            print("🔄 Lettura ART.DBF e aggiornamento...")
            for record in table:
                totale_scan += 1
                
                # MAPPATURA CAMPI
                sku = str(record.get('ART010', '')).strip()
                pz_cartone = record.get('APR110')
                giacenza = record.get('ART350') 

                # Se il prodotto esiste nel nostro DB
                if sku in prodotti_db:
                    p = prodotti_db[sku]
                    changed = False

                    # 1. Aggiorna Pezzi per Cartone
                    if isinstance(pz_cartone, (int, float)) and pz_cartone > 0:
                        nuovo_pz = int(pz_cartone)
                        if p.pezzi_per_cartone != nuovo_pz:
                            p.pezzi_per_cartone = nuovo_pz
                            changed = True

                    # 2. Aggiorna Giacenza
                    if isinstance(giacenza, (int, float)):
                        nuova_giac = int(giacenza)
                        if p.giacenza != nuova_giac:
                            p.giacenza = nuova_giac
                            changed = True

                    if changed:
                        buffer_update.append(p)
                        aggiornati += 1

                    # Salviamo a blocchi di 1000
                    if len(buffer_update) >= 1000:
                        Prodotto.objects.bulk_update(buffer_update, ['pezzi_per_cartone', 'giacenza'])
                        buffer_update = []
                        print(f"\r   ⏳ Aggiornati {aggiornati} prodotti...", end="")

            # Salvataggio finale residui
            if buffer_update:
                Prodotto.objects.bulk_update(buffer_update, ['pezzi_per_cartone', 'giacenza'])

            print(f"\n\n📊 STATISTICHE FINALI:")
            print(f"   - File utilizzato: {target_path}")
            print(f"   - Righe lette nel DBF: {totale_scan}")
            print(f"   - Prodotti aggiornati: {aggiornati}")
            print(f"   - Prodotti invariati:  {len(prodotti_db) - aggiornati}")
            print("✅ OPERAZIONE COMPLETATA!")

        except Exception as e:
            print(f"\n❌ ERRORE CRITICO DURANTE LA LETTURA: {e}")