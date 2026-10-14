import { DecimalPipe, isPlatformBrowser } from '@angular/common';
import { Component, OnInit, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { AuthService } from '../../../../core/auth/auth.service';
import { Country, PortfolioDetail, PortfolioSummary } from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { PaisesService } from '../../../paises/services/paises.service';
import { PortafoliosService } from '../../services/portafolios.service';

/**
 * Portfolio detail with positions, distribution charts and PDF export.
 */
@Component({
  selector: 'app-portafolio-detail-page',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './portafolio-detail-page.html',
  styleUrl: './portafolio-detail-page.scss',
})
export class PortafolioDetailPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly portafoliosService = inject(PortafoliosService);
  private readonly paisesService = inject(PaisesService);
  private readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);
  private readonly snackBar = inject(MatSnackBar);
  private readonly platformId = inject(PLATFORM_ID);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly portfolio = signal<PortfolioDetail | null>(null);
  readonly summary = signal<PortfolioSummary | null>(null);
  readonly countries = signal<Country[]>([]);

  readonly positionColumns = [
    'pais_nombre',
    'tipo_activo',
    'monto_inversion_usd',
    'fecha_entrada',
    'fecha_salida',
    'acciones',
  ];

  readonly canWrite = () => {
    const role = this.auth.currentUser()?.rol;
    return role === 'ADMIN' || role === 'ANALISTA';
  };

  readonly distributionBars = computed(() => {
    const data = this.summary();
    if (!data) {
      return { paises: [], tipos: [] };
    }
    return {
      paises: data.distribucion_por_pais.map((item) => ({
        label: item.pais,
        porcentaje: Number(item.porcentaje) || 0,
        monto: Number(item.monto_usd) || 0,
      })),
      tipos: data.distribucion_por_tipo_activo.map((item) => ({
        label: String(item.tipo_activo),
        porcentaje: Number(item.porcentaje) || 0,
        monto: Number(item.monto_usd) || 0,
      })),
    };
  });

  readonly form = this.fb.nonNullable.group({
    pais: ['', Validators.required],
    tipo_activo: ['RENTA_FIJA', Validators.required],
    monto_inversion_usd: [1000, [Validators.required, Validators.min(1000)]],
    fecha_entrada: [new Date().toISOString().slice(0, 10), Validators.required],
    notas: [''],
  });

  private portfolioId = '';

  ngOnInit(): void {
    this.portfolioId = this.route.snapshot.paramMap.get('id') ?? '';
    this.paisesService.list({ activo: true, page_size: 100 }).subscribe({
      next: (page) => this.countries.set(page.results),
    });
    this.reload();
  }

  /**
   * Reload portfolio detail and distribution summary.
   */
  reload(): void {
    if (!this.portfolioId) {
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    forkJoin({
      detail: this.portafoliosService.getDetail(this.portfolioId),
      summary: this.portafoliosService.getSummary(this.portfolioId),
    }).subscribe({
      next: ({ detail, summary }) => {
        this.portfolio.set(detail);
        this.summary.set(summary);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  /**
   * Add a position to the current portfolio.
   */
  addPosition(): void {
    if (!this.canWrite() || this.form.invalid || this.saving()) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving.set(true);
    this.portafoliosService.addPosition(this.portfolioId, this.form.getRawValue()).subscribe({
      next: () => {
        this.saving.set(false);
        this.form.patchValue({
          monto_inversion_usd: 1000,
          notas: '',
          fecha_entrada: new Date().toISOString().slice(0, 10),
        });
        this.snackBar.open('Posición agregada.', 'Cerrar', { duration: 3000 });
        this.reload();
      },
      error: () => this.saving.set(false),
    });
  }

  /**
   * Soft-close an open position.
   */
  closePosition(positionId: number): void {
    if (!this.canWrite()) {
      return;
    }

    this.portafoliosService.closePosition(this.portfolioId, positionId).subscribe({
      next: (data) => {
        this.snackBar.open(data.detail, 'Cerrar', { duration: 3000 });
        this.reload();
      },
    });
  }

  /**
   * Download the portfolio PDF export.
   */
  exportPdf(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.portafoliosService.exportPdf(this.portfolioId).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `portafolio_${this.portfolioId}.pdf`;
        anchor.click();
        URL.revokeObjectURL(url);
      },
    });
  }
}
