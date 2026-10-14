import { Routes } from '@angular/router';

import { authGuard } from './core/auth/guards/auth.guard';
import { MainLayout } from './core/layout/main-layout/main-layout';

/**
 * Application root routes with lazy-loaded feature areas.
 */
export const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () =>
      import('./features/auth/auth.routes').then((m) => m.AUTH_ROUTES),
  },
  {
    path: '',
    component: MainLayout,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadChildren: () =>
          import('./features/dashboard/dashboard.routes').then((m) => m.DASHBOARD_ROUTES),
      },
      {
        path: 'paises',
        loadChildren: () =>
          import('./features/paises/paises.routes').then((m) => m.PAISES_ROUTES),
      },
      {
        path: 'portafolios',
        loadChildren: () =>
          import('./features/portafolios/portafolios.routes').then((m) => m.PORTAFOLIOS_ROUTES),
      },
      {
        path: 'alertas',
        loadChildren: () =>
          import('./features/alertas/alertas.routes').then((m) => m.ALERTAS_ROUTES),
      },
    ],
  },
  {
    path: '**',
    loadComponent: () =>
      import('./features/not-found/not-found-page').then((m) => m.NotFoundPage),
  },
];

