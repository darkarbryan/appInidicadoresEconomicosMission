import { Routes } from '@angular/router';

/**
 * Lazy-loaded portfolios feature routes.
 */
export const PORTAFOLIOS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/portafolios-placeholder/portafolios-placeholder').then(
        (m) => m.PortafoliosPlaceholder,
      ),
  },
];
