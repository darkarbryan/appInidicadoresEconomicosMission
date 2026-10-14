import { DecimalPipe, isPlatformBrowser } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Chart } from 'chart.js';
import { forkJoin } from 'rxjs';

import { AuthService } from '../../../../core/auth/auth.service';
import { Country, PortfolioDetail, PortfolioSummary } from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { createChart, destroyChart } from '../../../../shared/utils/chart.util';
import { PaisesService } from '../../../paises/services/paises.service';
import { PortafoliosService } from '../../services/portafolios.service';

const PIE_COLORS = ['#0891b2', '#ea580c', '#16a34a', '#7c3aed', '#db2777', '#0f766e', '#ca8a04'];

/**
 * Portfolio detail with positions, Chart.js distribution and PDF export.
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
export class PortafolioDetailPage implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('paisCanvas') paisCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('tipoCanvas') tipoCanvas?: ElementRef<HTMLCanvasElement>;

  private readonly route = inject(ActivatedRoute);
  private readonly portafoliosService = inject(PortafoliosService);
  private readonly paisesService = inject(PaisesService);
  private readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);
  private readonly snackBar = inject(MatSnackBar);
  private readonly platformId = inject(PLATFORM_ID);
  private paisChart: Chart | null = null;
  private tipoChart: Chart | null = null;
  private viewReady = false;

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

  readonly form = this.fb.nonNullable.group({
    pais: ['', Validators.required],
    tipo_activo: ['RENTA_FIJA', Validators.required],
    monto_inversion_usd: [
      1000,
      [Validators.required, Validators.min(1000), Validators.max(10_000_000)],
    ],
    fecha_entrada: [new Date().toISOString().slice(0, 10), Validators.required],
    notas: ['', Validators.maxLength(200)],
  });

  private portfolioId = '';

  ngOnInit(): void {
    this.portfolioId = this.route.snapshot.paramMap.get('id') ?? '';
    this.paisesService.list({ activo: true, page_size: 100 }).subscribe({
      next: (page) => this.countries.set(page.results),
    });
    this.reload();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.scheduleCharts();
  }

  ngOnDestroy(): void {
    destroyChart(this.paisChart);
    destroyChart(this.tipoChart);
  }

  private scheduleCharts(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    // Wait for @if canvases to mount and get a real layout size.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => this.renderCharts());
    });
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
        this.scheduleCharts();
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

    const value = this.form.getRawValue();
    const country = this.countries().find((item) => item.codigo_iso === value.pais);
    if (value.tipo_activo === 'MONEDA' && country?.moneda_codigo === 'USD') {
      this.snackBar.open(
        'No se puede agregar posición MONEDA para un país con moneda USD.',
        'Cerrar',
        { duration: 4000 },
      );
      return;
    }

    const currentTotal = Number(this.portfolio()?.metricas.monto_total_usd ?? 0);
    if (currentTotal + Number(value.monto_inversion_usd) > 50_000_000) {
      this.snackBar.open('El monto total del portafolio no puede superar USD 50,000,000.', 'Cerrar', {
        duration: 4000,
      });
      return;
    }

    this.saving.set(true);
    this.portafoliosService.addPosition(this.portfolioId, value).subscribe({
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

  private renderCharts(): void {
    if (!isPlatformBrowser(this.platformId) || !this.viewReady) {
      return;
    }

    const data = this.summary();
    destroyChart(this.paisChart);
    destroyChart(this.tipoChart);
    this.paisChart = null;
    this.tipoChart = null;

    if (!data) {
      return;
    }

    if (this.paisCanvas && data.distribucion_por_pais.length) {
      this.paisChart = createChart(this.paisCanvas.nativeElement, {
        type: 'pie',
        data: {
          labels: data.distribucion_por_pais.map((item) => item.pais),
          datasets: [
            {
              data: data.distribucion_por_pais.map((item) => Number(item.monto_usd)),
              backgroundColor: PIE_COLORS,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
        },
      });
    }

    if (this.tipoCanvas && data.distribucion_por_tipo_activo.length) {
      this.tipoChart = createChart(this.tipoCanvas.nativeElement, {
        type: 'doughnut',
        data: {
          labels: data.distribucion_por_tipo_activo.map((item) => String(item.tipo_activo)),
          datasets: [
            {
              data: data.distribucion_por_tipo_activo.map((item) => Number(item.monto_usd)),
              backgroundColor: PIE_COLORS,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
        },
      });
    }
  }
}
