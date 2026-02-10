# Proposta: Griglia scaffale (ordine multi-fornitore unificato)

## Obiettivo
Quando generi un ordine per più fornitori (es. Barilla 23 + Barilla 8314), vedere **in una sola griglia** tutti i prodotti da ordinare, nello stesso ordine in cui stanno a scaffale, e poter modificare le quantità da lì. I dati restano salvati come ordini distinti (uno per fornitore) per invio email e gestione.

---

## Flusso utente

1. In **Fornitori** selezioni due o più fornitori (es. Barilla 23, Barilla 8314) e clicchi **"⚡ Genera Bozza Ordine (Auto)"**.
2. Il sistema crea **un ordine per fornitore** (come oggi).
3. Invece di andare alla lista ordini, si apre una **vista "Griglia scaffale"**:
   - una sola tabella con **tutte le righe** degli ordini appena creati;
   - colonne: **Codice fornitore** | **Fornitore** | **Prodotto (SKU / descrizione)** | **Giacenza** | **15gg / 13ms** (opzionale) | **Quantità** | **U.M.**;
   - righe ordinate per **reparto / categoria** (o per nome prodotto) così da riflettere il percorso a scaffale;
   - le quantità sono **modificabili** in linea; salvando, si aggiornano le righe nei rispettivi ordini (uno per fornitore).
4. Un pulsante **"Torna agli ordini"** (o link) porta alla lista ordini; da lì puoi aprire il singolo ordine per un fornitore (es. per inviare email).

---

## Dettaglio tecnico (in sintesi)

- **Nessun nuovo modello**: restano `OrdineFornitore` (uno per fornitore) e `RigaOrdine` (collegata a un solo ordine).
- **Nuova vista (es. "Griglia scaffale")**:
  - URL es. `/admin/orders/griglia-scaffale/?ordini=12,13` (ID degli ordini creati).
  - La vista legge tutti gli ordini passati come parametro, unisce le righe (con riferimento a quale ordine/fornitore appartengono), le ordina per reparto/descrizione e le mostra in una tabella.
  - Form: ogni riga ha un campo quantità (e eventualmente U.M.); in POST si mappa ogni riga al suo `RigaOrdine.id` e si fa `RigaOrdine.objects.filter(id__in=...).update(qta_1=..., unita_1=...)` (o salvataggio riga per riga).
- **Integrazione con l’azione "Genera Bozza Ordine"**:
  - Dopo aver creato gli ordini (multi-fornitore), invece di redirect alla lista ordini, redirect a:  
    `/admin/orders/griglia-scaffale/?ordini=<id1>,<id2>`  
  - Così l’utente vede subito la griglia unificata e può modificare le quantità “a scaffale”.

---

## Cosa implementare (step)

1. **Vista admin custom** `GrigliaScaffaleView` (solo per staff):
   - GET: mostra tabella unificata (righe da più ordini, con colonna fornitore/codice fornitore).
   - POST: aggiorna le quantità (e U.M. se serve) sulle `RigaOrdine` interessate.
2. **Registrazione URL** sotto `/admin/...` (o sotto un path dedicato protetto da login admin).
3. **Modifica azione "Genera Bozza Ordine"**: se `len(ordini_creati) > 1`, redirect a griglia scaffale con `?ordini=id1,id2,...` invece che alla lista ordini.
4. **Colonna "Codice fornitore"** nella griglia: lettura da `riga.ordine.fornitore.codice` (già disponibile dopo il lavoro su APR050).

---

## Note

- **Permessi**: vista riservata a utenti staff (come il resto dell’admin).
- **Ordini già esistenti**: la stessa griglia può essere aperta anche per ordini creati in precedenza (basta passare gli ID), es. da un link “Apri griglia scaffale” nella lista ordini per ordini multipli selezionati (fase successiva).
