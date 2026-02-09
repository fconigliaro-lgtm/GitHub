import os
import datetime
from django.core.management.base import BaseCommand
from dbfread import DBF
from inventory.models import Prodotto
from sales.models import AcquistoStorico

class Command(BaseCommand):
    help = 'Importa ACQUISTI da MOVMAG (Fatture F, scartando i riepiloghi FLOC)'

    def handle(self, *args, **kwargs):
        ANNI = [("25", "2025"), ("26", "2026")]

        print("--- 🚛 IMPORTAZIONE ACQUISTI (Solo BLOC/Reali, No FLOC/Riepiloghi) ---")
        
        prodotti_map = {p.sku: p.id for p in Prodotto.objects.all()}
        AcquistoStorico.objects.all().delete()

        totale_importato = 0

        for cartella, anno_label in ANNI:
            path_movmag = rf"P:\Cdapos\{cartella}\MOVMAG.DBF"
            if not os.path.exists(path_movmag): continue

            print(f"📂 Elaborazione Anno {anno_label}...")
            
            try:
                table = DBF(path_movmag, encoding='cp1252', ignore_missing_memofile=True)
                buffer = []
                count = 0
                scartati_floc = 0

                for record in table:
                    tipo = str(record.get('MDM010', '')).strip().upper()
                    
                    # 1. Deve essere di tipo 'F' (Fatture/Contabilità)
                    if tipo != 'F': continue 
                    
                    # 2. FILTRO ANTI-DOPPIONE (Il cuore della modifica)
                    doc_type = str(record.get('MDM040', '')).strip().upper()
                    if doc_type == 'FLOC':
                        scartati_floc += 1
                        continue # SCARTIAMO I RIEPILOGHI DI FINE MESE

                    # 3. Importazione normale
                    sku = str(record.get('MDM110', '')).strip()
                    data = record.get('MDM030')
                    qta = record.get('MDM150')

                    if sku in prodotti_map and isinstance(qta, (int, float)) and qta != 0:
                        if isinstance(data, datetime.date):
                            a = AcquistoStorico(
                                prodotto_id=prodotti_map[sku],
                                data=data,
                                quantita=abs(qta), # Teniamo abs() per ora
                                riferimento=f"{doc_type}:{record.get('MDM140')}"
                            )
                            buffer.append(a)
                            count += 1

                    if len(buffer) >= 5000:
                        AcquistoStorico.objects.bulk_create(buffer)
                        buffer = []

                if buffer:
                    AcquistoStorico.objects.bulk_create(buffer)
                
                print(f"✅ Anno {anno_label}: {count} caricati. (Scartati {scartati_floc} riepiloghi 'FLOC')")
                totale_importato += count

            except Exception as e:
                print(f"❌ Errore: {e}")

        print(f"\n🎉 FINITO! Totale acquisti puliti: {totale_importato}")