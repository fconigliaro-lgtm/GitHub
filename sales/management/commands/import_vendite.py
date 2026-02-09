import os
import datetime
from django.core.management.base import BaseCommand
from dbfread import DBF
from inventory.models import Prodotto
from sales.models import VenditaStorica

class Command(BaseCommand):
    help = 'Importa VENDITE UNIFICATE (Scontrini VENDPOS + Scarichi MOVMAG)'

    def handle(self, *args, **kwargs):
        # Configurazione Anni
        ANNI = [
            ("25", "2025"),
            ("26", "2026"),
        ]

        print("--- 🚀 INIZIO IMPORTAZIONE VENDITE TOTALE (Scontrini + Magazzino) ---")
        
        print("Mappatura prodotti in memoria...")
        prodotti_map = {p.sku: p.id for p in Prodotto.objects.all()}
        
        print("🧹 Pulizia database vendite...")
        VenditaStorica.objects.all().delete()

        totale_importato = 0

        for cartella, anno_label in ANNI:
            print(f"\n📂 ELABORAZIONE ANNO {anno_label}...")
            buffer = []
            
            # ---------------------------------------------------------
            # FASE 1: VENDPOS (Scontrini di cassa)
            # ---------------------------------------------------------
            path_vendpos = rf"P:\Cdapos\{cartella}\VENDPOS.DBF"
            if os.path.exists(path_vendpos):
                print(f"   Reading VENDPOS (Scontrini)...")
                try:
                    table = DBF(path_vendpos, encoding='cp1252', ignore_missing_memofile=True)
                    for record in table:
                        sku = str(record.get('V020', '')).strip()
                        data = record.get('V010')
                        qta = record.get('V040')

                        if sku in prodotti_map and isinstance(qta, (int, float)) and qta > 0:
                            if isinstance(data, datetime.date):
                                v = VenditaStorica(
                                    prodotto_id=prodotti_map[sku],
                                    data=data,
                                    quantita=qta,
                                    riferimento=f"SCONTRINO:{record.get('IDRIGA')}"
                                )
                                buffer.append(v)
                except Exception as e:
                    print(f"   ❌ Errore lettura VENDPOS: {e}")
            else:
                print(f"   ⚠️ File VENDPOS non trovato in {path_vendpos}")

            # Salva buffer parziale (per liberare memoria prima di MOVMAG)
            if buffer:
                VenditaStorica.objects.bulk_create(buffer)
                totale_importato += len(buffer)
                print(f"   ✅ Salvati {len(buffer)} scontrini.")
                buffer = [] # Svuota per la prossima fase

            # ---------------------------------------------------------
            # FASE 2: MOVMAG (Movimenti manuali, ddt, scarichi)
            # ---------------------------------------------------------
            path_movmag = rf"P:\Cdapos\{cartella}\MOVMAG.DBF"
            if os.path.exists(path_movmag):
                print(f"   Reading MOVMAG (Movimenti Extra)...")
                try:
                    table = DBF(path_movmag, encoding='cp1252', ignore_missing_memofile=True)
                    count_mov = 0
                    for record in table:
                        tipo = str(record.get('MDM010', '')).strip().upper()
                        
                        # Escludiamo i Fornitori ('F') che vanno negli acquisti
                        if tipo == 'F': continue

                        sku = str(record.get('MDM110', '')).strip()
                        data = record.get('MDM030')
                        qta = record.get('MDM150')

                        if sku in prodotti_map and isinstance(qta, (int, float)) and qta != 0:
                            if isinstance(data, datetime.date):
                                # Usiamo ABS() per convertire gli scarichi negativi in vendite positive
                                qta_reale = abs(qta)
                                
                                v = VenditaStorica(
                                    prodotto_id=prodotti_map[sku],
                                    data=data,
                                    quantita=qta_reale,
                                    riferimento=f"MOV:{tipo}:{record.get('MDM140')}"
                                )
                                buffer.append(v)
                                count_mov += 1
                    
                    # Salva buffer MOVMAG
                    if buffer:
                        VenditaStorica.objects.bulk_create(buffer)
                        totale_importato += len(buffer)
                        print(f"   ✅ Salvati {len(buffer)} movimenti extra.")
                        buffer = []

                except Exception as e:
                    print(f"   ❌ Errore lettura MOVMAG: {e}")
            else:
                print(f"   ⚠️ File MOVMAG non trovato in {path_movmag}")

        print(f"\n🎉 OPERAZIONE COMPLETATA! Totale righe vendite importate: {totale_importato}")