import { Routes } from '@angular/router';

import { guestGuard } from '../../core/auth/guards/guest.guard';

/**
 * Lazy-loaded authentication feature routes.
 */
export const AUTH_ROUTES: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./pages/login-page/login-page').then((m) => m.LoginPage),
  },
  {
    path: 'register',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./pages/register-page/register-page').then((m) => m.RegisterPage),
  },
  {
    path: 'recovery',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./pages/recovery-page/recovery-page').then((m) => m.RecoveryPage),
  },
  {
    path: 'reset',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./pages/reset-page/reset-page').then((m) => m.ResetPage),
  },
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'login',
  },
];
