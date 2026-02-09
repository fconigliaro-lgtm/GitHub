from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from inventory import views as inventory_views 

urlpatterns = [
    # 1. La Home Page (Il menu con i bottoni)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # 2. L'Admin (Dove fai gli ordini)
    path('admin/', admin.site.urls),

    # 3. La Dashboard (Grafici e Statistiche)
    # CORRETTO: Ora punta alla funzione giusta 'dashboard_scadenze'
    path('dashboard/', inventory_views.dashboard_scadenze, name='dashboard'), 
    
    # 4. Dettaglio Prodotto
    # Necessario per vedere lo storico quando clicchi su un prodotto
    path('prodotto/<str:sku>/', inventory_views.dettaglio_prodotto, name='dettaglio_prodotto'),
]