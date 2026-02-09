from django.core.management.base import BaseCommand
from orders.models import OrdineFornitore, RigaOrdine
from sales.models import VenditaStorica

class Command(BaseCommand):
    help = 'Controlla dove punta la riga dell\'ordine'

    def handle(self, *args, **kwargs):
        TARGET_SKU = "142574647" # Avena
        print(f"--- 🕵️‍♂️ ANALISI RIGA ORDINE: {TARGET_SKU} ---")

        # 1. Prendi l'ultimo ordine creato
        ultimo_ordine = OrdineFornitore.objects.last()
        if not ultimo_ordine:
            print("❌ Nessun ordine trovato!")
            return

        print(f"📋 Analisi Ordine #{ultimo_ordine.id} (del {ultimo_ordine.data_creazione})")

        # 2. Cerca la riga dell'avena
        riga = RigaOrdine.objects.filter(ordine=ultimo_ordine, prodotto__sku=TARGET_SKU).first()
        
        if not riga:
            print(f"❌ In questo ordine NON c'è la riga per SKU {TARGET_SKU}")
            return

        # 3. VERIFICA IL COLLEGAMENTO
        prod_id = riga.prodotto.id
        prod_desc = riga.prodotto.descrizione
        
        print(f"✅ Riga Trovata!")
        print(f"   - Punta al Prodotto ID: {prod_id}")
        print(f"   - Descrizione: {prod_desc}")

        # 4. CONTA LE VENDITE SU *QUESTO* ID SPECIFICO
        vendite = VenditaStorica.objects.filter(prodotto_id=prod_id).count()
        print(f"   - Vendite collegate a questo ID ({prod_id}): {vendite}")

        if vendite == 0:
            print("\n🚨 COLPEVOLE TROVATO: L'ordine punta a un Prodotto ID che ha 0 vendite!")
            print("   Probabilmente i dati sono stati caricati su un ID diverso (es. un duplicato).")
        else:
            print("\n✅ Mistero: L'ordine punta al prodotto giusto e le vendite ci sono.")
            print("   Il problema è quasi sicuramente nel file orders/admin.py (filtri data o logica).")