"""URLs raíz del proyecto sistema_horarios."""

from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Sistema de Horarios Universitarios"
admin.site.site_title  = "Horarios"
admin.site.index_title = "Panel de Administración"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',       include('core.urls', namespace='core')),
]
