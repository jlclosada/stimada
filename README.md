# Stimada

Plataforma interna de gestión para la agencia creativa Stimada. Django 5 + Nuxt 3 + PostgreSQL.

## Requisitos

- Docker Desktop

## Puesta en marcha (primera vez)

```bash
# 1. Clona el repositorio
git clone https://github.com/jlclosada/stimada.git
cd stimada

# 2. Copia los archivos de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Levanta los servicios
docker compose up --build
```

Al arrancar, el backend automáticamente:
- Aplica todas las migraciones
- Crea el usuario administrador (`admin@stimada.com` / `Stimada2025!`)
- Importa las 267 content makers desde el CSV incluido en el repositorio

La app estará disponible en:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api
- **Admin Django:** http://localhost:8000/admin

## Roles

| Rol | Acceso |
|-----|--------|
| `admin` | Todo |
| `stimada_employee` | Content Makers, Clientes |
| `client` | Sus proyectos |
| `content_maker` | Sus contenidos |

## Stack

- **Backend:** Django 5 + Django REST Framework + SimpleJWT
- **Frontend:** Nuxt 3 + Pinia + Tailwind CSS
- **Base de datos:** PostgreSQL 16
- **Cache:** Redis 7
