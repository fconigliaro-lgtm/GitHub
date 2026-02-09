from django.contrib import admin
from .models import VenditaStorica, AcquistoStorico

@admin.register(VenditaStorica)
class VenditaStoricaAdmin(admin.ModelAdmin):
    # Usiamo i NUOVI nomi: 'data', 'quantita', 'riferimento'
    list_display = ('data', 'get_sku', 'quantita', 'riferimento')
    # Cerchiamo dentro il prodotto collegato
    search_fields = ('prodotto__sku', 'prodotto__descrizione', 'riferimento')
    list_filter = ('data',)
    ordering = ('-data',)
    
    def get_sku(self, obj):
        return obj.prodotto.sku
    get_sku.short_description = 'SKU'

@admin.register(AcquistoStorico)
class AcquistoStoricoAdmin(admin.ModelAdmin):
    list_display = ('data', 'get_sku', 'quantita', 'riferimento')
    search_fields = ('prodotto__sku', 'riferimento')
    list_filter = ('data',)
    ordering = ('-data',)

    def get_sku(self, obj):
        return obj.prodotto.sku
    get_sku.short_description = 'SKU'