import os
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.core.management import call_command
from dbfread import DBF
from inventory.models import Prodotto, LottoVirtuale
from sales.models import VenditaStorica

class Command(BaseCommand):
    help = 'RESET TOTALE: Cancella tutto e ricarica (Usa UNA TANTUM per manutenzione)'

    def handle(self, *args, **kwargs):
        PATH_ARCHIVI = r"P:\CDAPOS\ARCHIVI" 
        PATH_ANNI = r"P:\CDAPOS"
        FILE_ACQUISTI = "movmag.dbf"
        FILE_VENDITE = "vendpos.dbf"
        
        DATE_DA_ESCLUDERE = [date(2025, 1, 6), date(2024, 1, 1)]

        self.stdout.write(self.style.WARNING("--- ☢️ AVVIO RESET NUCLEARE DEL DATABASE ☢️ ---"))

        # 1. CANCELLAZIONE TOTALE
        self.stdout.write("Cancellazione totale dati...", ending="")
        LottoVirtuale.objects.all().delete()
        VenditaStorica.objects.all().delete()
        self.stdout.write(" FATTO.")

        sku_map = {p.sku: (p.id, p.tmc_giorni) for p in Prodotto.objects.all()}
        anni = ['24', '25', '26'] 
        
        for anno in anni:
            path_base_anno = os.path.join(PATH_ANNI, anno)
            if not os.path.exists(path_base_anno): continue

            self.stdout.write(f"\n--- Ricaricamento FULL ANNO 20{anno} ---")
            anno_completo = int("20" + anno)

            # A) ACQUISTI
            path_movmag = os.path.join(path_base_anno, FILE_ACQUISTI)
            if os.path.exists(path_movmag):
                try:
                    table = DBF(path_movmag, encoding='cp1252', ignore_missing_memofile=True)
                    batch = []
                    count = 0
                    for record in table:
                        if str(record.get('MDM010', '')).strip() != 'F': continue 
                        data_mov = record.get('MDM030')
                        if not data_mov or data_mov in DATE_DA_ESCLUDERE: continue

                        codice_prod = str(record.get('MDM110', '')).strip() 
                        qta = record.get('MDM1501')                         
                        
                        if codice_prod and qta and qta > 0 and codice_prod in sku_map:
                            prod_id, tmc_giorni = sku_map[codice_prod]
                            
                            # LOGICA CORRETTA (Niente 30 giorni default)
                            scadenza_calc = None
                            if tmc_giorni and tmc_giorni > 0:
                                scadenza_calc = data_mov + timedelta(days=tmc_giorni)

                            batch.append(LottoVirtuale(prodotto_id=prod_id, data_arrivo=data_mov, qta_iniziale=qta, qta_residua=qta, data_scadenza_stimata=scadenza_calc))
                            count += 1
                        if len(batch) >= 5000:
                            LottoVirtuale.objects.bulk_create(batch); batch = []
                            self.stdout.write(".", ending="")
                    if batch: LottoVirtuale.objects.bulk_create(batch)
                    self.stdout.write(f" Fatto ({count} acquisti).")
                except Exception as e: self.stdout.write(str(e))
            
            # B) VENDITE
            path_vendpos = os.path.join(path_base_anno, FILE_VENDITE)
            if os.path.exists(path_vendpos):
                try:
                    table = DBF(path_vendpos, encoding='cp1252', ignore_missing_memofile=True)
                    batch = []
                    count = 0
                    for record in table:
                        codice = str(record.get('V020', '')).strip()
                        if codice and codice in sku_map:
                            batch.append(VenditaStorica(sku=codice, data_vendita=record.get('V010'), quantita=record.get('V040'), anno_riferimento=anno_completo))
                            count += 1
                        if len(batch) >= 10000:
                            VenditaStorica.objects.bulk_create(batch); batch = []
                            self.stdout.write(".", ending="")
                    if batch: VenditaStorica.objects.bulk_create(batch)
                    self.stdout.write(f" Fatto ({count} vendite).")
                except Exception as e: self.stdout.write(str(e))

        self.stdout.write("\nReset terminato. Avvio calcolo giacenze...")
        call_command('aggiorna_giacenze')