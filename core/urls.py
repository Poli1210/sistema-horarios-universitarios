"""URLs de la app core."""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Vistas principales
    path('',              views.lista_horarios,   name='horarios'),
    path('horarios/',     views.lista_horarios,   name='lista_horarios'),
    path('facultades/',   views.lista_facultades, name='facultades'),

    # Automatrícula: vista HTML + endpoint API
    path('automatricula/',      views.vista_automatricula, name='automatricula'),
    path('api/automatricula/',  views.api_automatricula,   name='api_automatricula'),
]
