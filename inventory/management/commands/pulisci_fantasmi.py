from django.core.management.base import BaseCommand
from datetime import date
from inventory.models import LottoVirtuale

class Command(BaseCommand):
    help = 'Azzera le giacenze dei prodotti scaduti da troppo tempo (Fantasmi)'

    def handle(self, *args, **kwargs):
        # DATA DI TAGLIO: Tutto ciò che scade prima di questa data viene azzerato.
        # Mettiamo 1 Gennaio 2025 (così teniamo solo lo storico recente)
        # Se vuoi essere più aggressivo, puoi mettere date(2025, 12, 1)
        DATA_LIMIT = date(2026, 1, 1)

        self.stdout.write(f"--- PULIZIA FANTASMI (Precedenti al {DATA_LIMIT}) ---")

        # Trova i lotti vecchi che risultano ancora pieni
        lotti_vecchi = LottoVirtuale.objects.filter(
            data_scadenza_stimata__lt=DATA_LIMIT,
            qta_residua__gt=0
        )

        count = lotti_vecchi.count()
        self.stdout.write(f"Trovati {count} lotti 'fantasmi' da eliminare...")

        # Aggiornamento massivo (velocissimo)
        # Mettiamo qta_residua = 0 così spariscono dalla Dashboard
        rows = lotti_vecchi.update(qta_residua=0)

        self.stdout.write(self.style.SUCCESS(f"✅ PULIZIA COMPLETATA! Rimossi {rows} prodotti vecchi."))