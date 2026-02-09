from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from datetime import date
from itertools import chain
from operator import attrgetter

from .models import LottoVirtuale, Prodotto 
from sales.models import VenditaStorica 

# ---------------------------------------------------
# VISTA 1: DASHBOARD PRINCIPALE
# ---------------------------------------------------
def dashboard_scadenze(request):
    oggi = date.today()
    
    # MODIFICA 1: Escludiamo i prodotti che non hanno una data di scadenza calcolata
    # (cioè quelli senza TMC che nell'import abbiamo impostato a None)
    lotti_tutti = LottoVirtuale.objects.filter(
        qta_residua__gt=0
    ).exclude(
        data_scadenza_stimata__isnull=True
    ).order_by('data_scadenza_stimata')[:5000] 

    return render(request, 'dashboard.html', {
        'lotti': lotti_tutti, 
        'today': oggi
    })

# ---------------------------------------------------
# VISTA 2: SCHEDA DETTAGLIO PRODOTTO (Timeline Unificata)
# ---------------------------------------------------
def dettaglio_prodotto(request, sku):
    # 1. Trova il prodotto
    prodotto = get_object_or_404(Prodotto, sku=sku)
    
    # 2. LOGICA DATA (TMC vs SCADENZA per l'header)
    info_data = "N/D"
    etichetta_data = "Data Riferimento"
    
    # Controlliamo se esistono i campi nel modello Prodotto
    if getattr(prodotto, 'scadenza', None):
         info_data = prodotto.scadenza
         etichetta_data = "SCADENZA"
    elif getattr(prodotto, 'tmc', None): # O prodotto.tmc_giorni a seconda del tuo modello
         info_data = prodotto.tmc
         etichetta_data = "TMC (Consigliato)"
    
    # 3. RECUPERO DATI DAL DB
    lotti = LottoVirtuale.objects.filter(prodotto=prodotto)
    vendite = VenditaStorica.objects.filter(sku=sku)
    
    # 4. CALCOLI TOTALI
    tot_acquistato = lotti.aggregate(Sum('qta_iniziale'))['qta_iniziale__sum'] or 0
    tot_venduto = vendite.aggregate(Sum('quantita'))['quantita__sum'] or 0
    rimanenza_teorica = tot_acquistato - tot_venduto
    rimanenza_reale = lotti.aggregate(Sum('qta_residua'))['qta_residua__sum'] or 0

    # 5. PREPARAZIONE TIMELINE (Standardizzazione)
    
    # Gestione Lotti (ACQUISTI)
    for l in lotti:
        l.tipo_movimento = 'ACQUISTO'
        l.data_movimento = l.data_arrivo  # Data per ordinamento
        l.qty_movimento = l.qta_iniziale
        l.is_lotto = True 

    # Gestione Vendite (USCITE)
    for v in vendite:
        v.tipo_movimento = 'VENDITA'
        v.data_movimento = v.data  # Data per ordinamento
        v.qty_movimento = v.quantita
        v.is_lotto = False # <--- CORRETTO (Prima c'era l.is_lotto per errore)

    # 6. UNIONE E ORDINAMENTO
    # chain unisce le liste, sorted ordina per data (reverse=True: data più recente in alto)
    timeline = sorted(chain(lotti, vendite), key=attrgetter('data_movimento'), reverse=True)

    return render(request, 'dettaglio.html', {
        'prodotto': prodotto,
        'timeline': timeline,           # Lista unica movimenti
        'info_data': info_data,         # Data visualizzata in alto
        'etichetta_data': etichetta_data,
        'tot_acquistato': tot_acquistato,
        'tot_venduto': tot_venduto,
        'rimanenza_teorica': rimanenza_teorica,
        'rimanenza_reale': rimanenza_reale
    })