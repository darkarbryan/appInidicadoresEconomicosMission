import { DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import {
  CountryDetail,
  EconomicIndicator,
  ExchangeRate,
} from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { PaisesService } from '../../services/paises.service';

/**
 * Country detail with risk, indicators and FX history.
 */
@Component({
  selector: 'app-pais-detail-page',
  imports: [DecimalPipe, RouterLink, MatCardModule, MatButtonModule, MatTableModule, EmptyState],
  templateUrl: './pais-detail-page.html',
  styleUrl: './pais-detail-page.scss',
})
export class PaisDetailPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly paisesService = inject(PaisesService);

  readonly loading = signal(true);
  readonly country = signal<CountryDetail | null>(null);
  readonly indicators = signal<EconomicIndicator[]>([]);
  readonly rates = signal<ExchangeRate[]>([]);

  readonly indicatorColumns = ['tipo', 'anio', 'valor', 'unidad', 'fuente'];
  readonly rateColumns = ['fecha', 'tasa', 'variacion_porcentual', 'fuente'];

  ngOnInit(): void {
    const iso = this.route.snapshot.paramMap.get('iso') ?? '';
    if (!iso) {
      this.loading.set(false);
      return;
    }

    forkJoin({
      detail: this.paisesService.getDetail(iso),
      indicators: this.paisesService.getIndicators(iso),
      rates: this.paisesService.getExchangeRates(iso),
    }).subscribe({
      next: ({ detail, indicators, rates }) => {
        this.country.set(detail);
        this.indicators.set(indicators.results);
        this.rates.set(rates.results);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
