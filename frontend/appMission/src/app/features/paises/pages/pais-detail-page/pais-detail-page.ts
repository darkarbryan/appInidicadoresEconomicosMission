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
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Chart } from 'chart.js';
import { forkJoin } from 'rxjs';

import { API_ENDPOINTS } from '../../../../core/constants/api-endpoints';
import {
  CountryDetail,
  EconomicIndicator,
  ExchangeRate,
} from '../../../../core/models/domain.model';
import { ApiService } from '../../../../core/services/api.service';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { createChart, destroyChart } from '../../../../shared/utils/chart.util';
import { PaisesService } from '../../services/paises.service';

/**
 * Country detail with flag, indicator cards, Chart.js history and IRPC table.
 */
@Component({
  selector: 'app-pais-detail-page',
  imports: [DecimalPipe, RouterLink, MatCardModule, MatButtonModule, MatTableModule, EmptyState],
  templateUrl: './pais-detail-page.html',
  styleUrl: './pais-detail-page.scss',
})
export class PaisDetailPage implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('indicatorsCanvas') indicatorsCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('fxCanvas') fxCanvas?: ElementRef<HTMLCanvasElement>;

  private readonly route = inject(ActivatedRoute);
  private readonly paisesService = inject(PaisesService);
  private readonly api = inject(ApiService);
  private readonly platformId = inject(PLATFORM_ID);
  private indicatorsChart: Chart | null = null;
  private fxChart: Chart | null = null;
  private viewReady = false;
  private allIndicators: EconomicIndicator[] = [];

  readonly loading = signal(true);
  readonly country = signal<CountryDetail | null>(null);
  readonly rates = signal<ExchangeRate[]>([]);
  readonly riskHistory = signal<
    Array<{
      fecha_calculo: string;
      indice_compuesto: string | number;
      nivel_riesgo: string;
      score_economico: string | number;
      score_cambiario: string | number;
      score_estabilidad: string | number;
    }>
  >([]);

  readonly riskColumns = [
    'fecha_calculo',
    'indice_compuesto',
    'nivel_riesgo',
    'score_economico',
    'score_cambiario',
    'score_estabilidad',
  ];

  ngOnInit(): void {
    const iso = this.route.snapshot.paramMap.get('iso') ?? '';
    if (!iso) {
      this.loading.set(false);
      return;
    }

    const fechaHasta = new Date();
    const fechaDesde = new Date();
    fechaDesde.setDate(fechaHasta.getDate() - 30);

    forkJoin({
      detail: this.paisesService.getDetail(iso),
      indicators: this.paisesService.getIndicators(iso, { page_size: 100 }),
      rates: this.paisesService.getExchangeRates(iso, {
        page_size: 60,
        fecha_desde: fechaDesde.toISOString().slice(0, 10),
        fecha_hasta: fechaHasta.toISOString().slice(0, 10),
      }),
      risk: this.api.get<{
        historico: Array<{
          fecha_calculo: string;
          indice_compuesto: string | number;
          nivel_riesgo: string;
          score_economico: string | number;
          score_cambiario: string | number;
          score_estabilidad: string | number;
        }>;
      }>(API_ENDPOINTS.risk.detail(iso)),
    }).subscribe({
      next: ({ detail, indicators, rates, risk }) => {
        this.country.set(detail);
        this.allIndicators = indicators.results;
        this.rates.set(
          [...rates.results].sort((a, b) => String(a.fecha).localeCompare(String(b.fecha))),
        );
        this.riskHistory.set(risk.historico ?? []);
        this.loading.set(false);
        this.scheduleCharts();
      },
      error: () => this.loading.set(false),
    });
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.scheduleCharts();
  }

  ngOnDestroy(): void {
    destroyChart(this.indicatorsChart);
    destroyChart(this.fxChart);
  }

  private scheduleCharts(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    requestAnimationFrame(() => {
      requestAnimationFrame(() => this.renderCharts());
    });
  }

  private renderCharts(): void {
    if (!isPlatformBrowser(this.platformId) || !this.viewReady) {
      return;
    }
    this.renderIndicatorsChart();
    this.renderFxChart();
  }

  private renderIndicatorsChart(): void {
    if (!this.indicatorsCanvas) {
      return;
    }
    destroyChart(this.indicatorsChart);
    this.indicatorsChart = null;

    const byType = new Map<string, EconomicIndicator[]>();
    for (const row of this.allIndicators) {
      const list = byType.get(row.tipo) ?? [];
      list.push(row);
      byType.set(row.tipo, list);
    }

    const years = Array.from(new Set(this.allIndicators.map((row) => row.anio))).sort(
      (a, b) => a - b,
    );
    if (!years.length) {
      return;
    }

    const colors = ['#0891b2', '#ea580c', '#16a34a', '#7c3aed', '#db2777', '#0f766e'];
    const datasets = Array.from(byType.entries())
      .slice(0, 6)
      .map(([tipo, rows], index) => {
        const byYear = new Map(rows.map((row) => [row.anio, Number(row.valor)]));
        return {
          label: tipo,
          data: years.map((year) => byYear.get(year) ?? null),
          borderColor: colors[index % colors.length],
          tension: 0.2,
          spanGaps: true,
        };
      });

    this.indicatorsChart = createChart(this.indicatorsCanvas.nativeElement, {
      type: 'line',
      data: { labels: years.map(String), datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
      },
    });
  }

  private renderFxChart(): void {
    if (!this.fxCanvas) {
      return;
    }
    destroyChart(this.fxChart);
    this.fxChart = null;

    const rows = this.rates();
    if (!rows.length) {
      return;
    }

    this.fxChart = createChart(this.fxCanvas.nativeElement, {
      type: 'line',
      data: {
        labels: rows.map((row) => row.fecha),
        datasets: [
          {
            label: 'Tasa vs USD',
            data: rows.map((row) => Number(row.tasa)),
            borderColor: '#0891b2',
            backgroundColor: 'rgba(8, 145, 178, 0.15)',
            fill: true,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    });
  }
}
