import { DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import {
  DashboardMap,
  DashboardSummary,
  DashboardTrends,
  RiskRankingItem,
} from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { DashboardService } from '../../services/dashboard.service';

/**
 * Authenticated dashboard with KPIs, map, ranking and trends.
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
export class DashboardPage implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly summary = signal<DashboardSummary | null>(null);
  readonly mapData = signal<DashboardMap | null>(null);
  readonly ranking = signal<RiskRankingItem[]>([]);
  readonly trends = signal<DashboardTrends | null>(null);

  readonly rankingColumns = ['nombre', 'indice_compuesto', 'nivel_riesgo', 'region'];

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
        x: ((lon + 120) / 90) * 100,
        y: ((35 - lat) / 70) * 100,
      };
    });
  });

  readonly trendBars = computed(() => {
    const data = this.trends();
    if (!data?.series?.length) {
      return [];
    }

    const values = data.series.flatMap((serie) =>
      serie.puntos.map((punto) => Math.abs(Number(punto.valor) || 0)),
    );
    const max = Math.max(...values, 1);

    return data.series.map((serie) => ({
      ...serie,
      bars: serie.puntos.map((punto) => {
        const valor = Number(punto.valor) || 0;
        return {
          anio: punto.anio,
          valor,
          height: Math.max(4, (Math.abs(valor) / max) * 100),
        };
      }),
    }));
  });

  ngOnInit(): void {
    this.loadAll();
  }

  /**
   * Reload trends using the selected filters.
   */
  applyTrendFilters(): void {
    const { indicador, paises, anios } = this.filters.getRawValue();
    this.dashboard.getTrends({ indicador, paises, anios }).subscribe({
      next: (trends) => this.trends.set(trends),
    });
  }

  private loadAll(): void {
    this.loading.set(true);
    const { indicador, paises, anios } = this.filters.getRawValue();

    forkJoin({
      summary: this.dashboard.getSummary(),
      map: this.dashboard.getMap(),
      ranking: this.dashboard.getRiskRanking(),
      trends: this.dashboard.getTrends({ indicador, paises, anios }),
    }).subscribe({
      next: ({ summary, map, ranking, trends }) => {
        this.summary.set(summary);
        this.mapData.set(map);
        this.ranking.set(ranking.results);
        this.trends.set(trends);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
