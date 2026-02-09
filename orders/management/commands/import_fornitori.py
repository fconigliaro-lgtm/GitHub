import os
from django.core.management.base import BaseCommand
from django.db import transaction
from dbfread import DBF
from inventory.models import Prodotto
from orders.models import Fornitore, ListinoFornitore

class Command(BaseCommand):
    help = 'Importa Fornitori e Listini direttamente con i nomi corretti da ACF.DBF'

    def normalize_code(self, val):
        """Pulisce il codice: trasforma 671.0 o ' 671 ' in '671'"""
        try:
            if not val: return ""
            return str(int(float(val)))
        except:
            return str(val).strip()

    def handle(self, *args, **kwargs):
        PATH_ART = r"P:\Cdapos\Archivi\art.dbf"
        PATH_ACF = r"P:\Cdapos\Archivi\acf.dbf"

        if not os.path.exists(PATH_ART) or not os.path.exists(PATH_ACF):
            self.stdout.write(self.style.ERROR("File non trovati."))
            return

        # 1. CARICAMENTO MAPPA NOMI (ACF)
        self.stdout.write("Lettura anagrafica fornitori (ACF.DBF)...")
        nomi_fornitori = {} 
        
        try:
            table_acf = DBF(PATH_ACF, encoding='cp1252', ignore_missing_memofile=True)
            for record in table_acf:
                raw_code = record.get('ACF020', '')
                nome = str(record.get('ACF030', '')).strip()
                
                codice_pulito = self.normalize_code(raw_code)
                if codice_pulito and nome:
                    nomi_fornitori[codice_pulito] = nome
            
            self.stdout.write(f"✅ Mappati {len(nomi_fornitori)} nomi da ACF.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Errore lettura ACF: {e}"))
            return

        # 2. CARICAMENTO PRODOTTI ESISTENTI
        prodotti_db = {p.sku: p for p in Prodotto.objects.all()}
        
        # 3. IMPORTAZIONE (ART)
        self.stdout.write(f"Inizio importazione da {PATH_ART}...")
        
        table_art = DBF(PATH_ART, encoding='cp1252', ignore_missing_memofile=True)
        
        count_fornitori_creati = 0
        count_listini = 0
        processed = 0
        
        # Cache: { '671': oggetto_fornitore_granarolo }
        fornitori_cache = {} 

        with transaction.atomic():
            for record in table_art:
                processed += 1
                if processed % 2000 == 0:
                    self.stdout.write(f"\rAnalizzati {processed} record...", ending="")

                # Filtro Categoria
                cat_stat = str(record.get('APR080', '')).strip().upper()
                if not (cat_stat.startswith('200') or cat_stat.startswith('LOC')):
                    continue 

                sku = str(record.get('ART010') or record.get('APR010') or '').strip()
                raw_cod_forn = record.get('APR050', '')
                rif_forn = str(record.get('APR200', '')).strip()

                if not sku or sku not in prodotti_db: continue
                
                cod_forn_id = self.normalize_code(raw_cod_forn)
                if not cod_forn_id or cod_forn_id == '0': continue

                # --- GESTIONE FORNITORE (LOGICA CORRETTA) ---
                if cod_forn_id in fornitori_cache:
                    fornitore_usato = fornitori_cache[cod_forn_id]
                else:
                    # Troviamo il nome vero (o usiamo il codice come fallback)
                    nome_reale = nomi_fornitori.get(cod_forn_id, f"Fornitore {cod_forn_id}")
                    
                    # Cerca o Crea usando DIRETTAMENTE il nome reale
                    fornitore_usato, created = Fornitore.objects.get_or_create(
                        nome=nome_reale,
                        defaults={'giorno_consegna_abituale': 'Da definire'}
                    )
                    
                    if created:
                        count_fornitori_creati += 1
                    
                    fornitori_cache[cod_forn_id] = fornitore_usato

                # --- COLLEGAMENTO LISTINO ---
                prodotto_usato = prodotti_db[sku]
                
                ListinoFornitore.objects.update_or_create(
                    fornitore=fornitore_usato,
                    prodotto=prodotto_usato,
                    defaults={'codice_articolo_fornitore': rif_forn}
                )
                count_listini += 1

        print() 
        self.stdout.write(self.style.SUCCESS(f"✅ IMPORTAZIONE COMPLETATA SENZA ERRORI!"))
        self.stdout.write(f"- Fornitori Totali nel DB: {Fornitore.objects.count()} (Nuovi: {count_fornitori_creati})")
        self.stdout.write(f"- Prodotti collegati: {count_listini}")