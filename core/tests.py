"""
Suite de pruebas para el Sistema de Horarios Universitarios.

Organizada según los 4 tipos descritos en el manual de pruebas de backend:
  1. Pruebas Unitarias    -> validan una sola función/método aislado
  2. Pruebas de Integración -> validan vistas completas (HTTP + BD + template)
  3. Pruebas de Base de Datos -> validan operaciones CRUD y relaciones
  4. Pruebas de API/Endpoints -> validan códigos de estado HTTP y contenido

Ejecutar todo:
    python manage.py test core --verbosity=2

Ejecutar solo una clase:
    python manage.py test core.tests.HorarioValidacionTest --verbosity=2
"""

from datetime import time

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Facultad, Programa, Profesor, Materia, Horario


# ════════════════════════════════════════════════════════════════════════
# 1. PRUEBAS UNITARIAS
#    Objetivo: probar una sola función/método de forma aislada.
# ════════════════════════════════════════════════════════════════════════

class HorarioValidacionTest(TestCase):
    """Prueba unitaria del método clean() del modelo Horario."""

    def setUp(self):
        """
        ARRANGE: se ejecuta antes de CADA prueba.
        Crea los datos mínimos necesarios (fixtures) para no depender
        de datos reales ni de otras pruebas (principio de aislamiento).
        """
        facultad = Facultad.objects.create(nombre="Facultad de Ingeniería")
        programa = Programa.objects.create(nombre="Ingeniería de Sistemas", facultad=facultad)
        profesor = Profesor.objects.create(nombre="Carlos Ramírez", email="carlos@uni.edu.co")
        self.materia = Materia.objects.create(
            nombre="Programación I", programa=programa, profesor=profesor
        )

    def test_hora_fin_mayor_que_inicio_es_valido(self):
        """CASO FELIZ: hora_fin > hora_inicio no debe lanzar ningún error."""
        # ACT
        horario = Horario(
            materia=self.materia, dia='lunes',
            hora_inicio=time(7, 0), hora_fin=time(9, 0), salon='A-101'
        )
        # ASSERT: full_clean() no debe lanzar excepción
        try:
            horario.full_clean()
        except ValidationError:
            self.fail("full_clean() lanzó ValidationError con un horario válido")

    def test_hora_fin_menor_que_inicio_lanza_error(self):
        """CASO LÍMITE: hora_fin antes de hora_inicio debe ser rechazado."""
        horario = Horario(
            materia=self.materia, dia='lunes',
            hora_inicio=time(9, 0), hora_fin=time(7, 0), salon='A-101'
        )
        with self.assertRaises(ValidationError):
            horario.full_clean()

    def test_hora_fin_igual_a_inicio_lanza_error(self):
        """CASO LÍMITE: horas iguales (duración cero) también deben fallar."""
        horario = Horario(
            materia=self.materia, dia='lunes',
            hora_inicio=time(8, 0), hora_fin=time(8, 0), salon='A-101'
        )
        with self.assertRaises(ValidationError):
            horario.full_clean()

    def test_str_facultad(self):
        """Prueba unitaria simple de __str__()."""
        facultad = Facultad.objects.create(nombre="Facultad de Ciencias")
        self.assertEqual(str(facultad), "Facultad de Ciencias")

    def test_str_horario_incluye_dia_y_salon(self):
        """Prueba que la representación en texto del Horario sea legible."""
        horario = Horario.objects.create(
            materia=self.materia, dia='martes',
            hora_inicio=time(10, 0), hora_fin=time(12, 0), salon='B-203'
        )
        texto = str(horario)
        self.assertIn('Martes', texto)
        self.assertIn('B-203', texto)


# ════════════════════════════════════════════════════════════════════════
# 2. PRUEBAS DE BASE DE DATOS
#    Objetivo: validar operaciones CREATE / READ / UPDATE / DELETE
#    y la integridad de las relaciones entre modelos.
# ════════════════════════════════════════════════════════════════════════

class FacultadProgramaCRUDTest(TestCase):
    """CRUD básico sobre Facultad y Programa."""

    def test_crear_facultad(self):
        """CREATE: una facultad se guarda correctamente."""
        facultad = Facultad.objects.create(nombre="Facultad de Ciencias")
        self.assertEqual(Facultad.objects.count(), 1)
        self.assertEqual(facultad.nombre, "Facultad de Ciencias")

    def test_leer_facultad(self):
        """READ: se puede recuperar una facultad por su nombre."""
        Facultad.objects.create(nombre="Facultad de Ingeniería")
        facultad = Facultad.objects.get(nombre="Facultad de Ingeniería")
        self.assertIsNotNone(facultad)

    def test_actualizar_facultad(self):
        """UPDATE: el nombre se actualiza y persiste en la base de datos."""
        facultad = Facultad.objects.create(nombre="Nombre Viejo")
        facultad.nombre = "Nombre Nuevo"
        facultad.save()
        facultad.refresh_from_db()
        self.assertEqual(facultad.nombre, "Nombre Nuevo")

    def test_eliminar_facultad(self):
        """DELETE: la facultad desaparece de la base de datos."""
        facultad = Facultad.objects.create(nombre="Facultad Temporal")
        facultad_id = facultad.id
        facultad.delete()
        self.assertFalse(Facultad.objects.filter(id=facultad_id).exists())

    def test_eliminar_facultad_elimina_programas_en_cascada(self):
        """
        Integridad referencial: al borrar una Facultad (on_delete=CASCADE),
        sus Programas asociados también deben eliminarse.
        """
        facultad = Facultad.objects.create(nombre="Facultad de Artes")
        Programa.objects.create(nombre="Diseño", facultad=facultad)
        self.assertEqual(Programa.objects.count(), 1)

        facultad.delete()
        self.assertEqual(Programa.objects.count(), 0)


class MateriaProfesorRelacionTest(TestCase):
    """Pruebas de la relación opcional Materia -> Profesor (SET_NULL)."""

    def test_eliminar_profesor_no_elimina_materia(self):
        """
        Al borrar un Profesor (on_delete=SET_NULL), la Materia debe
        seguir existiendo, pero con profesor=None.
        """
        facultad = Facultad.objects.create(nombre="Facultad X")
        programa = Programa.objects.create(nombre="Programa X", facultad=facultad)
        profesor = Profesor.objects.create(nombre="Laura Gómez", email="laura@uni.edu.co")
        materia = Materia.objects.create(nombre="Base de Datos", programa=programa, profesor=profesor)

        profesor.delete()
        materia.refresh_from_db()

        self.assertEqual(Materia.objects.count(), 1)
        self.assertIsNone(materia.profesor)


# ════════════════════════════════════════════════════════════════════════
# 3. PRUEBAS DE INTEGRACIÓN
#    Objetivo: validar que vista + modelo + base de datos + template
#    funcionen juntos correctamente (simulan una petición HTTP real).
# ════════════════════════════════════════════════════════════════════════

class ListaHorariosIntegracionTest(TestCase):
    """Pruebas de integración sobre la vista principal de horarios."""

    def setUp(self):
        """Crea un escenario completo: 2 facultades, 2 programas, 2 horarios."""
        self.facultad_ing = Facultad.objects.create(nombre="Facultad de Ingeniería")
        self.facultad_cie = Facultad.objects.create(nombre="Facultad de Ciencias")

        self.programa_sis = Programa.objects.create(
            nombre="Ingeniería de Sistemas", facultad=self.facultad_ing
        )
        self.programa_mat = Programa.objects.create(
            nombre="Matemáticas", facultad=self.facultad_cie
        )

        profesor = Profesor.objects.create(nombre="Andrés Torres", email="andres@uni.edu.co")

        self.materia_sis = Materia.objects.create(
            nombre="Programación I", programa=self.programa_sis, profesor=profesor
        )
        self.materia_mat = Materia.objects.create(
            nombre="Cálculo I", programa=self.programa_mat, profesor=profesor
        )

        Horario.objects.create(
            materia=self.materia_sis, dia='lunes',
            hora_inicio=time(7, 0), hora_fin=time(9, 0), salon='A-101'
        )
        Horario.objects.create(
            materia=self.materia_mat, dia='martes',
            hora_inicio=time(9, 0), hora_fin=time(11, 0), salon='C-05'
        )

    def test_vista_responde_200(self):
        """ACT + ASSERT: la página principal debe cargar sin errores."""
        response = self.client.get(reverse('core:horarios'))
        self.assertEqual(response.status_code, 200)

    def test_vista_usa_template_correcto(self):
        """Verifica que se use el template esperado."""
        response = self.client.get(reverse('core:horarios'))
        self.assertTemplateUsed(response, 'core/lista_horarios.html')

    def test_vista_muestra_todos_los_horarios_sin_filtro(self):
        """Sin filtros, deben aparecer los 2 horarios creados en setUp."""
        response = self.client.get(reverse('core:horarios'))
        self.assertEqual(len(response.context['horarios']), 2)

    def test_filtro_por_facultad_funciona(self):
        """Filtrar por Facultad de Ingeniería solo debe devolver 1 horario."""
        response = self.client.get(
            reverse('core:horarios'), {'facultad': self.facultad_ing.id}
        )
        horarios = response.context['horarios']
        self.assertEqual(len(horarios), 1)
        self.assertEqual(horarios[0].materia, self.materia_sis)

    def test_filtro_por_programa_funciona(self):
        """Filtrar por programa de Matemáticas solo debe devolver 1 horario."""
        response = self.client.get(
            reverse('core:horarios'), {'programa': self.programa_mat.id}
        )
        horarios = response.context['horarios']
        self.assertEqual(len(horarios), 1)
        self.assertEqual(horarios[0].materia, self.materia_mat)

    def test_filtro_sin_resultados_devuelve_lista_vacia(self):
        """Un filtro que no coincide con nada debe devolver 0 horarios, no error."""
        facultad_vacia = Facultad.objects.create(nombre="Facultad Sin Horarios")
        response = self.client.get(
            reverse('core:horarios'), {'facultad': facultad_vacia.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['horarios']), 0)

    def test_contenido_html_incluye_nombre_materia(self):
        """Prueba de contenido: el HTML renderizado debe incluir el nombre de la materia."""
        response = self.client.get(reverse('core:horarios'))
        self.assertContains(response, "Programación I")
        self.assertContains(response, "Cálculo I")


class ListaFacultadesIntegracionTest(TestCase):
    """Pruebas de integración sobre la vista de resumen de facultades."""

    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Facultad de Ingeniería")
        Programa.objects.create(nombre="Ingeniería de Sistemas", facultad=self.facultad)

    def test_vista_facultades_responde_200(self):
        response = self.client.get(reverse('core:facultades'))
        self.assertEqual(response.status_code, 200)

    def test_vista_facultades_muestra_programas_asociados(self):
        response = self.client.get(reverse('core:facultades'))
        self.assertContains(response, "Facultad de Ingeniería")
        self.assertContains(response, "Ingeniería de Sistemas")


# ════════════════════════════════════════════════════════════════════════
# 4. PRUEBAS DE API / ENDPOINTS
#    Objetivo: validar códigos de estado HTTP y comportamiento de rutas,
#    incluyendo el panel de administración (Django Admin).
# ════════════════════════════════════════════════════════════════════════

class EndpointsAdminTest(TestCase):
    """Pruebas de los endpoints del Django Admin (requiere superusuario)."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin_test', email='admin_test@uni.edu.co', password='claveSegura123'
        )
        # enforce_csrf_checks=False: en pruebas no necesitamos simular el
        # token CSRF del formulario, solo validar la lógica de la vista.
        self.client = Client(enforce_csrf_checks=False)

    def test_admin_requiere_login(self):
        """Sin autenticación, el admin debe redirigir (302) al login."""
        self.client.logout()
        response = self.client.get('/admin/core/horario/')
        self.assertEqual(response.status_code, 302)

    def test_admin_login_y_acceso_horario(self):
        """Con login válido, el listado de Horario debe responder 200."""
        self.client.login(username='admin_test', password='claveSegura123')
        response = self.client.get('/admin/core/horario/')
        self.assertEqual(response.status_code, 200)

    def test_admin_crear_facultad_via_post(self):
        """
        Prueba de API tipo POST: crear una Facultad enviando datos
        directamente al formulario del admin.

        FacultadAdmin tiene un inline (ProgramaInline), así que el POST
        debe incluir también los campos de gestión del formset
        (TOTAL_FORMS, INITIAL_FORMS), aunque no se cree ningún programa.
        """
        self.client.login(username='admin_test', password='claveSegura123')
        response = self.client.post('/admin/core/facultad/add/', {
            'nombre': 'Facultad Creada Desde Test',
            # Campos obligatorios del formset inline de Programa (vacío):
            'programas-TOTAL_FORMS': '0',
            'programas-INITIAL_FORMS': '0',
            'programas-MIN_NUM_FORMS': '0',
            'programas-MAX_NUM_FORMS': '1000',
        })
        # 302 = redirección tras guardar exitosamente
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Facultad.objects.filter(nombre='Facultad Creada Desde Test').exists())


class RutasNoExistentesTest(TestCase):
    """Caso de error: rutas inexistentes deben devolver 404, no un error 500."""

    def test_ruta_inexistente_devuelve_404(self):
        response = self.client.get('/esta-ruta-no-existe/')
        self.assertEqual(response.status_code, 404)