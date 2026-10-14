import { Routes } from '@angular/router';

/**
 * Lazy-loaded portfolios feature routes.
 */
export const PORTAFOLIOS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/portafolios-list-page/portafolios-list-page').then(
        (m) => m.PortafoliosListPage,
      ),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./pages/portafolio-detail-page/portafolio-detail-page').then(
        (m) => m.PortafolioDetailPage,
      ),
  },
];
