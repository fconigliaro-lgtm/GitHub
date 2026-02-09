from django.contrib import admin
from .models import Prodotto, LottoVirtuale

@admin.register(Prodotto)
class ProdottoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'descrizione', 'tmc_giorni', 'reparto', 'barcode')
    search_fields = ('sku', 'descrizione', 'barcode')
    list_filter = ('reparto',)

@admin.register(LottoVirtuale)
class LottoVirtualeAdmin(admin.ModelAdmin):
    # Ho rimosso 'stato' se c'era e aggiunto 'stato_giacenza' che calcoliamo qui sotto
    list_display = ('get_sku', 'get_desc', 'data_arrivo', 'qta_iniziale', 'qta_residua', 'data_scadenza_stimata', 'stato_giacenza')
    
    # CORREZIONE: Ho rimosso 'stato' da qui, ora funzionerà
    list_filter = ('data_arrivo',) 
    
    search_fields = ('prodotto__sku', 'prodotto__descrizione')
    ordering = ('-data_arrivo',)

    def get_sku(self, obj):
        return obj.prodotto.sku
    get_sku.short_description = 'SKU'

    def get_desc(self, obj):
        return obj.prodotto.descrizione
    get_desc.short_description = 'Descrizione'

    # Calcoliamo lo stato al volo senza bisogno del campo nel database
    def stato_giacenza(self, obj):
        if obj.qta_residua <= 0:
            return "🔴 ESAURITO"
        elif obj.qta_residua < obj.qta_iniziale:
            return "🟠 IN VENDITA"
        else:
            return "🟢 STOCCATO"
    stato_giacenza.short_description = 'Stato'