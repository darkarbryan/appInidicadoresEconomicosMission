import { Routes } from '@angular/router';

/**
 * Lazy-loaded countries feature routes.
 */
export const PAISES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/paises-list-page/paises-list-page').then((m) => m.PaisesListPage),
  },
  {
    path: ':iso',
    loadComponent: () =>
      import('./pages/pais-detail-page/pais-detail-page').then((m) => m.PaisDetailPage),
  },
];
