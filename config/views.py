import csv
import io
import urllib.request
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

# Chiave e TTL cache tabella casse
CASSE_CACHE_KEY = 'link_casse_table_rows'
CASSE_MAX_COLS = 6  # colonne A–F dal foglio
# Indici colonne da mostrare (0=A, 1=B, …): escluse C e F (date)
CASSE_COL_INDICES = (0, 1, 3, 4)  # A Saldo, B Codice Cliente, D, E


def _build_csv_url():
    """
    Costruisce l'URL di export CSV.
    L'export funziona solo con l'ID del foglio dall'URL di MODIFICA (…/d/ID/edit#gid=…),
    non con l'ID "Pubblica sul web" (/d/e/…).
    """
    url = getattr(settings, 'GOOGLE_SHEET_CASSE_CSV_URL', '').strip()
    if url:
        return url
    sheet_id = getattr(settings, 'GOOGLE_SHEET_CASSE_SPREADSHEET_ID', '').strip()
    gid = getattr(settings, 'GOOGLE_SHEET_CASSE_GID', '0').strip() or '0'
    if not sheet_id:
        return ''
    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'


def _is_saldo_zero(cell_value):
    """True se la colonna A (Saldo) è zero: es. '€ 0,00', '0', '-€ 0,00'."""
    if not cell_value:
        return True
    s = cell_value.strip().replace(' ', '').replace(',', '.').replace('€', '').replace('−', '-').replace('\u2212', '-')
    if not s or s == '-':
        return True
    try:
        return float(s) == 0
    except ValueError:
        return s in ('0', '0.00', '0,00')


def _fetch_csv_rows(csv_url, max_cols=CASSE_MAX_COLS):
    """Scarica il CSV da Google e restituisce le righe (solo prime max_cols colonne)."""
    req = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0 (compatible; ConigliaroCasse/1)'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(text))
    keep = CASSE_COL_INDICES
    def pick(row):
        r = row[:max_cols]
        return [r[i] for i in keep if i < len(r)]
    rows = [pick(row) for row in reader]
    # Dati dal rigo 3 in poi (indice 2 = terza riga come intestazione)
    from_row_3 = rows[2:] if len(rows) > 2 else []
    if not from_row_3:
        return []
    header = from_row_3[0]
    data_rows = [r for r in from_row_3[1:] if r and not _is_saldo_zero(r[0])]
    return [header] + data_rows


def link_casse(request):
    """
    Pagina tabella casse: dati dal foglio Google in CSV, cache 3 min, solo colonne A–F.
    Niente iframe: tabella HTML leggera, caricamento in circa 1 secondo.
    """
    csv_url = _build_csv_url()

    table_rows = None
    error_message = None

    if csv_url:
        cache_seconds = getattr(settings, 'CASSE_TABLE_CACHE_SECONDS', 180)
        table_rows = cache.get(CASSE_CACHE_KEY)
        if table_rows is None:
            try:
                table_rows = _fetch_csv_rows(csv_url)
                cache.set(CASSE_CACHE_KEY, table_rows, cache_seconds)
            except Exception as e:
                err = str(e)
                if '404' in err:
                    error_message = (
                        'Foglio non trovato (404). Usa l’ID dall’URL di MODIFICA: '
                        'apri il foglio in Google Fogli, nella barra indirizzi copia '
                        'l’ID tra /d/ e /edit (es. 1BxiM...) e impostalo in '
                        'GOOGLE_SHEET_CASSE_SPREADSHEET_ID. Non usare l’URL "Pubblica sul web".'
                    )
                else:
                    error_message = f'Impossibile caricare i dati: {e}'
                table_rows = []

    return render(request, 'link_casse.html', {
        'table_rows': table_rows or [],
        'error_message': error_message,
        'casse_configured': bool(csv_url),
    })
