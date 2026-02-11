# Aggiornamento automatico Tabella Casse da Google Fogli

Quando modifichi il foglio "saldi per casse", i dati possono essere inviati a PythonAnywhere così che la pagina `/casse/` sia sempre istantanea (legge da file locale invece che da Google).

---

## 1. Configurazione su PythonAnywhere

Su PythonAnywhere la chiave si imposta **nel file WSGI** (non serve cercare "Environment variables" né il file .env).

1. Vai su **Dashboard** → **Web**.
2. Clicca sul link **WSGI configuration file** (es. `/var/www/federicoconigliaro_pythonanywhere_com_wsgi.py`).
3. Si apre l’editor. **Subito dopo le righe che aggiungono il path** (quelle con `sys.path.insert`), aggiungi queste due righe (sostituisci `TUA_CHIAVE_SEGRETA` con una password che scegli solo tu, es. `SaldiCasse2026xyz`):

```python
import os
os.environ['CASSE_UPDATE_SECRET'] = 'TUA_CHIAVE_SEGRETA'
```

   Esempio: se il file contiene già qualcosa tipo:
   ```python
   path = '/home/FedericoConigliaro/GitHub'
   if path not in sys.path:
       sys.path.insert(0, path)
   ```
   aggiungi **subito sotto**:
   ```python
   os.environ['CASSE_UPDATE_SECRET'] = 'TUA_CHIAVE_SEGRETA'
   ```
   (se c’è già `import os` più sopra, non ripeterlo, aggiungi solo la riga con `os.environ`.)

4. Clicca **Save** in alto.
5. Torna alla scheda **Web** e clicca il pulsante verde **Reload** per la web app.

L’URL da chiamare da Google sarà:  
`https://federicoconigliaro.pythonanywhere.com/casse/update/`  
e nello script Google (riga `var SECRET = '...'`) userai **esattamente** lo stesso valore di `TUA_CHIAVE_SEGRETA`.

---

## 2. Script in Google Fogli

1. Apri il foglio **Crediti Conigliaro** (scheda "saldi per casse").
2. Menu **Estensioni** → **Apps Script**.
3. Cancella il contenuto e incolla lo script qui sotto.
4. Nella riga `var SECRET = '...';` metti **esattamente** lo stesso valore di `CASSE_UPDATE_SECRET`.
5. Nella riga `var URL = '...';` metti l’URL del tuo sito (es. `https://federicoconigliaro.pythonanywhere.com/casse/update/`).
6. Salva (icona disco) e dai un nome al progetto (es. "Invia saldi a PythonAnywhere").

### Script da incollare

```javascript
// Invia il foglio "saldi per casse" come CSV a PythonAnywhere
// Da eseguire: alla modifica (trigger) oppure dal menu "Invia saldi a server"

var SECRET = 'MettiQuiLaStessaChiaveDiCASSE_UPDATE_SECRET';
var URL = 'https://federicoconigliaro.pythonanywhere.com/casse/update/';

function getSheetAsCsv() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('saldi per casse');
  if (!sheet) {
    Logger.log('Foglio "saldi per casse" non trovato');
    return null;
  }
  var data = sheet.getDataRange().getValues();
  var csv = data.map(function(row) {
    return row.map(function(cell) {
      var s = cell === null || cell === undefined ? '' : String(cell);
      if (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\n') >= 0) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    }).join(',');
  }).join('\r\n');
  return csv;
}

function inviaSaldiAServer() {
  var csv = getSheetAsCsv();
  if (!csv) return;
  var options = {
    method: 'post',
    contentType: 'text/csv; charset=utf-8',
    payload: csv,
    headers: { 'X-Casse-Secret': SECRET },
    muteHttpExceptions: true
  };
  var resp = UrlFetchApp.fetch(URL, options);
  if (resp.getResponseCode() === 200) {
    Logger.log('OK – Saldi inviati a PythonAnywhere');
  } else {
    Logger.log('Errore ' + resp.getResponseCode() + ': ' + resp.getContentText());
  }
}

// Menu per invio manuale
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Saldi Casse')
    .addItem('Invia saldi a server', 'inviaSaldiAServer')
    .addToUi();
}
```

---

## 3. Trigger alla modifica (opzionale)

Per inviare i dati **automaticamente** ogni volta che modifichi il foglio:

1. In Apps Script: icona **Trigger** (orologio) → **Aggiungi trigger**.
2. Funzione: `inviaSaldiAServer`.
3. Evento: **Da foglio** → **Alla modifica** (o **All’apertura** se preferisci aggiornare aprendo il foglio).
4. Salva.

In alternativa puoi usare solo il menu **Saldi Casse** → **Invia saldi a server** quando hai finito di modificare.

---

## 4. Verifica

- Dopo aver eseguito **Invia saldi a server** (o dopo una modifica se hai il trigger), apri la pagina `/casse/` sul sito: dovrebbe caricarsi subito con i dati aggiornati.
- Se vedi ancora dati vecchi o errore, controlla i log in Apps Script (**Esecuzione**) e l’error log della web app su PythonAnywhere.
