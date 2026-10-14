import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { RouterLink } from '@angular/router';

import { AlertItem, AlertsSummary } from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { AlertasService } from '../../services/alertas.service';

/**
 * Alerts inbox with filters and mark-as-read actions.
 */
@Component({
  selector: 'app-alertas-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatSelectModule,
    EmptyState,
  ],
  templateUrl: './alertas-page.html',
  styleUrl: './alertas-page.scss',
})
export class AlertasPage implements OnInit {
  private readonly alertasService = inject(AlertasService);
  private readonly fb = inject(FormBuilder);
  private readonly snackBar = inject(MatSnackBar);

  readonly loading = signal(true);
  readonly alerts = signal<AlertItem[]>([]);
  readonly summary = signal<AlertsSummary | null>(null);

  readonly filters = this.fb.nonNullable.group({
    leida: [''],
    tipo: [''],
    severidad: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  /**
   * Reload alerts list and summary counters.
   */
  load(): void {
    this.loading.set(true);
    const { leida, tipo, severidad } = this.filters.getRawValue();

    this.alertasService.getSummary().subscribe({
      next: (summary) => this.summary.set(summary),
    });

    this.alertasService
      .list({
        leida: leida === '' ? undefined : leida,
        tipo: tipo || undefined,
        severidad: severidad || undefined,
      })
      .subscribe({
        next: (page) => {
          this.alerts.set(page.results);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  /**
   * Mark one alert as read and refresh counters.
   */
  markRead(alert: AlertItem): void {
    if (alert.leida) {
      return;
    }

    this.alertasService.markRead(alert.id).subscribe({
      next: () => {
        this.snackBar.open('Alerta marcada como leída.', 'Cerrar', { duration: 2500 });
        this.load();
      },
    });
  }

  /**
   * Mark all alerts as read.
   */
  markAllRead(): void {
    this.alertasService.markAllRead().subscribe({
      next: (data) => {
        this.snackBar.open(data.detail, 'Cerrar', { duration: 3000 });
        this.load();
      },
    });
  }
}
