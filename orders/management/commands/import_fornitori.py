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
        scartati_non_fornitori = 0
        
        try:
            table_acf = DBF(PATH_ACF, encoding='cp1252', ignore_missing_memofile=True)
            for record in table_acf:
                # In ACF.DBF ci sono anche clienti/altre anagrafiche.
                # ACF010 = 'F' identifica i FORNITORI (evita sovrapposizioni tipo codice 23).
                tipo = str(record.get('ACF010', '')).strip().upper()
                if tipo != 'F':
                    scartati_non_fornitori += 1
                    continue

                raw_code = record.get('ACF020', '')
                nome = str(record.get('ACF030', '')).strip()
                
                codice_pulito = self.normalize_code(raw_code)
                if codice_pulito and nome:
                    nomi_fornitori[codice_pulito] = nome
            
            self.stdout.write(f"✅ Mappati {len(nomi_fornitori)} nomi da ACF.")
            self.stdout.write(f"ℹ️ Scartati record ACF non-fornitori: {scartati_non_fornitori}")
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

                # --- GESTIONE FORNITORE: codice da APR050 (ART.DBF), nome da ACF ---
                if cod_forn_id in fornitori_cache:
                    fornitore_usato = fornitori_cache[cod_forn_id]
                else:
                    nome_reale = nomi_fornitori.get(cod_forn_id, f"Fornitore {cod_forn_id}")
                    fornitore_usato, created = Fornitore.objects.get_or_create(
                        codice=cod_forn_id,
                        defaults={'nome': nome_reale, 'giorno_consegna_abituale': 'Da definire'}
                    )
                    if created:
                        count_fornitori_creati += 1
                    else:
                        # Aggiorna il nome se è cambiato in ACF
                        if fornitore_usato.nome != nome_reale:
                            fornitore_usato.nome = nome_reale
                            fornitore_usato.save()
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