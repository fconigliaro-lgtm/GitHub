from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from inventory import views as inventory_views
from config.views import link_casse, casse_upload_csv

urlpatterns = [
    # 1. La Home Page (Il menu con i bottoni)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # 2. L'Admin (Dove fai gli ordini)
    path('admin/', admin.site.urls),

    # 3. La Dashboard (Grafici e Statistiche)
    path('dashboard/', inventory_views.dashboard_scadenze, name='dashboard'),

    # 4. Dettaglio Prodotto
    path('prodotto/<str:sku>/', inventory_views.dettaglio_prodotto, name='dettaglio_prodotto'),

    # 5. Link veloce casse – tabella da Google Fogli
    path('casse/', link_casse, name='link_casse'),
    # 6. Ricezione CSV da Google Apps Script (aggiornamento saldi casse)
    path('casse/update/', casse_upload_csv, name='casse_upload_csv'),
]