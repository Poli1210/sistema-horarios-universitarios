"""
Configuración del panel de administración Django para los modelos académicos.
"""

from django.contrib import admin
from .models import Facultad, Programa, Profesor, Materia, Horario


# ── Inlines ──────────────────────────────────────────────────────────────────

class ProgramaInline(admin.TabularInline):
    """Muestra los programas directamente dentro de la Facultad."""
    model = Programa
    extra = 1


class MateriaInline(admin.TabularInline):
    """Muestra las materias directamente dentro del Programa."""
    model = Materia
    extra = 1


class HorarioInline(admin.TabularInline):
    """Muestra los horarios directamente dentro de la Materia."""
    model = Horario
    extra = 1


# ── ModelAdmins ───────────────────────────────────────────────────────────────

@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'total_programas')
    search_fields = ('nombre',)
    inlines       = [ProgramaInline]

    @admin.display(description='Programas')
    def total_programas(self, obj):
        return obj.programas.count()


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'facultad', 'total_materias')
    list_filter   = ('facultad',)
    search_fields = ('nombre', 'facultad__nombre')
    inlines       = [MateriaInline]

    @admin.display(description='Materias')
    def total_materias(self, obj):
        return obj.materias.count()


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'email', 'total_materias')
    search_fields = ('nombre', 'email')

    @admin.display(description='Materias asignadas')
    def total_materias(self, obj):
        return obj.materias.count()


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'programa', 'facultad_nombre', 'profesor')
    list_filter   = ('programa__facultad', 'programa')
    search_fields = ('nombre', 'programa__nombre', 'profesor__nombre')
    inlines       = [HorarioInline]

    @admin.display(description='Facultad', ordering='programa__facultad__nombre')
    def facultad_nombre(self, obj):
        return obj.programa.facultad.nombre


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display  = ('materia', 'dia_display', 'hora_inicio', 'hora_fin', 'salon', 'facultad_nombre')
    list_filter   = ('dia', 'materia__programa__facultad', 'materia__programa')
    search_fields = ('materia__nombre', 'salon')
    ordering      = ('dia', 'hora_inicio')

    @admin.display(description='Día', ordering='dia')
    def dia_display(self, obj):
        return obj.get_dia_display()

    @admin.display(description='Facultad')
    def facultad_nombre(self, obj):
        return obj.materia.programa.facultad.nombre
