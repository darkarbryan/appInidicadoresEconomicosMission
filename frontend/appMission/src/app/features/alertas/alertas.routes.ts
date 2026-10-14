import { Routes } from '@angular/router';

/**
 * Lazy-loaded alerts feature routes.
 */
export const ALERTAS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/alertas-placeholder/alertas-placeholder').then(
        (m) => m.AlertasPlaceholder,
      ),
  },
];
