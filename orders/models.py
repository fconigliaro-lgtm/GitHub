from django.db import models
from django.utils import timezone

class Fornitore(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    attivo = models.BooleanField(default=True, verbose_name="Fornitore Attivo")
    email_ordini = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    indirizzo = models.TextField(blank=True, null=True)
    giorno_consegna_abituale = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self): return self.nome
    class Meta: verbose_name_plural = "Fornitori"

class ListinoFornitore(models.Model):
    fornitore = models.ForeignKey(Fornitore, on_delete=models.CASCADE, related_name='prodotti_listino')
    prodotto = models.ForeignKey('inventory.Prodotto', on_delete=models.CASCADE)
    codice_articolo_fornitore = models.CharField(max_length=50, blank=True, null=True)
    prezzo_acquisto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    escludi_da_ordine = models.BooleanField(default=False, verbose_name="🚫 Escludi (Obsoleto)")

    class Meta: unique_together = ('fornitore', 'prodotto')
    def __str__(self):
        # Mostra: "900074330 - NOME PRODOTTO"
        return f"{self.prodotto.sku} - {self.prodotto.descrizione}"

class OrdineFornitore(models.Model):
    STATI = [('BOZZA', 'Bozza'), ('INVIATO', 'Inviato'), ('CONFERMATO', 'Confermato')]
    fornitore = models.ForeignKey(Fornitore, on_delete=models.CASCADE)
    data_creazione = models.DateTimeField(auto_now_add=True)
    stato = models.CharField(max_length=20, choices=STATI, default='BOZZA')
    note = models.TextField(blank=True, null=True)
    
    def __str__(self): return f"Ordine #{self.id} - {self.fornitore.nome}"
    class Meta: verbose_name_plural = "Ordini Fornitori"

class RigaOrdine(models.Model):
    UNITA_MISURA = [
        ('COLLI', 'Colli'),
        ('PEZZI', 'Pezzi'),
        ('EXPO', 'Expo'),
        ('KG', 'Kg'),
    ]

    ordine = models.ForeignKey(OrdineFornitore, on_delete=models.CASCADE, related_name='righe')
    prodotto = models.ForeignKey('inventory.Prodotto', on_delete=models.CASCADE)
    pezzi_per_collo = models.IntegerField(default=1) 

    # --- UNICA QUANTITA' (SEMPLICE E PULITO) ---
    qta_1 = models.IntegerField(default=0, verbose_name="Quantità")
    unita_1 = models.CharField(max_length=10, choices=UNITA_MISURA, default='COLLI', verbose_name="U.M.")
    
    class Meta: verbose_name_plural = "Righe Ordine"

    def __str__(self):
        return self.prodotto.descrizione if self.prodotto else "Nuova Riga"