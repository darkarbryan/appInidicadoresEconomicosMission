import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_ENDPOINTS } from '../../../core/constants/api-endpoints';
import {
  DashboardMap,
  DashboardSummary,
  DashboardTrends,
  RiskRankingItem,
} from '../../../core/models/domain.model';
import { PaginatedData } from '../../../core/models/api-response.model';
import { ApiService } from '../../../core/services/api.service';

/**
 * Dashboard and risk ranking API access.
 */
@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly api = inject(ApiService);

  /**
   * Load KPI summary for the authenticated user.
   */
  getSummary(): Observable<DashboardSummary> {
    return this.api.get<DashboardSummary>(API_ENDPOINTS.dashboard.summary);
  }

  /**
   * Load map markers with current risk colors.
   */
  getMap(): Observable<DashboardMap> {
    return this.api.get<DashboardMap>(API_ENDPOINTS.dashboard.map);
  }

  /**
   * Load comparative indicator trends for selected countries.
   */
  getTrends(query?: {
    indicador?: string;
    paises?: string;
    anios?: number;
  }): Observable<DashboardTrends> {
    return this.api.get<DashboardTrends>(API_ENDPOINTS.dashboard.trends, query);
  }

  /**
   * Load the regional risk ranking list.
   */
  getRiskRanking(query?: {
    page?: number;
    page_size?: number;
    nivel_riesgo?: string;
    region?: string;
    ordering?: string;
  }): Observable<PaginatedData<RiskRankingItem>> {
    return this.api.get<PaginatedData<RiskRankingItem>>(API_ENDPOINTS.risk.ranking, {
      page_size: 20,
      ordering: '-indice_compuesto',
      ...query,
    });
  }
}
