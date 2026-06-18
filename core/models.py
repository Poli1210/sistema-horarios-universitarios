"""
Modelos del sistema de gestión de horarios universitarios.

Relaciones:
  Facultad → Programa → Materia ← Profesor
  Materia → Horario
"""

from django.db import models
from django.core.exceptions import ValidationError


class Facultad(models.Model):
    """Facultad de la universidad (ej: Ingeniería, Ciencias)."""
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre")

    class Meta:
        verbose_name = "Facultad"
        verbose_name_plural = "Facultades"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Programa(models.Model):
    """Programa académico perteneciente a una Facultad."""
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.CASCADE,
        related_name='programas',
        verbose_name="Facultad"
    )

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"
        ordering = ['facultad__nombre', 'nombre']
        unique_together = ('nombre', 'facultad')

    def __str__(self):
        return f"{self.nombre} — {self.facultad}"


class Profesor(models.Model):
    """Docente que imparte materias."""
    nombre = models.CharField(max_length=200, verbose_name="Nombre completo")
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    """Asignatura que pertenece a un Programa y es impartida por un Profesor."""
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='materias',
        verbose_name="Programa"
    )
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materias',
        verbose_name="Profesor"
    )

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ['programa__nombre', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.programa})"


class Horario(models.Model):
    """Horario de clase: define cuándo y dónde se dicta una materia."""

    DIAS = [
        ('lunes',     'Lunes'),
        ('martes',    'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves',    'Jueves'),
        ('viernes',   'Viernes'),
        ('sabado',    'Sábado'),
    ]

    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='horarios',
        verbose_name="Materia"
    )
    dia = models.CharField(
        max_length=10,
        choices=DIAS,
        verbose_name="Día"
    )
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin    = models.TimeField(verbose_name="Hora de fin")
    salon       = models.CharField(max_length=100, verbose_name="Salón")

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ['dia', 'hora_inicio']

    def clean(self):
        """Valida que hora_fin sea posterior a hora_inicio."""
        if self.hora_inicio and self.hora_fin:
            if self.hora_fin <= self.hora_inicio:
                raise ValidationError({
                    'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio.'
                })

    def __str__(self):
        return (
            f"{self.materia.nombre} — {self.get_dia_display()} "
            f"{self.hora_inicio.strftime('%H:%M')}–{self.hora_fin.strftime('%H:%M')} "
            f"({self.salon})"
        )
