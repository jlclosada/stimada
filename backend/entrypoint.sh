#!/bin/sh
set -e

echo "Esperando a PostgreSQL..."
until python -c "
import os, psycopg2
psycopg2.connect(os.environ.get('DATABASE_URL', 'postgres://stimada:stimada@db:5432/stimada'))
" 2>/dev/null; do
  sleep 1
done

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Creando admin inicial..."
python manage.py seed_admin

echo "Importando content makers desde CSV..."
python manage.py import_content_makers --csv /app/data/comunidad.csv

echo "Iniciando servidor..."
exec "$@"
