import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_ENDPOINTS } from '../../../core/constants/api-endpoints';
import { PaginatedData } from '../../../core/models/api-response.model';
import {
  Portfolio,
  PortfolioDetail,
  PortfolioSummary,
  Position,
} from '../../../core/models/domain.model';
import { ApiService } from '../../../core/services/api.service';

export interface PortfolioWritePayload {
  nombre: string;
  descripcion?: string;
  es_publico?: boolean;
  activo?: boolean;
}

export interface PositionWritePayload {
  pais: string;
  tipo_activo: string;
  monto_inversion_usd: number | string;
  fecha_entrada: string;
  fecha_salida?: string | null;
  notas?: string;
}

/**
 * Portfolios feature API access.
 */
@Injectable({ providedIn: 'root' })
export class PortafoliosService {
  private readonly api = inject(ApiService);

  /**
   * List portfolios visible to the current user.
   */
  list(query?: {
    page?: number;
    page_size?: number;
    mios?: number | string;
    publicos?: number | string;
    activo?: boolean | string;
    search?: string;
  }): Observable<PaginatedData<Portfolio>> {
    return this.api.get<PaginatedData<Portfolio>>(API_ENDPOINTS.portfolios.list, {
      page_size: 50,
      ...query,
    });
  }

  /**
   * Create a portfolio owned by the current user.
   */
  create(payload: PortfolioWritePayload): Observable<PortfolioDetail> {
    return this.api.post<PortfolioDetail>(API_ENDPOINTS.portfolios.list, payload);
  }

  /**
   * Load portfolio detail with positions and metrics.
   */
  getDetail(id: number | string): Observable<PortfolioDetail> {
    return this.api.get<PortfolioDetail>(API_ENDPOINTS.portfolios.detail(id));
  }

  /**
   * Update portfolio metadata.
   */
  update(id: number | string, payload: PortfolioWritePayload): Observable<PortfolioDetail> {
    return this.api.put<PortfolioDetail>(API_ENDPOINTS.portfolios.detail(id), payload);
  }

  /**
   * Soft-delete a portfolio.
   */
  remove(id: number | string): Observable<{ detail: string; id: number }> {
    return this.api.delete<{ detail: string; id: number }>(API_ENDPOINTS.portfolios.detail(id));
  }

  /**
   * Add a position to a portfolio.
   */
  addPosition(id: number | string, payload: PositionWritePayload): Observable<Position> {
    return this.api.post<Position>(API_ENDPOINTS.portfolios.positions(id), payload);
  }

  /**
   * Update an existing position.
   */
  updatePosition(
    id: number | string,
    positionId: number | string,
    payload: PositionWritePayload,
  ): Observable<Position> {
    return this.api.put<Position>(
      API_ENDPOINTS.portfolios.positionDetail(id, positionId),
      payload,
    );
  }

  /**
   * Soft-close a position.
   */
  closePosition(
    id: number | string,
    positionId: number | string,
    fechaSalida?: string,
  ): Observable<{ detail: string; posicion: Position }> {
    return this.api.delete<{ detail: string; posicion: Position }>(
      API_ENDPOINTS.portfolios.positionDetail(id, positionId),
      fechaSalida ? { fecha_salida: fechaSalida } : undefined,
    );
  }

  /**
   * Load distribution summary for charts.
   */
  getSummary(id: number | string): Observable<PortfolioSummary> {
    return this.api.get<PortfolioSummary>(API_ENDPOINTS.portfolios.summary(id));
  }

  /**
   * Download the portfolio PDF export as a blob.
   */
  exportPdf(id: number | string): Observable<Blob> {
    return this.api.getBlob(API_ENDPOINTS.portfolios.exportPdf(id));
  }
}
