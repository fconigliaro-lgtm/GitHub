import os
import django

# --- CONFIGURAZIONE DJANGO (FONDAMENTALE) ---
# Questo dice allo script dove trovare il database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --------------------------------------------

from django.db.models import Sum
from inventory.models import LottoVirtuale
from sales.models import VenditaStorica

# Il codice delle Fettuccine
TARGET_SKU = '155200651'

print(f"--- 🔍 DIAGNOSI ARTICOLO: {TARGET_SKU} ---")

# 1. CONTROLLO VENDITE (Cosa vede il database?)
vendite = VenditaStorica.objects.filter(sku=TARGET_SKU)
tot_vendite = vendite.aggregate(Sum('quantita'))['quantita__sum'] or 0
print(f"1. Totale Vendite trovate nel DB: {tot_vendite}")

# 2. CONTROLLO LOTTI (Cosa c'è sullo scaffale?)
lotti = LottoVirtuale.objects.filter(prodotto__sku=TARGET_SKU).order_by('data_arrivo')
tot_acquistato = lotti.aggregate(Sum('qta_iniziale'))['qta_iniziale__sum'] or 0
tot_residuo = lotti.aggregate(Sum('qta_residua'))['qta_residua__sum'] or 0
print(f"2. Totale Acquistato: {tot_acquistato}")
print(f"3. Attualmente a sistema risultano: {tot_residuo}")

# 3. SIMULAZIONE DEL CALCOLO (Vediamo dove si blocca)
print("\n--- 🧮 SIMULAZIONE CALCOLO ---")
da_scalare = tot_vendite
print(f"Obiettivo: Scalare {da_scalare} pezzi dai lotti...")

for lotto in lotti:
    if da_scalare <= 0:
        print("   -> Vendite esaurite. Stop.")
        break
    
    # Quanto posso togliere da questo lotto?
    qta_disponibile = lotto.qta_iniziale
    sottrazione = min(qta_disponibile, da_scalare)
    
    print(f"   📅 Lotto del {lotto.data_arrivo}: Aveva {qta_disponibile}, tolgo {sottrazione} -> Rimane {qta_disponibile - sottrazione}")
    
    da_scalare -= sottrazione

print(f"\nRISULTATO FINALE: Dovrebbero rimanere da scalare {da_scalare} pezzi.")
if da_scalare > 0:
    print("(Questi sono i pezzi venduti dal magazzino vecchio 2023)")

# 4. FIX FORZATO
print("\nVuoi applicare questa correzione ora? (scrivi SI e premi invio)")
conferma = input("> ")
if conferma.lower() == 'si':
    da_scalare_reale = tot_vendite
    for lotto in lotti:
        if da_scalare_reale <= 0:
            break
        
        # Ripartiamo sempre dalla quantità iniziale per ricalcolare giusto
        qta_lotto_originale = lotto.qta_iniziale 
        
        if qta_lotto_originale > 0:
            decremento = min(qta_lotto_originale, da_scalare_reale)
            
            # Aggiorniamo
            lotto.qta_residua = qta_lotto_originale - decremento
            lotto.save()
            
            da_scalare_reale -= decremento
            
    print("✅ CORREZIONE APPLICATA! Aggiorna la pagina web.")