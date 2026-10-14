import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { API_ENDPOINTS } from '../../../core/constants/api-endpoints';
import { PaginatedData } from '../../../core/models/api-response.model';
import { AlertItem, AlertsSummary } from '../../../core/models/domain.model';
import { ApiService } from '../../../core/services/api.service';

/**
 * Alerts feature API access with unread badge state.
 */
@Injectable({ providedIn: 'root' })
export class AlertasService {
  private readonly api = inject(ApiService);

  readonly unreadCount = signal(0);

  /**
   * List alerts for the current user (own + global).
   */
  list(query?: {
    page?: number;
    page_size?: number;
    leida?: boolean | string;
    tipo?: string;
    severidad?: string;
    ordering?: string;
  }): Observable<PaginatedData<AlertItem>> {
    return this.api.get<PaginatedData<AlertItem>>(API_ENDPOINTS.alerts.list, {
      page_size: 50,
      ordering: '-fecha_creacion',
      ...query,
    });
  }

  /**
   * Load alert counters and refresh the unread badge signal.
   */
  getSummary(): Observable<AlertsSummary> {
    return this.api.get<AlertsSummary>(API_ENDPOINTS.alerts.summary).pipe(
      tap((summary) => this.unreadCount.set(summary.no_leidas)),
    );
  }

  /**
   * Mark a single alert as read.
   */
  markRead(id: number | string): Observable<AlertItem> {
    return this.api.put<AlertItem>(API_ENDPOINTS.alerts.markRead(id), {}).pipe(
      tap(() => {
        const current = this.unreadCount();
        if (current > 0) {
          this.unreadCount.set(current - 1);
        }
      }),
    );
  }

  /**
   * Mark all visible alerts as read.
   */
  markAllRead(): Observable<{ detail: string; actualizadas: number }> {
    return this.api
      .put<{ detail: string; actualizadas: number }>(API_ENDPOINTS.alerts.markAllRead, {})
      .pipe(tap(() => this.unreadCount.set(0)));
  }
}
