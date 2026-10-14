import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

/**
 * Placeholder countries page until section 4 is implemented.
 */
@Component({
  selector: 'app-paises-placeholder',
  imports: [MatCardModule],
  template: `<mat-card><mat-card-title>Paises</mat-card-title><mat-card-subtitle>Proximamente</mat-card-subtitle></mat-card>`,
})
export class PaisesPlaceholder {}
