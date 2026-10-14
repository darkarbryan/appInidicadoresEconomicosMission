import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/api-response.model';

type QueryParams = Record<string, string | number | boolean | undefined | null>;

/**
 * Thin HTTP client that prefixes the API base URL and unwraps the envelope.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl.replace(/\/$/, '');

  /**
   * Perform a GET request and return the envelope data payload.
   */
  get<T>(path: string, query?: QueryParams): Observable<T> {
    return this.http
      .get<ApiResponse<T>>(this.url(path), { params: this.toParams(query) })
      .pipe(map((response) => response.data));
  }

  /**
   * Perform a POST request and return the envelope data payload.
   */
  post<T>(path: string, body: unknown = {}): Observable<T> {
    return this.http
      .post<ApiResponse<T>>(this.url(path), body)
      .pipe(map((response) => response.data));
  }

  /**
   * Perform a PUT request and return the envelope data payload.
   */
  put<T>(path: string, body: unknown = {}): Observable<T> {
    return this.http
      .put<ApiResponse<T>>(this.url(path), body)
      .pipe(map((response) => response.data));
  }

  /**
   * Perform a DELETE request and return the envelope data payload.
   */
  delete<T>(path: string, body?: unknown): Observable<T> {
    return this.http
      .delete<ApiResponse<T>>(this.url(path), body !== undefined ? { body } : {})
      .pipe(map((response) => response.data));
  }

  /**
   * Perform a GET that returns a binary blob (e.g. PDF export).
   */
  getBlob(path: string): Observable<Blob> {
    return this.http.get(this.url(path), { responseType: 'blob' });
  }

  /**
   * Build an absolute API URL from a relative path constant.
   */
  private url(path: string): string {
    const normalized = path.startsWith('/') ? path : `/${path}`;
    return `${this.baseUrl}${normalized}`;
  }

  /**
   * Convert a plain object into HttpParams, skipping empty values.
   */
  private toParams(query?: QueryParams): HttpParams | undefined {
    if (!query) {
      return undefined;
    }
    let params = new HttpParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    });
    return params;
  }
}
