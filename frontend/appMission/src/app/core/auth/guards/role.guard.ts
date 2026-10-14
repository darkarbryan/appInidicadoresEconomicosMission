import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { UserRole } from '../../models/user.model';
import { AuthService } from '../auth.service';

/**
 * Protect routes that require one of the allowed roles.
 */
export const roleGuard = (allowedRoles: UserRole[]): CanActivateFn => {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);
    const role = auth.currentUser()?.rol;

    if (role && allowedRoles.includes(role)) {
      return true;
    }

    return router.createUrlTree(['/dashboard']);
  };
};
