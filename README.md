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

## Roles y permisos

| Rol                | Acceso                                                              |
| ------------------ | ------------------------------------------------------------------- |
| `admin`            | Todo: gestión completa de la plataforma                             |
| `stimada_employee` | Content Makers, Clientes, Proyectos (crear/editar/eliminar)         |
| `client`           | Ver sus proyectos, seleccionar Content Makers cuando se le solicita |
| `content_maker`    | Ver proyectos asignados/pendientes, aceptar/rechazar participación  |

## Funcionalidades

### Gestión de Content Makers

- CRUD completo con importación desde CSV
- Búsqueda y filtros por nombre, estado, tipo, sexo, calidad, seguidores
- Creación de cuenta de acceso a la plataforma para cada CM
- Paginación

### Gestión de Clientes

- CRUD completo con soporte para agencias y marcas
- Creación de cuenta de acceso a la plataforma
- Asociación de marcas (Brand) por cliente

### Gestión de Proyectos

- **Creación** (solo admin/empleados): wizard de 4 pasos (Cliente → Detalles → Content Maker → Resumen)
- **Modos de selección de Content Maker:**
  - `Definida`: el admin/empleado asigna una CM directamente
  - `Recomendadas`: el admin/empleado sugiere varias CMs para que el cliente elija
  - `El cliente elige`: el cliente busca y selecciona la CM que quiera
- **Detalle del proyecto** (`/proyectos/{id}`): accesible desde la lista, muestra info completa
- **Edición** (solo admin/empleados): modificar nombre, descripción, precios, fechas, estado
- **Desvincular Content Maker**: los admin/empleados pueden quitar la CM asignada
- **Eliminar proyecto**: con confirmación, solo admin/empleados
- **Aceptar/rechazar** (Content Makers): banner de acción cuando tienen una solicitud pendiente

### Sistema de Notificaciones

- Notificaciones en tiempo real en la barra de navegación
- **Clickable**: al pulsar una notificación, navega al proyecto relacionado
- Marcado de leídas (individual y masivo)
- Flujo de notificaciones:
  - Al crear proyecto → notifica al cliente
  - Al seleccionar CM (modo client_chooses) → notifica a la CM seleccionada
  - CM acepta → notifica a cliente y admin/creador
  - CM rechaza → notifica a cliente (pidiéndole elegir otra CM) y admin/creador
  - CM definida directamente → notifica a la CM para que acepte/rechace

### Navegación por roles

- **Admin/Empleado**: Inicio, Dashboard, Proyectos (con sidebar de gestión completa)
- **Cliente**: Inicio, Mis proyectos (lista de sus proyectos con estado)
- **Content Maker**: Inicio, Mis campañas (proyectos asignados y pendientes)

### Landing page (`/inicio`)

- Saludo personalizado según hora del día
- Accesos rápidos según rol
- Para clientes y CMs: lista de proyectos actuales con enlaces directos al detalle

### Gestión de Usuarios

- CRUD de usuarios internos (admin, empleados)
- Reseteo de contraseña

## Estructura del proyecto

```
stimada/
├── backend/           # Django 5 + DRF
│   ├── apps/
│   │   ├── accounts/       # Auth, usuarios, JWT
│   │   ├── clients/        # Clientes y marcas
│   │   ├── content_makers/ # Perfiles de CMs
│   │   └── projects/       # Proyectos, notificaciones
│   ├── config/             # Settings, URLs, WSGI
│   └── data/               # CSV de importación
├── frontend/          # Nuxt 3 + Pinia + Tailwind
│   ├── components/         # Componentes UI
│   ├── layouts/            # app (navbar), default (navbar+sidebar)
│   ├── pages/              # Rutas de la app
│   ├── stores/             # Pinia stores
│   └── middleware/         # Auth, roles
└── docker-compose.yml
```

## API Endpoints principales

| Método | Endpoint                             | Descripción                              |
| ------ | ------------------------------------ | ---------------------------------------- |
| GET    | `/api/projects/`                     | Listar proyectos (filtrado por rol)      |
| POST   | `/api/projects/`                     | Crear proyecto (solo admin/empleados)    |
| GET    | `/api/projects/{id}/`                | Detalle de proyecto                      |
| PATCH  | `/api/projects/{id}/`                | Editar proyecto (solo admin/empleados)   |
| DELETE | `/api/projects/{id}/`                | Eliminar proyecto (solo admin/empleados) |
| POST   | `/api/projects/{id}/accept/`         | CM acepta proyecto                       |
| POST   | `/api/projects/{id}/reject/`         | CM rechaza proyecto                      |
| POST   | `/api/projects/{id}/select_cm/`      | Cliente selecciona CM                    |
| GET    | `/api/projects/search_cms/?q=`       | Búsqueda de CMs para selección           |
| GET    | `/api/projects/filters/`             | Filtros (estados, tipos de servicio)     |
| GET    | `/api/notifications/`                | Listar notificaciones                    |
| GET    | `/api/notifications/unread_count/`   | Contador de no leídas                    |
| PATCH  | `/api/notifications/{id}/mark_read/` | Marcar leída                             |
| POST   | `/api/notifications/mark_all_read/`  | Marcar todas leídas                      |
| GET    | `/api/content-makers/`               | Listar CMs                               |
| GET    | `/api/clients/`                      | Listar clientes                          |

## Stack

- **Backend:** Django 5 + Django REST Framework + SimpleJWT
- **Frontend:** Nuxt 3 + Pinia + Tailwind CSS
- **Base de datos:** PostgreSQL 16
- **Cache:** Redis 7
- **Deploy:** Docker Compose
