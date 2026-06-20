"""
Vistas del sistema de horarios universitarios.
"""

from django.shortcuts import render
from .models import Facultad, Programa, Horario


def lista_horarios(request):
    facultades = Facultad.objects.prefetch_related('programas').all()
    programas  = Programa.objects.select_related('facultad').all()

    facultad_id = request.GET.get('facultad')
    programa_id = request.GET.get('programa')

    horarios = (
        Horario.objects
        .select_related('materia', 'materia__programa', 'materia__programa__facultad', 'materia__profesor')
        .all()
    )

    if facultad_id:
        horarios  = horarios.filter(materia__programa__facultad_id=facultad_id)
        programas = programas.filter(facultad_id=facultad_id)

    if programa_id:
        horarios = horarios.filter(materia__programa_id=programa_id)

    ORDEN_DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
    horarios = sorted(horarios, key=lambda h: (ORDEN_DIAS.index(h.dia), h.hora_inicio))

    return render(request, 'core/lista_horarios.html', {
        'horarios':    horarios,
        'facultades':  facultades,
        'programas':   programas,
        'facultad_id': facultad_id,
        'programa_id': programa_id,
    })


def lista_facultades(request):
    facultades = Facultad.objects.prefetch_related(
        'programas', 'programas__materias', 'programas__materias__profesor',
    ).all()
    return render(request, 'core/facultades.html', {'facultades': facultades})


# ── API de Automatrícula con IA (Groq - gratuita) ────────────────────────────

import json
import urllib.request
import urllib.error
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

RANGOS_JORNADA = {
    'diurno':   (6,  17),
    'nocturno': (17, 23),
    'virtual':  (0,  24),
}

DIAS_JORNADA = {
    'diurno':   ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
    'nocturno': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'],
    'virtual':  ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'],
}


def _filtrar_horarios_por_jornada(jornada):
    """Lógica fija: filtra horarios según la jornada del estudiante."""
    hora_min, hora_max = RANGOS_JORNADA.get(jornada, (0, 24))
    dias_validos = DIAS_JORNADA.get(jornada, [])

    horarios_qs = (
        Horario.objects
        .select_related('materia', 'materia__programa', 'materia__programa__facultad', 'materia__profesor')
        .filter(dia__in=dias_validos)
        .filter(hora_inicio__hour__gte=hora_min)
        .filter(hora_inicio__hour__lt=hora_max)
    )

    return [{
        'materia':  h.materia.nombre,
        'programa': h.materia.programa.nombre,
        'facultad': h.materia.programa.facultad.nombre,
        'profesor': h.materia.profesor.nombre if h.materia.profesor else 'Sin asignar',
        'dia':      h.get_dia_display(),
        'inicio':   h.hora_inicio.strftime('%H:%M'),
        'fin':      h.hora_fin.strftime('%H:%M'),
        'salon':    h.salon,
    } for h in horarios_qs]


def _consultar_ia(jornada, semestre, horarios_disponibles):
    """
    Llama a Groq (gratuita, modelo llama-3.3-70b) para recomendar
    las mejores materias según el perfil del estudiante.
    """
    from django.conf import settings

    if not horarios_disponibles:
        return "No hay horarios disponibles para tu jornada en este momento."

    lineas = [
        "- {materia} ({programa}) | {dia} {inicio}-{fin} | Salon {salon} | Prof. {profesor}".format(**h)
        for h in horarios_disponibles
    ]
    horarios_texto = "\n".join(lineas)

    prompt = (
        "Eres un asistente de automatricula universitaria.\n\n"
        "Un estudiante de jornada " + jornada.upper() + " en semestre " + semestre + " necesita matricularse.\n\n"
        "Estos son los horarios disponibles para su jornada:\n"
        + horarios_texto +
        "\n\nTu tarea:\n"
        "1. Selecciona entre 4 y 5 materias que formen un horario equilibrado para semestre " + semestre + ".\n"
        "2. Evita cruces de horario (misma hora en el mismo dia).\n"
        "3. Prioriza variedad de dias y carga academica razonable.\n"
        "4. Explica brevemente por que recomiendas esas materias.\n\n"
        "Responde en espanol, de forma clara y estructurada."
    )

    payload = json.dumps({
        "model":      "llama-3.3-70b-versatile",
        "max_tokens": 1000,
        "messages":   [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": "Bearer " + settings.ANTHROPIC_API_KEY,
            "User-Agent":    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


@csrf_exempt
@require_http_methods(["POST"])
def api_automatricula(request):
    """
    POST /api/automatricula/
    Body JSON: { "jornada": "nocturno", "semestre": "3" }
    """
    try:
        body     = json.loads(request.body)
        jornada  = body.get("jornada", "").lower().strip()
        semestre = body.get("semestre", "").strip()

        if jornada not in RANGOS_JORNADA:
            return JsonResponse(
                {"error": "Jornada invalida. Opciones: diurno, nocturno, virtual"}, status=400
            )

        if not semestre or not semestre.isdigit() or not (1 <= int(semestre) <= 10):
            return JsonResponse(
                {"error": "Semestre invalido. Debe ser un numero entre 1 y 10."}, status=400
            )

        horarios_disponibles = _filtrar_horarios_por_jornada(jornada)
        recomendacion_ia     = _consultar_ia(jornada, semestre, horarios_disponibles)

        return JsonResponse({
            "estudiante":           {"jornada": jornada, "semestre": semestre},
            "horarios_disponibles": horarios_disponibles,
            "total_disponibles":    len(horarios_disponibles),
            "recomendacion_ia":     recomendacion_ia,
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "El cuerpo debe ser JSON valido."}, status=400)
    except urllib.error.URLError as e:
        return JsonResponse({"error": "Error al conectar con la IA: " + str(e)}, status=503)
    except Exception as e:
        return JsonResponse({"error": "Error interno: " + str(e)}, status=500)


def vista_automatricula(request):
    """Vista HTML para probar la automatricula desde el navegador."""
    return render(request, "core/automatricula.html")
