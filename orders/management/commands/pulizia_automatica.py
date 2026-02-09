from django.core.management.base import BaseCommand
from orders.models import Fornitore
from dbfread import DBF
import os

class Command(BaseCommand):
    help = 'Importa Fornitori da ART.DBF (P:\\cdapos\\archivi) ignorando quelli senza nome'

    def handle(self, *args, **options):
        # --- PERCORSO CORRETTO INDICATO DA TE ---
        path_dbf = r'P:\cdapos\archivi\ART.DBF'

        if not os.path.exists(path_dbf):
            self.stdout.write(self.style.ERROR(f'ERRORE: File non trovato in: {path_dbf}'))
            self.stdout.write(self.style.WARNING('Verifica che il disco P: sia collegato.'))
            return

        self.stdout.write(f"Lettura di {path_dbf} in corso...")
        
        try:
            table = DBF(path_dbf, encoding='cp850') 
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Errore lettura DBF: {e}"))
            return

        count_creati = 0
        nomi_visti_in_questo_giro = set()

        for record in table:
            raw_nome = record.get('DITTA')

            # --- FILTRO ANTI-SPAZZATURA ---
            if raw_nome is None:
                continue
            
            nome_pulito = str(raw_nome).strip()

            if nome_pulito == "":
                continue
            # ------------------------------

            if nome_pulito in nomi_visti_in_questo_giro:
                continue
            
            nomi_visti_in_questo_giro.add(nome_pulito)

            fornitore, created = Fornitore.objects.get_or_create(
                nome=nome_pulito,
                defaults={'attivo': True}
            )

            if created:
                count_creati += 1
                self.stdout.write(f" + Creato: {nome_pulito}")

        self.stdout.write(self.style.SUCCESS(f"✅ IMPORTAZIONE TERMINATA DA P:. Nuovi fornitori: {count_creati}"))