import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { RouterLink } from '@angular/router';

/**
 * Dedicated 404 page for unknown application routes.
 */
@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink, MatButtonModule],
  template: `
    <section class="not-found">
      <p class="code">404</p>
      <h1>Página no encontrada</h1>
      <p>La ruta solicitada no existe en DataPulse Mission.</p>
      <a mat-flat-button color="primary" routerLink="/dashboard">Ir al dashboard</a>
    </section>
  `,
  styles: `
    .not-found {
      min-height: 60vh;
      display: grid;
      place-content: center;
      justify-items: center;
      gap: 0.5rem;
      text-align: center;
      padding: 2rem;
    }

    .code {
      margin: 0;
      font: var(--mat-sys-display-large);
      font-weight: 700;
      color: var(--mat-sys-primary);
    }

    h1 {
      margin: 0;
      font: var(--mat-sys-headline-medium);
    }

    p {
      margin: 0 0 0.75rem;
      color: color-mix(in srgb, var(--mat-sys-on-surface) 70%, transparent);
    }
  `,
})
export class NotFoundPage {}
