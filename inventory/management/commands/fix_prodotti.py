from django.core.management.base import BaseCommand
from dbfread import DBF
from inventory.models import Prodotto
import os

class Command(BaseCommand):
    help = 'Aggiorna i TMC dei prodotti leggendo il campo APR1070'

    def handle(self, *args, **kwargs):
        PATH_ART = r"P:\Cdapos\Archivi\art.dbf" 
        CAMPO_TMC = 'APR1070' 
        CAMPI_SKU = ['ART010', 'APR010']

        self.stdout.write(f"--- AGGIORNAMENTO PRODOTTI DA {CAMPO_TMC} ---")
        
        if not os.path.exists(PATH_ART):
            self.stdout.write(self.style.ERROR("File art.dbf non trovato!"))
            return

        table = DBF(PATH_ART, encoding='cp1252', ignore_missing_memofile=True)
        updates = []
        prodotti_map = {p.sku: p for p in Prodotto.objects.all()} 
        count = 0
        
        self.stdout.write("Lettura file ART.DBF in corso...")

        for record in table:
            sku = None
            for campo in CAMPI_SKU:
                val = str(record.get(campo, '')).strip()
                if val:
                    sku = val
                    break
            
            if sku and sku in prodotti_map:
                prodotto = prodotti_map[sku]
                giorni_reali = record.get(CAMPO_TMC)
                
                # --- CORREZIONE QUI SOTTO (prima c'era days_reali) ---
                if giorni_reali and isinstance(giorni_reali, (int, float)) and giorni_reali > 0:
                    nuovo_tmc = int(giorni_reali)
                else:
                    nuovo_tmc = 0 
                
                if prodotto.tmc_giorni != nuovo_tmc:
                    prodotto.tmc_giorni = nuovo_tmc
                    updates.append(prodotto)
                    count += 1
            
            if len(updates) >= 1000:
                Prodotto.objects.bulk_update(updates, ['tmc_giorni'])
                updates = []
                self.stdout.write(".", ending="")

        if updates:
            Prodotto.objects.bulk_update(updates, ['tmc_giorni'])
        
        self.stdout.write(self.style.SUCCESS(f"\nFATTO! Aggiornati {count} prodotti."))