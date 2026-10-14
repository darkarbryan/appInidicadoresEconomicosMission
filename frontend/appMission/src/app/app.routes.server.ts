import { RenderMode, ServerRoute } from '@angular/ssr';

/**
 * Prefer client rendering for SPA hosting (e.g. Vercel static).
 * Avoids broken prerender for guarded/dynamic routes like /auth/login.
 */
export const serverRoutes: ServerRoute[] = [
  {
    path: '**',
    renderMode: RenderMode.Client
  }
];
