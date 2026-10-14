# Backend — DataPulse Mission API

API REST del proyecto **DataPulse Latam**. Expone autenticación JWT, países e indicadores, riesgo (IRPC), portafolios, alertas y dashboard.

Stack: **Django 6**, **Django REST Framework**, **SimpleJWT**, **PostgreSQL**, **django-cors-headers**.

## ¿Qué hace este backend?

- Auth: registro, login, refresh, perfil, logout, recuperación de contraseña
- Países: listado/detalle, indicadores, tipos de cambio, sync ADMIN
- Riesgo: ranking IRPC, histórico, recálculo ADMIN (con alertas de negocio)
- Portafolios: CRUD, posiciones, resumen, export PDF
- Alertas: listado, marcar leídas, resumen / badge
- Dashboard: KPIs, mapa de riesgo, tendencias
- Integraciones: World Bank, ExchangeRate-API, REST Countries
- Envelope uniforme `{ status, message, data }` + paginación + throttling

## Requisitos

- Python 3.12+
- PostgreSQL 16
- (Opcional) Docker para levantar solo la DB

## Setup local

### 1. Entorno virtual e dependencias

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
# Windows
copy .env.example .env

# Linux / macOS
# cp .env.example .env
```

Ajusta al menos:

```env
SECRET_KEY=tu-clave-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=app_mission
DB_USER=us3r_missi0n
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=5432

FRONTEND_URL=http://localhost:4200
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### 3. PostgreSQL

**Opción A — Docker** (usa las variables `DB_*` del `.env`):

```bash
docker compose -f docker.compose.yaml up -d
```

**Opción B — Postgres instalado**: crea la base y el usuario con los mismos valores del `.env`.

### 4. Migraciones y datos semilla

```bash
python manage.py migrate
python manage.py seed_data
```

`seed_data` carga usuarios, 10 países LatAm, indicadores, FX de ejemplo, IRPC, portafolios y alertas.

### 5. Servidor de desarrollo

```bash
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/
- Admin Django: http://127.0.0.1:8000/admin/ (usuario ADMIN del seed)

## Usuarios seed

Contraseña: **`DataPulse2026!`**

| Email | Rol |
|-------|-----|
| `admin@datapulse.com` | ADMIN |
| `analista@datapulse.com` | ANALISTA |
| `viewer@datapulse.com` | VIEWER |

## Management commands útiles

```bash
# Datos de prueba
python manage.py seed_data
python manage.py seed_data --flush   # limpia y vuelve a sembrar (según implementación)

# World Bank + recálculo IRPC/alertas
python manage.py sync_indicadores --years 5

# Tipos de cambio diarios
python manage.py sync_tipos_cambio

# Banderas / población / coords (REST Countries)
python manage.py sync_paises_restcountries
```

## Apps Django

| App | Responsabilidad |
|-----|-----------------|
| `apps.users` | Usuario custom, auth JWT |
| `apps.countries` | Países, indicadores, FX, IRPC, sync |
| `apps.portfolios` | Portafolios, posiciones, PDF |
| `apps.alerts` | Alertas |
| `apps.activity` | Log de actividad |
| `apps.dashboard` | Agregados del dashboard |

Proyecto: `apiMission/` (`settings.py`, URLs, middleware, envelope).

## Endpoints (base)

| Área | Prefijo |
|------|---------|
| Auth | `/api/auth/` |
| Países | `/api/paises/` |
| Riesgo | `/api/riesgo/` |
| Portafolios | `/api/portafolios/` |
| Alertas | `/api/alertas/` |
| Dashboard | `/api/dashboard/` |

Solo **ADMIN**:

- `POST /api/paises/sync-indicadores/`
- `POST /api/paises/sync-tipos-cambio/`
- `POST /api/riesgo/calcular/`

Auth de API: header `Authorization: Bearer <access_token>`.

## Tests

```bash
python manage.py test apps.countries
# u otros módulos cuando existan tests
```

## Deploy (Render)

1. Servicio web + PostgreSQL managed
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn apiMission.wsgi:application`
4. Migraciones / seed en release command o shell
5. Variables: las de `.env.example` + `ALLOWED_HOSTS` del host Render
6. Incluir el origen de Vercel en `CORS_ALLOWED_ORIGINS` y `FRONTEND_URL`

## Relación con el frontend

Documentación de la SPA: [../frontend/appMission/README.md](../frontend/appMission/README.md)

README general del monorepo: [../README.md](../README.md)
