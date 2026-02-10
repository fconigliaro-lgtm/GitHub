from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from orders.models import Fornitore, ListinoFornitore, OrdineFornitore


class Command(BaseCommand):
    help = (
        "Pulisce i fornitori senza codice (codice NULL/vuoto) duplicati per nome.\n"
        "Per sicurezza è in DRY-RUN di default. Usa --apply per applicare davvero.\n"
        "\n"
        "Regole:\n"
        "- se un fornitore senza codice ha 0 listino e 0 ordini, e esiste 1 fornitore con stesso nome ma con codice, viene cancellato\n"
        "- se ha relazioni e esiste 1 fornitore con stesso nome e codice, sposta relazioni e poi cancella\n"
        "- se esistono più fornitori con codice con lo stesso nome, non fa nulla (ambiguità) e segnala\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Applica realmente le modifiche (di default è dry-run).",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])

        senza_codice = Fornitore.objects.filter(Q(codice__isnull=True) | Q(codice=""))
        totale = senza_codice.count()
        self.stdout.write(f"Trovati fornitori senza codice: {totale}")
        if totale == 0:
            return

        cancellati = 0
        accorpati = 0
        ambigui = 0
        orfani = 0

        @transaction.atomic
        def process_one(f: Fornitore):
            nonlocal cancellati, accorpati, ambigui, orfani

            nome = (f.nome or "").strip()
            if not nome:
                orfani += 1
                self.stdout.write(self.style.WARNING(f"- ID {f.id}: nome vuoto, salto"))
                return

            candidati = (
                Fornitore.objects.filter(nome__iexact=nome)
                .exclude(id=f.id)
                .exclude(Q(codice__isnull=True) | Q(codice=""))
            )
            n = candidati.count()
            if n == 0:
                orfani += 1
                self.stdout.write(self.style.WARNING(f"- ID {f.id} '{f.nome}': nessun duplicato con codice (orfano)"))
                return
            if n > 1:
                ambigui += 1
                codici = list(candidati.values_list("codice", flat=True)[:10])
                self.stdout.write(self.style.WARNING(
                    f"- ID {f.id} '{f.nome}': {n} duplicati con codice (ambigui), codici es: {codici}"
                ))
                return

            target = candidati.first()
            listini = ListinoFornitore.objects.filter(fornitore=f)
            ordini = OrdineFornitore.objects.filter(fornitore=f)

            listini_count = listini.count()
            ordini_count = ordini.count()

            # Se non ha relazioni: cancellazione semplice
            if listini_count == 0 and ordini_count == 0:
                self.stdout.write(f"- ID {f.id} '{f.nome}': duplicato di ID {target.id} (cod {target.codice}) -> DELETE")
                if apply_changes:
                    f.delete()
                cancellati += 1
                return

            # Ha relazioni: accorpa su target
            self.stdout.write(
                f"- ID {f.id} '{f.nome}': accorpo su ID {target.id} (cod {target.codice}) "
                f"[listini={listini_count}, ordini={ordini_count}]"
            )
            if apply_changes:
                # Sposta relazioni LISTINO gestendo collisioni (unique_together fornitore+prodotto)
                # NOTA: niente filtri enormi con IN (...) per evitare "too many SQL variables" su SQLite.
                target_listini = {
                    lf.prodotto_id: lf
                    for lf in ListinoFornitore.objects.filter(fornitore=target)
                }

                # Percorriamo TUTTI i listini del fornitore senza codice e li spostiamo uno per volta
                for lf in listini.select_related("prodotto"):
                    existing = target_listini.get(lf.prodotto_id)
                    if existing:
                        # Esiste già un listino per quel prodotto sul target: fondi i dati e cancella il duplicato
                        changed_listino = False

                        if (existing.codice_articolo_fornitore in (None, "")) and lf.codice_articolo_fornitore not in (None, ""):
                            existing.codice_articolo_fornitore = lf.codice_articolo_fornitore
                            changed_listino = True

                        if existing.prezzo_acquisto is None and lf.prezzo_acquisto is not None:
                            existing.prezzo_acquisto = lf.prezzo_acquisto
                            changed_listino = True

                        if bool(lf.escludi_da_ordine) and not bool(existing.escludi_da_ordine):
                            existing.escludi_da_ordine = True
                            changed_listino = True

                        if changed_listino:
                            existing.save()

                        lf.delete()
                    else:
                        # Nessuna collisione: sposta semplicemente il listino sul target
                        lf.fornitore = target
                        lf.save(update_fields=["fornitore"])
                        target_listini[lf.prodotto_id] = lf

                # Sposta ordini (qui il numero è molto inferiore rispetto ai listini)
                ordini.update(fornitore=target)

                # Migra contatti solo se target è vuoto
                fields = ["email_ordini", "telefono", "indirizzo", "giorno_consegna_abituale"]
                changed = False
                for field in fields:
                    v_old = getattr(f, field, None)
                    v_new = getattr(target, field, None)
                    if (v_new is None or v_new == "") and v_old not in (None, ""):
                        setattr(target, field, v_old)
                        changed = True
                if changed:
                    target.save()

                # Cancella duplicato
                f.delete()
            accorpati += 1

        # Esecuzione
        for f in senza_codice.order_by("nome", "id"):
            process_one(f)

        mode = "APPLY" if apply_changes else "DRY-RUN"
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"[{mode}] Risultato:"))
        self.stdout.write(f"- cancellati: {cancellati}")
        self.stdout.write(f"- accorpati: {accorpati}")
        self.stdout.write(f"- ambigui (non toccati): {ambigui}")
        self.stdout.write(f"- orfani (non toccati): {orfani}")

