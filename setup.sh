#!/bin/bash
# Script de configuración inicial del proyecto sistema_horarios
echo "=== Sistema de Horarios Universitarios ==="
echo ""

# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Migraciones
python manage.py migrate

# 4. Superusuario (admin / admin123)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin / admin123')
"

echo ""
echo "Listo. Ejecuta:  python manage.py runserver"
echo "Luego abre:      http://127.0.0.1:8000/"
echo "Admin:           http://127.0.0.1:8000/admin/  (admin / admin123)"
