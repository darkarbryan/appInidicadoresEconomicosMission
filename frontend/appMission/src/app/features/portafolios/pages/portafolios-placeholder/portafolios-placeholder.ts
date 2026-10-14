import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

/**
 * Placeholder portfolios page until section 5 is implemented.
 */
@Component({
  selector: 'app-portafolios-placeholder',
  imports: [MatCardModule],
  template: `<mat-card><mat-card-title>Portafolios</mat-card-title><mat-card-subtitle>Proximamente</mat-card-subtitle></mat-card>`,
})
export class PortafoliosPlaceholder {}
