from django.db import models

class VenditaStorica(models.Model):
    # Collegamento diretto al prodotto (più veloce delle stringhe)
    prodotto = models.ForeignKey('inventory.Prodotto', on_delete=models.CASCADE, related_name='vendite')
    
    data = models.DateField(db_index=True) 
    quantita = models.DecimalField(max_digits=10, decimal_places=2) # 2 decimali bastano per i pezzi
    
    # Campo opzionale per debug (utile per capire da dove viene il dato)
    riferimento = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Vendite Storiche"
        indexes = [
            # Indice turbo per le query "Dammi le vendite di QUESTO prodotto in QUESTA data"
            models.Index(fields=['prodotto', 'data']),
        ]

    def __str__(self):
        return f"{self.data} | {self.prodotto.sku} | Q: {self.quantita}"
    
    # ... lascia VenditaStorica com'è ...

class AcquistoStorico(models.Model):
    prodotto = models.ForeignKey('inventory.Prodotto', on_delete=models.CASCADE, related_name='acquisti')
    data = models.DateField(db_index=True)
    quantita = models.DecimalField(max_digits=10, decimal_places=2)
    
    riferimento = models.CharField(max_length=100, blank=True, null=True) # Es. Numero Bolla

    class Meta:
        verbose_name_plural = "Acquisti Storici"
        indexes = [
            models.Index(fields=['prodotto', 'data']),
        ]

    def __str__(self):
        return f"ACQ {self.data} | {self.prodotto.sku} | Q: {self.quantita}"