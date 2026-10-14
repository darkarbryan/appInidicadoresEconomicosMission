import { DecimalPipe, isPlatformBrowser } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';
import { Chart } from 'chart.js';
import { forkJoin } from 'rxjs';

import { AuthService } from '../../../../core/auth/auth.service';
import {
  DashboardMap,
  DashboardSummary,
  DashboardTrends,
  RiskRankingItem,
} from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { createChart, destroyChart } from '../../../../shared/utils/chart.util';
import { PaisesService } from '../../../paises/services/paises.service';
import { DashboardService } from '../../services/dashboard.service';

const TREND_COLORS = ['#0891b2', '#ea580c', '#16a34a'];

/**
 * Authenticated dashboard with KPIs, map, ranking and Chart.js trends.
 */
@Component({
  selector: 'app-dashboard-page',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss',
})
export class DashboardPage implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('trendsCanvas') trendsCanvas?: ElementRef<HTMLCanvasElement>;

  private readonly dashboard = inject(DashboardService);
  private readonly paisesService = inject(PaisesService);
  private readonly auth = inject(AuthService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly fb = inject(FormBuilder);
  private readonly platformId = inject(PLATFORM_ID);
  private trendsChart: Chart | null = null;
  private viewReady = false;

  readonly loading = signal(true);
  readonly syncing = signal(false);
  readonly summary = signal<DashboardSummary | null>(null);
  readonly mapData = signal<DashboardMap | null>(null);
  readonly ranking = signal<RiskRankingItem[]>([]);
  readonly trends = signal<DashboardTrends | null>(null);

  readonly isAdmin = () => this.auth.currentUser()?.rol === 'ADMIN';
  readonly rankingColumns = ['nombre', 'indice_compuesto', 'nivel_riesgo', 'variacion', 'tendencia'];

  readonly filters = this.fb.nonNullable.group({
    indicador: ['PIB'],
    paises: ['CO,BR,MX'],
    anios: [5],
  });

  readonly mapPoints = computed(() => {
    const paises = this.mapData()?.paises ?? [];
    return paises.map((pais) => {
      const lat = Number(pais.latitud);
      const lon = Number(pais.longitud);
      return {
        ...pais,
        x: Math.min(95, Math.max(5, ((lon + 120) / 90) * 100)),
        y: Math.min(95, Math.max(5, ((35 - lat) / 70) * 100)),
      };
    });
  });

  ngOnInit(): void {
    this.loadAll();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.scheduleTrendsChart();
  }

  ngOnDestroy(): void {
    destroyChart(this.trendsChart);
  }

  /**
   * Reload trends using the selected filters.
   */
  applyTrendFilters(): void {
    const { indicador, paises, anios } = this.filters.getRawValue();
    this.dashboard.getTrends({ indicador, paises, anios }).subscribe({
      next: (trends) => {
        this.trends.set(trends);
        this.scheduleTrendsChart();
      },
    });
  }

  /**
   * ADMIN: run World Bank sync + IRPC recalculation.
   */
  runSyncIndicators(): void {
    if (!this.isAdmin() || this.syncing()) {
      return;
    }
    this.syncing.set(true);
    this.paisesService.syncIndicators(5).subscribe({
      next: () => {
        this.syncing.set(false);
        this.snackBar.open('Sincronización de indicadores + IRPC completada.', 'Cerrar', {
          duration: 4000,
        });
        this.loadAll();
      },
      error: () => this.syncing.set(false),
    });
  }

  /**
   * ADMIN: sync FX rates.
   */
  runSyncFx(): void {
    if (!this.isAdmin() || this.syncing()) {
      return;
    }
    this.syncing.set(true);
    this.paisesService.syncExchangeRates().subscribe({
      next: () => {
        this.syncing.set(false);
        this.snackBar.open('Tipos de cambio sincronizados.', 'Cerrar', { duration: 3500 });
      },
      error: () => this.syncing.set(false),
    });
  }

  private loadAll(): void {
    this.loading.set(true);
    const { indicador, paises, anios } = this.filters.getRawValue();

    forkJoin({
      summary: this.dashboard.getSummary(),
      map: this.dashboard.getMap(),
      ranking: this.dashboard.getRiskRanking({ page_size: 10 }),
      trends: this.dashboard.getTrends({ indicador, paises, anios }),
    }).subscribe({
      next: ({ summary, map, ranking, trends }) => {
        this.summary.set(summary);
        this.mapData.set(map);
        this.ranking.set(ranking.results.slice(0, 10));
        this.trends.set(trends);
        this.loading.set(false);
        this.scheduleTrendsChart();
      },
      error: () => this.loading.set(false),
    });
  }

  private scheduleTrendsChart(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    // Double rAF waits for layout/paint so Chart.js gets real canvas size on Vercel.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => this.renderTrendsChart());
    });
  }

  private renderTrendsChart(): void {
    if (!isPlatformBrowser(this.platformId) || !this.viewReady || !this.trendsCanvas) {
      return;
    }

    const data = this.trends();
    destroyChart(this.trendsChart);
    this.trendsChart = null;

    if (!data?.series?.length) {
      return;
    }

    const years = Array.from(
      new Set(data.series.flatMap((serie) => serie.puntos.map((punto) => punto.anio))),
    ).sort((a, b) => a - b);

    this.trendsChart = createChart(this.trendsCanvas.nativeElement, {
      type: 'line',
      data: {
        labels: years.map(String),
        datasets: data.series.map((serie, index) => {
          const byYear = new Map(serie.puntos.map((punto) => [punto.anio, Number(punto.valor)]));
          return {
            label: `${serie.nombre} (${serie.codigo_iso})`,
            data: years.map((year) => byYear.get(year) ?? null),
            borderColor: TREND_COLORS[index % TREND_COLORS.length],
            backgroundColor: TREND_COLORS[index % TREND_COLORS.length],
            tension: 0.25,
            spanGaps: true,
          };
        }),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: false } },
      },
    });
  }
}
