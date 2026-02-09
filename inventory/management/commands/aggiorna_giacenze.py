from django.core.management.base import BaseCommand
from django.db.models import Sum, F
from django.db import transaction
from inventory.models import LottoVirtuale
from sales.models import VenditaStorica

class Command(BaseCommand):
    help = 'Ricalcolo FIFO ad alte prestazioni (In-Memory Bulk Update)'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- INIZIO RICALCOLO VELOCE (TURBO FIFO) ---")

        # 1. RESET ISTANTANEO (1 sola query SQL)
        self.stdout.write("Reset giacenze...")
        LottoVirtuale.objects.all().update(qta_residua=F('qta_iniziale'))

        # 2. CARICAMENTO VENDITE IN MEMORIA (1 sola query SQL)
        # Creiamo un dizionario: { 'SKU_123': 50.0, 'SKU_456': 12.0 }
        self.stdout.write("Caricamento vendite in RAM...")
        vendite_qs = VenditaStorica.objects.values('sku').annotate(tot=Sum('quantita'))
        
        # Mappa SKU -> Quantità totale venduta
        vendite_map = {item['sku']: item['tot'] for item in vendite_qs}

        # 3. CARICAMENTO LOTTI (1 sola query SQL)
        # Prendiamo tutti i lotti ordinati per data (FIFO)
        # select_related ottimizza se serve accedere al prodotto, ma qui ci basta l'ID o SKU del prodotto
        # Assumiamo che LottoVirtuale abbia un campo 'prodotto' che punta al modello Prodotto
        # E che Prodotto abbia il campo 'sku'. 
        self.stdout.write("Elaborazione FIFO in corso...")
        
        # Ottimizzazione: prendiamo solo i lotti dei prodotti che hanno avuto vendite
        sku_con_vendite = list(vendite_map.keys())
        
        # Filtriamo i lotti interessati e li ordiniamo per data
        lotti_qs = LottoVirtuale.objects.filter(
            prodotto__sku__in=sku_con_vendite
        ).select_related('prodotto').order_by('data_arrivo', 'id')

        lotti_da_aggiornare = []
        count_updates = 0

        # 4. CALCOLO PURO (Velocità CPU)
        for lotto in lotti_qs:
            sku = lotto.prodotto.sku
            
            # Se abbiamo ancora vendite da scalare per questo SKU
            if sku in vendite_map and vendite_map[sku] > 0:
                da_scalare = vendite_map[sku]
                residuo_attuale = lotto.qta_residua

                if residuo_attuale > da_scalare:
                    # Il lotto copre tutto, avanza qualcosa
                    lotto.qta_residua = residuo_attuale - da_scalare
                    vendite_map[sku] = 0 # Vendite azzerate per questo SKU
                else:
                    # Il lotto finisce tutto
                    lotto.qta_residua = 0
                    vendite_map[sku] -= residuo_attuale # Riduciamo il debito vendite
                
                # Aggiungiamo alla lista dei lotti da salvare
                lotti_da_aggiornare.append(lotto)
                count_updates += 1

        # 5. SALVATAGGIO DI MASSA (Bulk Update)
        # Salviamo in blocchi da 1000 per non intasare la memoria
        self.stdout.write(f"Salvataggio di {len(lotti_da_aggiornare)} record modificati...")
        
        if lotti_da_aggiornare:
            # bulk_update è MOLTO più veloce di .save() in un ciclo
            LottoVirtuale.objects.bulk_update(lotti_da_aggiornare, ['qta_residua'], batch_size=1000)

        self.stdout.write(self.style.SUCCESS("--- OPERAZIONE COMPLETATA ---"))