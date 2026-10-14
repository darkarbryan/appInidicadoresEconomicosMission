import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

/**
 * Placeholder alerts page until section 6 is implemented.
 */
@Component({
  selector: 'app-alertas-placeholder',
  imports: [MatCardModule],
  template: `<mat-card><mat-card-title>Alertas</mat-card-title><mat-card-subtitle>Proximamente</mat-card-subtitle></mat-card>`,
})
export class AlertasPlaceholder {}
