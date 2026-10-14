# Frontend — AppMission (DataPulse Latam)

SPA en **Angular 22** + **Angular Material** + **Chart.js** para consumir la API DataPulse Mission.

Permite login/registro, dashboard (KPIs, mapa de riesgo, ranking, tendencias), catálogo de países, portafolios con gráficos y export PDF, y panel de alertas con badge.

## Requisitos

- Node.js **≥ 22.22.3**
- npm (el proyecto declara `packageManager: npm@10.9.8`)
- Backend API disponible (local o Render)

## Setup local

```bash
cd frontend/appMission
npm install
npm start
```

Equivale a `ng serve`. Abre **http://localhost:4200**

La app recarga en caliente al editar archivos.

## Conectar al API

La URL base del backend está en:

- `src/environments/environment.development.ts` → usada con `ng serve`
- `src/environments/environment.ts` → build de producción

### Opción A — Backend en Render (por defecto)

```ts
apiBaseUrl: 'https://appinidicadoreseconomicosmission.onrender.com',
```

### Opción B — Backend local

```ts
apiBaseUrl: 'http://127.0.0.1:8000',
```

El backend debe permitir CORS desde `http://localhost:4200` (ver `backend/.env` → `CORS_ALLOWED_ORIGINS`).

> Nota: el archivo `.env` / `NG_APP_API_BASE_URL` es referencia documental; la URL efectiva del cliente es la de `environment*.ts`.

## Scripts npm

| Comando | Descripción |
|---------|-------------|
| `npm start` | Servidor de desarrollo (`ng serve`) |
| `npm run build` | Build producción + copia `index.html` para Vercel SPA |
| `npm test` | Tests unitarios (Vitest) |
| `npm run watch` | Build en modo watch (development) |

## Usuarios de prueba

Si el backend tiene `seed_data` aplicado:

| Email | Password | Rol |
|-------|----------|-----|
| `admin@datapulse.com` | `DataPulse2026!` | ADMIN |
| `analista@datapulse.com` | `DataPulse2026!` | ANALISTA |
| `viewer@datapulse.com` | `DataPulse2026!` | VIEWER |

## Estructura relevante

```
src/app/
├── core/           # auth, guards, interceptors, layout, ApiService
├── features/
│   ├── auth/       # login, register, recovery, reset
│   ├── dashboard/  # KPIs, mapa, ranking, Chart.js
│   ├── paises/     # lista + detalle
│   ├── portafolios/# lista + detalle + PDF
│   └── alertas/    # inbox + polling badge
└── shared/         # empty-state, confirm-dialog, chart utils
```

- Lazy loading por feature
- Interceptors: loading, JWT, errores (snackbar)
- Guards: sesión (`authGuard`) y roles (`roleGuard`)
- Polling de alertas no leídas cada 30 s en el layout

## Build y Vercel

```bash
npm run build
```

Salida: `dist/appMission/browser/`

El build copia `index.csr.html` → `index.html` para que las rutas profundas (`/auth/login`, `/paises/CO`, etc.) no den 404 al refrescar. La config está en `vercel.json` (rewrites SPA).

Root Directory en Vercel: carpeta `frontend/appMission` (o la ruta equivalente del monorepo).

## Relación con el backend

Documentación API: [../../backend/README.md](../../backend/README.md)

README general: [../../README.md](../../README.md)
