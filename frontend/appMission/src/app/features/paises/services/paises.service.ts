import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_ENDPOINTS } from '../../../core/constants/api-endpoints';
import { PaginatedData } from '../../../core/models/api-response.model';
import {
  Country,
  CountryDetail,
  EconomicIndicator,
  ExchangeRate,
} from '../../../core/models/domain.model';
import { ApiService } from '../../../core/services/api.service';

/**
 * Countries feature API access.
 */
@Injectable({ providedIn: 'root' })
export class PaisesService {
  private readonly api = inject(ApiService);

  /**
   * List countries with optional filters and pagination.
   */
  list(query?: {
    page?: number;
    page_size?: number;
    region?: string;
    activo?: boolean | string;
    search?: string;
    ordering?: string;
  }): Observable<PaginatedData<Country>> {
    return this.api.get<PaginatedData<Country>>(API_ENDPOINTS.countries.list, {
      page_size: 50,
      ordering: 'nombre',
      ...query,
    });
  }

  /**
   * Load a country detail payload including recent indicators and risk.
   */
  getDetail(iso: string): Observable<CountryDetail> {
    return this.api.get<CountryDetail>(API_ENDPOINTS.countries.detail(iso));
  }

  /**
   * List economic indicators for a country.
   */
  getIndicators(
    iso: string,
    query?: { tipo?: string; anio?: number; page?: number; page_size?: number },
  ): Observable<PaginatedData<EconomicIndicator>> {
    return this.api.get<PaginatedData<EconomicIndicator>>(
      API_ENDPOINTS.countries.indicators(iso),
      { page_size: 50, ...query },
    );
  }

  /**
   * List FX rates for a country.
   */
  getExchangeRates(
    iso: string,
    query?: { fecha_desde?: string; fecha_hasta?: string; page?: number; page_size?: number },
  ): Observable<PaginatedData<ExchangeRate>> {
    return this.api.get<PaginatedData<ExchangeRate>>(
      API_ENDPOINTS.countries.exchangeRates(iso),
      { page_size: 30, ...query },
    );
  }

  /**
   * ADMIN: synchronize World Bank indicators and chain IRPC recalculation.
   */
  syncIndicators(years = 5): Observable<unknown> {
    return this.api.post(API_ENDPOINTS.countries.syncIndicators, { years });
  }

  /**
   * ADMIN: synchronize FX rates from ExchangeRate-API.
   */
  syncExchangeRates(): Observable<unknown> {
    return this.api.post(API_ENDPOINTS.countries.syncFx, {});
  }

  /**
   * ADMIN: recalculate IRPC for all active countries.
   */
  recalculateRisk(): Observable<unknown> {
    return this.api.post(API_ENDPOINTS.risk.calculate, {});
  }
}
