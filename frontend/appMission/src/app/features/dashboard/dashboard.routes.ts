import { Routes } from '@angular/router';

/**
 * Lazy-loaded dashboard feature routes.
 */
export const DASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/dashboard-page/dashboard-page').then((m) => m.DashboardPage),
  },
];
