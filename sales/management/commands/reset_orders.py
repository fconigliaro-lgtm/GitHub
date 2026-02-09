from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Cancella solo le tabelle degli ORDINI per ricrearle pulite'

    def handle(self, *args, **kwargs):
        print("--- 🧹 PULIZIA TABELLE ORDINI ---")
        
        with connection.cursor() as cursor:
            # 1. Cancelliamo le tabelle vecchie (l'ordine è importante per le chiavi esterne)
            tables = [
                'orders_rigaordine',
                'orders_ordinefornitore',
                'orders_listinofornitore',
                'orders_fornitore'  # Se vuoi resettare anche i fornitori, altrimenti toglilo
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"✅ Tabella eliminata: {table}")
                except Exception as e:
                    print(f"⚠️ Errore su {table}: {e}")

            # 2. Cancelliamo la memoria delle migrazioni per 'orders'
            try:
                cursor.execute("DELETE FROM django_migrations WHERE app='orders'")
                print("✅ Reset storico migrazioni 'orders' completato.")
            except Exception as e:
                print(f"⚠️ Errore reset migrazioni: {e}")
                
        print("\n🎉 ORA PUOI RI-FARE MAKEMIGRATIONS!")