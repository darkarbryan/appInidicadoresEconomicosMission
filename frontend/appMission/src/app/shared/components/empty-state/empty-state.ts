import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

/**
 * Lightweight empty-state block for lists and feature panels.
 */
@Component({
  selector: 'app-empty-state',
  imports: [MatIconModule],
  templateUrl: './empty-state.html',
  styleUrl: './empty-state.scss',
})
export class EmptyState {
  readonly icon = input('inbox');
  readonly title = input('Sin datos');
  readonly message = input('No hay información para mostrar todavía.');
}
