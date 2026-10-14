import { Routes } from '@angular/router';

/**
 * Lazy-loaded countries feature routes.
 */
export const PAISES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/paises-placeholder/paises-placeholder').then((m) => m.PaisesPlaceholder),
  },
];
