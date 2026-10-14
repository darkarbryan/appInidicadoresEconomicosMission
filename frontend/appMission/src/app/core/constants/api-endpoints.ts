/**
 * Central API path catalog.
 * Change paths here when backend routes change; services must not hardcode URLs.
 */
export const API_ENDPOINTS = {
  root: '/api/',
  auth: {
    login: '/api/auth/login/',
    register: '/api/auth/register/',
    refresh: '/api/auth/refresh/',
    me: '/api/auth/me/',
    logout: '/api/auth/logout/',
    passwordRecovery: '/api/auth/password-recovery/',
    passwordReset: '/api/auth/password-reset/',
  },
  countries: {
    list: '/api/paises/',
    detail: (iso: string) => `/api/paises/${iso}/`,
    indicators: (iso: string) => `/api/paises/${iso}/indicadores/`,
    exchangeRates: (iso: string) => `/api/paises/${iso}/tipo-cambio/`,
    syncIndicators: '/api/paises/sync-indicadores/',
    syncFx: '/api/paises/sync-tipos-cambio/',
  },
  risk: {
    ranking: '/api/riesgo/',
    detail: (iso: string) => `/api/riesgo/${iso}/`,
    history: (iso: string) => `/api/riesgo/${iso}/historico/`,
    calculate: '/api/riesgo/calcular/',
  },
  portfolios: {
    list: '/api/portafolios/',
    detail: (id: number | string) => `/api/portafolios/${id}/`,
    positions: (id: number | string) => `/api/portafolios/${id}/posiciones/`,
    positionDetail: (id: number | string, positionId: number | string) =>
      `/api/portafolios/${id}/posiciones/${positionId}/`,
    summary: (id: number | string) => `/api/portafolios/${id}/resumen/`,
    exportPdf: (id: number | string) => `/api/portafolios/${id}/export/pdf/`,
  },
  alerts: {
    list: '/api/alertas/',
    summary: '/api/alertas/resumen/',
    markRead: (id: number | string) => `/api/alertas/${id}/leer/`,
    markAllRead: '/api/alertas/leer-todas/',
  },
  dashboard: {
    summary: '/api/dashboard/resumen/',
    map: '/api/dashboard/mapa/',
    trends: '/api/dashboard/tendencias/',
  },
} as const;
