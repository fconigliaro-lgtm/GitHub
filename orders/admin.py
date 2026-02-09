from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Sum, Max
from django.core.mail import send_mail
from django.conf import settings
import calendar
import math
import datetime
from .models import Fornitore, OrdineFornitore, RigaOrdine, ListinoFornitore
from sales.models import VenditaStorica, AcquistoStorico

# --- CSS ESSENZIALE ---
CUSTOM_CSS = """
<style>
    .field-dettagli_prodotto {
        position: sticky !important; left: 0; z-index: 10;
        background-color: #fff !important; border-right: 2px solid #ccc;
        min-width: 180px; max-width: 200px;
        vertical-align: middle !important;
    }
    .vIntegerField { width: 40px !important; font-size: 11px !important; height: 18px !important; }
    select { width: 60px !important; font-size: 10px !important; height: 20px !important; padding: 0 !important; }
    
    .stats-cell { font-weight: bold; font-size: 11px; text-align: center; }
</style>
"""

# --- HELPER TABELLA ---
def get_compact_table(period_type, sales_data, purchase_data, reference_date):
    headers_html = ""
    sales_row = ""
    purch_row = ""
    
    STYLE_TH = "font-size:9px; padding:1px; background:#f0f0f0; border:1px solid #ccc; color:#333; min-width:14px; text-align:center;"
    STYLE_TD = "font-size:9px; padding:0px; text-align:center; border:1px solid #ccc; height:12px; line-height:12px;"
    
    if period_type == 'daily':
        labels = [(reference_date - datetime.timedelta(days=i)).day for i in range(14, -1, -1)]
        title = "15gg"
    else:
        curr_month = reference_date.month
        labels = []
        for i in range(12, -1, -1):
            m = curr_month - i
            if m <= 0: m += 12
            labels.append(calendar.month_name[m][:1])
        title = "13ms"

    for i, label in enumerate(labels):
        s_val = sales_data[i] if sales_data and len(sales_data) > i else 0
        s_bg = "#ffebee" if s_val > 0 else "#fff"
        s_fg = "#c62828" if s_val > 0 else "#ccc"
        s_w = "bold" if s_val > 0 else "normal"
        
        p_val = purchase_data[i] if purchase_data and len(purchase_data) > i else 0
        p_bg = "#e3f2fd" if p_val > 0 else "#fff"
        p_fg = "#1565c0" if p_val > 0 else "#ccc"
        p_w = "bold" if p_val > 0 else "normal"

        headers_html += f"<th style='{STYLE_TH}'>{label}</th>"
        sales_row += f"<td style='{STYLE_TD} background:{s_bg}; color:{s_fg}; font-weight:{s_w};'>{int(s_val) if s_val else ''}</td>"
        purch_row += f"<td style='{STYLE_TD} background:{p_bg}; color:{p_fg}; font-weight:{p_w};'>{int(p_val) if p_val else ''}</td>"

    return mark_safe(f"""
    <div style="display:inline-block; vertical-align:top; margin-right:4px;">
        <div style="font-size:8px; font-weight:bold; color:#666; margin-bottom:1px;">{title}</div>
        <table style="border-collapse: collapse; border:1px solid #ccc; margin:0;">
            <thead><tr><th style="width:10px; border:none; background:none;"></th>{headers_html}</tr></thead>
            <tbody>
                <tr style="height:12px;"><td style="font-size:9px; color:#c62828; font-weight:bold; padding:0 2px; border:none;">V</td>{sales_row}</tr>
                <tr style="height:12px;"><td style="font-size:9px; color:#1565c0; font-weight:bold; padding:0 2px; border:none;">A</td>{purch_row}</tr>
            </tbody>
        </table>
    </div>""")

# --- ACTION: GENERA ORDINE ---
@admin.action(description='⚡ Genera Bozza Ordine (Auto)')
def crea_bozza_ordine(modeladmin, request, queryset):
    ultima_vendita = VenditaStorica.objects.aggregate(Max('data'))['data__max']
    today = timezone.now().date()
    simulation_date = ultima_vendita if ultima_vendita and ultima_vendita.year > today.year else today
    start_date = simulation_date - datetime.timedelta(days=30)

    for fornitore in queryset:
        if not fornitore.attivo: continue
        ordine = OrdineFornitore.objects.create(fornitore=fornitore)
        prodotti = ListinoFornitore.objects.filter(fornitore=fornitore, escludi_da_ordine=False).select_related('prodotto')
        if not prodotti.exists(): continue

        righe = []
        for voce in prodotti:
            prod = voce.prodotto
            vendite = VenditaStorica.objects.filter(prodotto=prod, data__range=[start_date, simulation_date]).aggregate(tot=Sum('quantita'))['tot'] or 0
            
            fabbisogno = (float(vendite) / 30 * 40) - prod.giacenza
            qta = 0
            if fabbisogno > 0:
                divisore = prod.pezzi_per_cartone if prod.pezzi_per_cartone > 0 else 1
                qta = math.ceil(fabbisogno / divisore)

            righe.append(RigaOrdine(
                ordine=ordine, prodotto=prod, qta_1=qta, unita_1='COLLI', pezzi_per_collo=prod.pezzi_per_cartone
            ))
        RigaOrdine.objects.bulk_create(righe)
        return redirect(reverse('admin:orders_ordinefornitore_change', args=[ordine.id]))

# --- ACTION: INVIA EMAIL ---
@admin.action(description='📧 Invia Ordine via Email')
def invia_ordine_email(modeladmin, request, queryset):
    inviati = 0
    for ordine in queryset:
        if not ordine.fornitore.email_ordini:
            modeladmin.message_user(request, f"Manca email per {ordine.fornitore.nome}!", level='ERROR')
            continue
        
        righe = ordine.righe.filter(qta_1__gt=0).select_related('prodotto')
        if not righe: continue
        
        html_msg = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <h2>Ordine #{ordine.id}</h2>
            <p>Gentile <strong>{ordine.fornitore.nome}</strong>,</p>
            <p>Vi inviamo in allegato il nostro ordine:</p>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px; border: 1px solid #ddd;">
                <thead style="background-color: #f2f2f2;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Cod. Fornitore</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Descrizione</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Qta</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">U.M.</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        txt_msg = f"Ordine #{ordine.id} per {ordine.fornitore.nome}\n\nCOD. | DESCRIZIONE | QTA | UM\n" + "-"*50 + "\n"

        for r in righe:
            try:
                voce_listino = ListinoFornitore.objects.get(fornitore=ordine.fornitore, prodotto=r.prodotto)
                codice_rif = voce_listino.codice_articolo_fornitore or ""
            except ListinoFornitore.DoesNotExist:
                codice_rif = ""

            html_msg += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{codice_rif}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{r.prodotto.descrizione}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;"><strong>{r.qta_1}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{r.unita_1}</td>
                </tr>
            """
            txt_msg += f"{codice_rif:<10} | {r.prodotto.descrizione[:30]:<30} | {r.qta_1} {r.unita_1}\n"

        html_msg += """</tbody></table><br><p>Cordiali Saluti,<br><em>Supermercati Conigliaro</em></p></body></html>"""

        try:
            send_mail(f"Nuovo Ordine #{ordine.id}", txt_msg, settings.DEFAULT_FROM_EMAIL, [ordine.fornitore.email_ordini], fail_silently=False, html_message=html_msg)
            ordine.stato = 'INVIATO'
            ordine.save()
            inviati += 1
        except Exception as e:
            modeladmin.message_user(request, f"Errore invio: {e}", level='ERROR')
            
    if inviati > 0: modeladmin.message_user(request, f"✅ Ordini inviati: {inviati}")

# --- INLINES ---
class RigaOrdineInline(admin.TabularInline):
    model = RigaOrdine
    extra = 0
    fields = ('dettagli_prodotto', 'tabella_mesi', 'tabella_giorni', 'qta_1', 'unita_1')
    readonly_fields = ('dettagli_prodotto', 'tabella_mesi', 'tabella_giorni')
    
    def get_simulation_date(self):
        ultima = VenditaStorica.objects.aggregate(Max('data'))['data__max']
        return ultima if ultima else timezone.now().date()

    def dettagli_prodotto(self, obj):
        colore = "green" if obj.prodotto.giacenza > 0 else "red"
        return mark_safe(
            f"<div style='line-height:1; margin:0; padding:2px 0;'>"
            f"<b style='color:#000; font-size:10px;'>{obj.prodotto.descrizione}</b><br>"
            f"<span style='color:#666; font-size:9px;'>{obj.prodotto.sku}</span><br>"
            f"<span style='font-size:9px;'>Giac: <b style='color:{colore}'>{obj.prodotto.giacenza}</b></span>"
            f"</div>"
        )
    dettagli_prodotto.short_description = "Articolo"

    def tabella_giorni(self, obj):
        today = self.get_simulation_date()
        start = today - datetime.timedelta(days=14)
        v = VenditaStorica.objects.filter(prodotto=obj.prodotto, data__range=[start, today]).values('data').annotate(t=Sum('quantita'))
        a = AcquistoStorico.objects.filter(prodotto=obj.prodotto, data__range=[start, today]).values('data').annotate(t=Sum('quantita'))
        mv = {d['data']: d['t'] for d in v}
        ma = {d['data']: d['t'] for d in a}
        conf = obj.prodotto.pezzi_per_cartone if obj.prodotto.pezzi_per_cartone and obj.prodotto.pezzi_per_cartone > 0 else 1
        sd = [mv.get(today-datetime.timedelta(days=i), 0) for i in range(14,-1,-1)]
        pd = [(ma.get(today-datetime.timedelta(days=i), 0) * conf) for i in range(14,-1,-1)]
        return get_compact_table('daily', sd, pd, today)
    tabella_giorni.short_description = "15gg"

    def tabella_mesi(self, obj):
        today = self.get_simulation_date()
        start = today - datetime.timedelta(days=400)
        v = VenditaStorica.objects.filter(prodotto=obj.prodotto, data__gte=start).values('data__year', 'data__month').annotate(t=Sum('quantita'))
        a = AcquistoStorico.objects.filter(prodotto=obj.prodotto, data__gte=start).values('data__year', 'data__month').annotate(t=Sum('quantita'))
        mv = {f"{d['data__year']}-{d['data__month']}": d['t'] for d in v}
        ma = {f"{d['data__year']}-{d['data__month']}": d['t'] for d in a}
        sd, pd = [], []
        cm, cy = today.month, today.year
        conf = obj.prodotto.pezzi_per_cartone if obj.prodotto.pezzi_per_cartone and obj.prodotto.pezzi_per_cartone > 0 else 1
        for i in range(12, -1, -1):
            m, y = cm - i, cy
            if m <= 0: m, y = m + 12, y - 1
            k = f"{y}-{m}"
            sd.append(mv.get(k, 0))
            pd.append(ma.get(k, 0) * conf)
        return get_compact_table('monthly', sd, pd, today)
    tabella_mesi.short_description = "13ms"

class ListinoInline(admin.TabularInline):
    model = ListinoFornitore
    extra = 0
    raw_id_fields = ('prodotto',) 
    fields = ('prodotto', 'totale_venduto', 'totale_acquistato', 'escludi_da_ordine')
    readonly_fields = ('prodotto','totale_venduto', 'totale_acquistato')
    can_delete = False
    verbose_name = "Prodotto in Listino"
    verbose_name_plural = "📦 LISTINO PRODOTTI"

    def totale_venduto(self, obj):
        today = timezone.now().date()
        start = today - datetime.timedelta(days=365)
        tot = VenditaStorica.objects.filter(prodotto=obj.prodotto, data__gte=start).aggregate(t=Sum('quantita'))['t'] or 0
        style = "color: red;" if tot > 0 else "color: #ccc;"
        return mark_safe(f"<span class='stats-cell' style='{style}'>{int(tot)} pz</span>")
    totale_venduto.short_description = "Vend. 12m"

    def totale_acquistato(self, obj):
        today = timezone.now().date()
        start = today - datetime.timedelta(days=365)
        tot = AcquistoStorico.objects.filter(prodotto=obj.prodotto, data__gte=start).aggregate(t=Sum('quantita'))['t'] or 0
        conf = obj.prodotto.pezzi_per_cartone if obj.prodotto.pezzi_per_cartone > 0 else 1
        tot_pezzi = tot * conf
        style = "color: blue;" if tot_pezzi > 0 else "color: #ccc;"
        return mark_safe(f"<span class='stats-cell' style='{style}'>{int(tot_pezzi)} pz</span>")
    totale_acquistato.short_description = "Acq. 12m"

# --- FORNITORE ADMIN (CON ARCHIVIAZIONE RAPIDA) ---
@admin.register(Fornitore)
class FornitoreAdmin(admin.ModelAdmin):
    # Colonne visibili nella lista principale
    list_display = ('nome', 'attivo', 'volume_acquisti_anno', 'conta_prodotti') 
    
    # Questo è il trucco: rendiamo 'attivo' cliccabile direttamente nella lista
    list_editable = ('attivo',)
    
    # Filtro laterale: Clicca su "Attivo: Si" per nascondere l'archivio
    list_filter = ('attivo',) 
    
    search_fields = ('nome',)
    inlines = [ListinoInline]
    actions = [crea_bozza_ordine]
    ordering = ('-attivo', 'nome') # Mette prima i fornitori attivi, poi quelli archiviati

    def conta_prodotti(self, obj): 
        return obj.prodotti_listino.count()
    conta_prodotti.short_description = "N. Prodotti"

    def volume_acquisti_anno(self, obj):
        # Calcola il volume totale di acquisti per questo fornitore negli ultimi 12 mesi
        # Attenzione: somma i movimenti di tutti i prodotti collegati
        today = timezone.now().date()
        start = today - datetime.timedelta(days=365)
        
        # Recupera tutti i prodotti di questo fornitore
        prodotti_ids = obj.prodotti_listino.values_list('prodotto_id', flat=True)
        
        # Somma gli acquisti storici per quei prodotti
        tot = AcquistoStorico.objects.filter(prodotto_id__in=prodotti_ids, data__gte=start).aggregate(t=Sum('quantita'))['t'] or 0
        
        # Stile visivo
        style = "color: blue; font-weight: bold;" if tot > 0 else "color: #ccc;"
        return mark_safe(f"<span style='{style}'>{int(tot)} movimenti</span>")
    volume_acquisti_anno.short_description = "Acquisti (12m)"

@admin.register(OrdineFornitore)
class OrdineFornitoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'fornitore', 'data_creazione', 'stato')
    actions = [invia_ordine_email]
    inlines = [RigaOrdineInline]
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['media_custom'] = mark_safe(CUSTOM_CSS)
        return super().change_view(request, object_id, form_url, extra_context=extra_context)