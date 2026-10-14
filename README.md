# DataPulse Latam — Mission Indicators

Plataforma fullstack para monitorear indicadores económicos de Latinoamérica, calcular el índice de riesgo país compuesto (IRPC), gestionar portafolios de inversión simulados y emitir alertas automáticas.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Django 6 + Django REST Framework + SimpleJWT |
| Frontend | Angular 22 + Angular Material + Chart.js |
| Base de datos | PostgreSQL |
| Deploy | Backend en Render, frontend en Vercel |

## Arquitectura

```
frontend/appMission  →  Angular SPA (JWT Bearer)
        │
        ▼
backend/apiMission   →  DRF API envelope {status, message, data}
        │
        ▼
PostgreSQL           →  usuarios, paises, indicadores, FX, IRPC, portafolios, alertas
        │
        ▼
APIs externas        →  World Bank, ExchangeRate-API, REST Countries
```

### Decisiones técnicas

- Respuestas unificadas con envelope `{status, message, data}` y paginación estándar.
- Auth JWT con rotación/blacklist de refresh tokens.
- Soft-delete en portafolios y cierre de posiciones con `fecha_salida`.
- IRPC calculado en servicio de dominio (`irpc_service`) tras sync de indicadores.
- Sync World Bank / FX / REST Countries vía endpoints ADMIN y management commands.
- Frontend con lazy loading, guards, interceptors (JWT, loading, errores) y Chart.js.

## Setup local

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # ajustar credenciales Postgres
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

API local: `http://127.0.0.1:8000/api/`

### Frontend

```bash
cd frontend/appMission
npm install
copy .env.example .env   # NG_APP_API_BASE_URL=http://127.0.0.1:8000
npm start
```

App local: `http://localhost:4200`

### Postgres con Docker

```bash
cd backend
docker compose -f docker.compose.yaml up -d
```

## Variables de entorno

Ver `backend/.env.example` y `frontend/appMission/.env.example`.

Claves relevantes del backend: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`, `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`.

## Usuarios seed

Tras `seed_data` (ajustar si el seeder define otros):

| Email | Rol |
|-------|-----|
| admin@datapulse.com | ADMIN |
| analista@datapulse.com | ANALISTA |
| viewer@datapulse.com | VIEWER |

## Management commands

```bash
python manage.py seed_data
python manage.py sync_indicadores --years 5
python manage.py sync_tipos_cambio
python manage.py sync_paises_restcountries
```

`sync_indicadores` sincroniza World Bank y luego recalcula IRPC + alertas.

## Endpoints principales

| Área | Base |
|------|------|
| Auth | `/api/auth/` |
| Países | `/api/paises/` |
| Riesgo | `/api/riesgo/` |
| Portafolios | `/api/portafolios/` |
| Alertas | `/api/alertas/` |
| Dashboard | `/api/dashboard/` |

Admin-only: `POST /api/paises/sync-indicadores/`, `POST /api/paises/sync-tipos-cambio/`, `POST /api/riesgo/calcular/`.

## Tests

```bash
cd backend
python manage.py test apps.countries apps.users
```

## Deploy

| Servicio | URL (ejemplo) |
|----------|----------------|
| Frontend | https://app-inidicadores-economicos-mission.vercel.app |
| Backend | URL pública de Render (configurar `CORS_ALLOWED_ORIGINS` y `FRONTEND_URL`) |

En Render definir las mismas variables que en `.env.example` apuntando a la DB managed. En Vercel, `NG_APP_API_BASE_URL` debe apuntar al backend.

## Estructura del repo

```
backend/          Django project (apiMission) + apps
frontend/appMission/   Angular SPA
docs/             Enunciado de la prueba técnica
```
