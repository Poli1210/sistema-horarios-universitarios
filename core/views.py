"""
Vistas del sistema de horarios universitarios.

Rutas principales:
  /              → lista de horarios con filtros
  /horarios/     → igual que /
  /facultades/   → listado de facultades y sus programas
"""

from django.shortcuts import render, get_object_or_404
from .models import Facultad, Programa, Horario


def lista_horarios(request):
    """
    Vista principal: muestra todos los horarios con filtros opcionales
    por facultad y/o programa.
    """
    facultades = Facultad.objects.prefetch_related('programas').all()
    programas  = Programa.objects.select_related('facultad').all()

    # Leer parámetros GET
    facultad_id = request.GET.get('facultad')
    programa_id = request.GET.get('programa')

    horarios = (
        Horario.objects
        .select_related('materia', 'materia__programa', 'materia__programa__facultad', 'materia__profesor')
        .all()
    )

    # Aplicar filtros si se pasaron
    if facultad_id:
        horarios = horarios.filter(materia__programa__facultad_id=facultad_id)
        programas = programas.filter(facultad_id=facultad_id)  # limitar select de programas

    if programa_id:
        horarios = horarios.filter(materia__programa_id=programa_id)

    # Ordenar: día de la semana y luego por hora
    ORDEN_DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
    horarios = sorted(horarios, key=lambda h: (ORDEN_DIAS.index(h.dia), h.hora_inicio))

    context = {
        'horarios':    horarios,
        'facultades':  facultades,
        'programas':   programas,
        'facultad_id': facultad_id,
        'programa_id': programa_id,
    }
    return render(request, 'core/lista_horarios.html', context)


def lista_facultades(request):
    """Vista de resumen: todas las facultades con sus programas y materias."""
    facultades = Facultad.objects.prefetch_related(
        'programas',
        'programas__materias',
        'programas__materias__profesor',
    ).all()

    context = {'facultades': facultades}
    return render(request, 'core/facultades.html', context)
