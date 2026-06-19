# Sistema de Gestión de Horarios Universitarios

Aplicación web desarrollada con **Django 6** para administrar horarios académicos de una universidad. Permite gestionar facultades, programas, profesores, materias y horarios de clase.

---

## Tecnologías

- Python 3
- Django 6
- SQLite (base de datos por defecto)
- Bootstrap 5 (frontend)

---

## Estructura del proyecto

```
sistema_horarios/
├── core/                   # App principal
│   ├── models.py           # Modelos: Facultad, Programa, Profesor, Materia, Horario
│   ├── admin.py            # Configuración del panel de administración
│   ├── views.py            # Vistas con filtros y consultas a la base de datos
│   ├── urls.py             # Rutas de la app
│   └── tests.py            # Suite de 24 pruebas (unitarias, integración, BD, endpoints)
├── universidad/            # Configuración del proyecto Django
│   ├── settings.py
│   └── urls.py
├── templates/              # Templates HTML con Bootstrap 5
│   ├── base.html
│   └── core/
│       ├── lista_horarios.html
│       └── facultades.html
├── manage.py
└── requirements.txt
```

---

## Modelos y relaciones

```
Facultad
   └── Programa (ForeignKey → Facultad, CASCADE)
         └── Materia (ForeignKey → Programa, CASCADE)
               └── Horario (ForeignKey → Materia, CASCADE)

Profesor (ForeignKey → Materia, SET_NULL)
```

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/Poli1210/sistema-horarios-universitarios.git
cd sistema-horarios-universitarios
```

### 2. Crear y activar el entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario (para acceder al admin)

```bash
python manage.py createsuperuser
```

### 6. Correr el servidor

```bash
python manage.py runserver
```

---

## URLs disponibles

| URL | Descripción |
|-----|-------------|
| `http://127.0.0.1:8000/` | Lista de horarios con filtros por facultad y programa |
| `http://127.0.0.1:8000/facultades/` | Resumen de facultades y programas |
| `http://127.0.0.1:8000/admin/` | Panel de administración (CRUD completo) |

---

## Consultas a la base de datos

Las consultas principales se encuentran en `core/views.py`:

```python
# Consulta con filtros encadenados y optimización de relaciones
horarios = (
    Horario.objects
    .select_related(
        'materia',
        'materia__programa',
        'materia__programa__facultad',
        'materia__profesor'
    )
    .all()
)

# Filtro por facultad
horarios = horarios.filter(materia__programa__facultad_id=facultad_id)

# Filtro por programa
horarios = horarios.filter(materia__programa_id=programa_id)
```

---

## Pruebas

El proyecto incluye una suite de **24 pruebas** organizadas en 4 categorías:

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| Unitarias | 5 | Validaciones del modelo Horario y __str__() |
| Base de datos | 6 | CRUD e integridad referencial (CASCADE, SET_NULL) |
| Integración | 9 | Vistas, filtros y contenido HTML |
| API / Endpoints | 4 | Códigos de estado HTTP y Django Admin |

### Ejecutar las pruebas

```bash
python manage.py test core --verbosity=2
```

Resultado esperado:
```
Ran 24 tests in X.XXXs
OK
```

---

## Autor

- **Nombre:** Guillermo  
- **Curso:** Lenguajes de Programación para Aplicaciones en la Nube  
