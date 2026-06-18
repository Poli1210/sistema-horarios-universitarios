"""URLs de la app core."""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('',            views.lista_horarios,  name='horarios'),
    path('horarios/',   views.lista_horarios,  name='lista_horarios'),
    path('facultades/', views.lista_facultades, name='facultades'),
]
