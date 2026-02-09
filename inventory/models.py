from django.db import models
from datetime import timedelta, date

class Prodotto(models.Model):
    # Identificativi
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    barcode = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    
    # --- CAMPI FONDAMENTALI PER L'ORDINE (AGGIUNTI ORA) ---
    giacenza = models.IntegerField(default=0, verbose_name="Giacenza Attuale")
    pezzi_per_cartone = models.IntegerField(default=1, verbose_name="Pz x Cartone")
    # ------------------------------------------------------

    # Dettagli
    descrizione = models.CharField(max_length=255, blank=True)
    reparto = models.CharField(max_length=10, blank=True, null=True)
    cat_stat = models.CharField(max_length=10, blank=True, null=True)
    
    # Logiche Scadenza
    tmc_giorni = models.IntegerField(default=30, help_text="Giorni di vita (TMC)")
    
    def __str__(self):
        return f"{self.descrizione} ({self.sku})"

class LottoVirtuale(models.Model):
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE, related_name='lotti')
    data_arrivo = models.DateField()
    qta_iniziale = models.DecimalField(max_digits=10, decimal_places=3)
    qta_residua = models.DecimalField(max_digits=10, decimal_places=3)
    
    data_scadenza_stimata = models.DateField()
    data_scadenza_reale = models.DateField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.data_scadenza_stimata and self.data_arrivo:
            # Calcola scadenza stimata basandosi sul TMC del prodotto
            self.data_scadenza_stimata = self.data_arrivo + timedelta(days=self.prodotto.tmc_giorni)
        super().save(*args, **kwargs)