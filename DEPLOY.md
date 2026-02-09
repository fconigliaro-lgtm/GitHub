# Pubblicare le modifiche su PythonAnywhere

Flusso consigliato: **Git** sul PC → **GitHub** → **PythonAnywhere** (pull + reload).

---

## 1. Una tantum: preparare il repo (sul PC)

Apri il terminale in `c:\erp_scadenze`:

```powershell
cd c:\erp_scadenze
git init
git add .
git commit -m "Setup iniziale progetto"
```

Crea un repository **vuoto** su [GitHub](https://github.com/new) (senza README/license). Poi collega e pusha:

```powershell
git remote add origin https://github.com/TUO_USERNAME/erp_scadenze.git
git branch -M main
git push -u origin main
```

(Sostituisci `TUO_USERNAME` e `erp_scadenze` con il tuo utente e il nome del repo.)

---

## 2. Una tantum: su PythonAnywhere

- Vai su **Dashboard** → **Consoles** → **Bash**.
- Se non hai ancora il codice da GitHub:

```bash
cd ~
git clone https://github.com/TUO_USERNAME/erp_scadenze.git
```

- Nella scheda **Web** assicurati che:
  - **Source code** punti alla cartella del progetto (es. `/home/TUO_USERNAME/erp_scadenze`).
  - **WSGI** punti al file corretto (es. `config/wsgi.py`).
- Crea e attiva un virtualenv nella cartella del progetto e installa le dipendenze:

```bash
cd ~/erp_scadenze
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- Imposta variabili d’ambiente per produzione (Consoles o nel file WSGI):
  - `DEBUG=False`
  - `SECRET_KEY` (valore sicuro)
  - `ALLOWED_HOSTS` con il tuo dominio PythonAnywhere (es. `tuousername.pythonanywhere.com`)

Poi dalla scheda **Web** clicca **Reload** per avviare l’app.

---

## 3. Ogni volta che pubblichi modifiche

### Sul PC (dopo aver modificato il codice)

```powershell
cd c:\erp_scadenze
git add .
git status
git commit -m "Descrizione delle modifiche"
git push
```

### Su PythonAnywhere

1. Apri una **Bash console**.
2. Vai nella cartella del progetto e aggiorna il codice:

```bash
cd ~/erp_scadenze
git pull
```

3. Se hai cambiato dipendenze:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

4. Vai nella scheda **Web** e clicca il pulsante **Reload** (in alto).

Dopo il reload, il sito su PythonAnywhere userà il codice aggiornato.

---

## Riepilogo comandi rapidi

| Dove        | Cosa fare                          |
|------------|-------------------------------------|
| **PC**     | `git add .` → `git commit -m "..."` → `git push` |
| **PythonAnywhere** | `cd ~/erp_scadenze` → `git pull` → **Web** → **Reload** |

---

## Note

- **Database**: `db.sqlite3` è nel `.gitignore`. Su PythonAnywhere il DB è quello sul server; i dati non si sincronizzano con il PC. Per “copiare” dati da locale a PA dovresti fare export/import a parte.
- **Segreti**: non mettere mai `SECRET_KEY` o password in chiaro nel codice; su PA usa variabili d’ambiente o il file di config suggerito da PythonAnywhere.
- **Automatizzare il reload**: puoi usare una GitHub Action (es. [pythonanywhere-webapp-reload-action](https://github.com/jensvog/pythonanywhere-webapp-reload-action)) per fare reload automatico dopo ogni push.
