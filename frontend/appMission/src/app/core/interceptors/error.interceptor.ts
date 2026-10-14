import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../auth/auth.service';

/**
 * Extract a Spanish user-facing message from a Mission API error payload.
 */
function extractErrorMessage(error: HttpErrorResponse): string {
  const payload = error.error;

  if (typeof payload === 'string' && payload.trim()) {
    return payload;
  }

  if (payload?.data) {
    const data = payload.data;
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail.length) {
      return String(data.detail[0]);
    }
    if (typeof data === 'object') {
      const firstKey = Object.keys(data)[0];
      const value = data[firstKey];
      if (Array.isArray(value) && value.length) {
        return String(value[0]);
      }
      if (typeof value === 'string') {
        return value;
      }
    }
  }

  if (typeof payload?.detail === 'string') {
    return payload.detail;
  }

  if (error.status === 0) {
    return 'No hay conexión con el servidor. Verifica tu red o CORS.';
  }

  return 'Ocurrió un error inesperado. Intenta nuevamente.';
}

/**
 * Display API errors via snackbar and redirect to login on unauthorized responses.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      const message = extractErrorMessage(error);

      if (error.status === 401) {
        auth.clearSession();
        void router.navigate(['/auth/login']);
        snackBar.open('Tu sesión expiró. Inicia sesión nuevamente.', 'Cerrar', {
          duration: 4500,
        });
      } else {
        snackBar.open(message, 'Cerrar', { duration: 5000 });
      }

      return throwError(() => error);
    }),
  );
};
