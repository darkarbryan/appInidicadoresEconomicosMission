# DataPulse Latam — Mission Indicators

Plataforma **fullstack** para consultoría financiera sobre mercados latinoamericanos.

Centraliza indicadores económicos, tipos de cambio, cálculo del **Índice de Riesgo País Compuesto (IRPC)**, portafolios de inversión simulados, alertas automáticas y un dashboard para la toma de decisiones.

## ¿De qué trata?

DataPulse Latam necesita dejar de recopilar datos en hojas de cálculo. Esta aplicación permite:

- Consultar países de LatAm con indicadores (PIB, inflación, desempleo, etc.)
- Sincronizar datos desde **World Bank**, **ExchangeRate-API** y **REST Countries**
- Calcular y clasificar riesgo país (BAJO → CRÍTICO)
- Armar portafolios con posiciones y exportar PDF
- Recibir alertas (IRPC, FX, hiperinflación, sync)
- Visualizar KPIs, ranking, tendencias (Chart.js) y mapa de riesgo

## Estructura del repositorio

```
appIndicadoresEconomicosMission/
├── backend/                 # API Django + DRF
├── frontend/appMission/     # SPA Angular + Material
├── docs/                    # Enunciado de la prueba técnica
└── README.md                # Este archivo
```

Detalle de setup:

- [Backend](./backend/README.md)
- [Frontend](./frontend/appMission/README.md)

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Django 6 + Django REST Framework + SimpleJWT |
| Frontend | Angular 22 + Angular Material + Chart.js |
| Base de datos | PostgreSQL 16 |
| Deploy | Backend en Render, frontend en Vercel |

## Requisitos previos

- Python **3.12+** (probado con 3.13)
- Node.js **≥ 22.22.3** y npm
- PostgreSQL **16** (local o Docker)
- Git

## Levantamiento local (resumen)

### 1. Base de datos

Con Docker (desde `backend/`):

```bash
cd backend
# Copia .env.example → .env y ajusta DB_*
docker compose -f docker.compose.yaml up -d
```

O usa un PostgreSQL local con la misma base/usuario/clave del `.env`.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # o: cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

API: **http://127.0.0.1:8000/api/**

### 3. Frontend

```bash
cd frontend/appMission
npm install
npm start
```

App: **http://localhost:4200**

Por defecto el frontend apunta al API en **Render**. Para usar el backend local, edita `src/environments/environment.development.ts` y deja:

```ts
apiBaseUrl: 'http://127.0.0.1:8000',
```

Asegura CORS en el `.env` del backend:

```env
FRONTEND_URL=http://localhost:4200
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

## Usuarios de prueba (seed)

Contraseña para todos: **`DataPulse2026!`**

| Email | Rol |
|-------|-----|
| `admin@datapulse.com` | ADMIN |
| `analista@datapulse.com` | ANALISTA |
| `viewer@datapulse.com` | VIEWER |

## Arquitectura (alto nivel)

```
Angular SPA (JWT)  →  Django REST API  →  PostgreSQL
                           │
                           ▼
              World Bank / ExchangeRate-API / REST Countries
```

Respuestas API con envelope `{ status, message, data }`.

## Deploy

| Servicio | URL de ejemplo |
|----------|----------------|
| Frontend | https://app-inidicadores-economicos-mission.vercel.app |
| Backend | https://appinidicadoreseconomicosmission.onrender.com |

En producción configura `CORS_ALLOWED_ORIGINS` / `FRONTEND_URL` en Render y la URL del API en los `environment*.ts` del frontend (o variables de build en Vercel).

## Licencia / contexto

Proyecto de **prueba técnica fullstack** (Angular + Django). Ver `docs/Prueba_Tecnica_Desarrollador.pdf`.
