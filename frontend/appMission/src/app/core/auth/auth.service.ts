import { isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { Observable, of, tap } from 'rxjs';

import { API_ENDPOINTS } from '../constants/api-endpoints';
import { AuthPayload, User } from '../models/user.model';
import { ApiService } from '../services/api.service';

const ACCESS_KEY = 'datapulse_access_token';
const REFRESH_KEY = 'datapulse_refresh_token';
const USER_KEY = 'datapulse_user';

/**
 * Handles authentication state, token persistence and auth API calls.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly browser = isPlatformBrowser(this.platformId);

  readonly currentUser = signal<User | null>(this.readStoredUser());

  /**
   * Register a new analyst account and persist the returned session.
   */
  register(payload: {
    email: string;
    password: string;
    password_confirm: string;
    nombre_completo: string;
  }): Observable<AuthPayload> {
    return this.api.post<AuthPayload>(API_ENDPOINTS.auth.register, payload).pipe(
      tap((data) => this.persistSession(data)),
    );
  }

  /**
   * Authenticate with email/password and persist the session.
   */
  login(email: string, password: string): Observable<AuthPayload> {
    return this.api.post<AuthPayload>(API_ENDPOINTS.auth.login, { email, password }).pipe(
      tap((data) => this.persistSession(data)),
    );
  }

  /**
   * Refresh the access token using the stored refresh token.
   */
  refresh(): Observable<{ access: string; refresh?: string }> {
    const refresh = this.getRefreshToken();
    return this.api.post<{ access: string; refresh?: string }>(API_ENDPOINTS.auth.refresh, {
      refresh,
    }).pipe(
      tap((tokens) => {
        if (tokens.access) {
          this.setAccessToken(tokens.access);
        }
        if (tokens.refresh) {
          this.setRefreshToken(tokens.refresh);
        }
      }),
    );
  }

  /**
   * Load the authenticated user profile from the API.
   */
  me(): Observable<User> {
    return this.api.get<User>(API_ENDPOINTS.auth.me).pipe(
      tap((user) => {
        this.currentUser.set(user);
        this.writeStorage(USER_KEY, JSON.stringify(user));
      }),
    );
  }

  /**
   * Invalidate the refresh token on the server and clear local session data.
   */
  logout(): Observable<{ detail: string }> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      this.clearSession();
      return of({ detail: 'Sesión cerrada localmente.' });
    }

    return this.api.post<{ detail: string }>(API_ENDPOINTS.auth.logout, { refresh }).pipe(
      tap(() => this.clearSession()),
    );
  }

  /**
   * Clear local auth state without calling the API.
   */
  clearSession(): void {
    this.removeStorage(ACCESS_KEY);
    this.removeStorage(REFRESH_KEY);
    this.removeStorage(USER_KEY);
    this.currentUser.set(null);
  }

  /**
   * Return whether the browser currently holds an access token.
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Return the current access token, if any.
   */
  getAccessToken(): string | null {
    return this.readStorage(ACCESS_KEY);
  }

  /**
   * Return the current refresh token, if any.
   */
  getRefreshToken(): string | null {
    return this.readStorage(REFRESH_KEY);
  }

  /**
   * Persist tokens and user after a successful auth response.
   */
  private persistSession(payload: AuthPayload): void {
    this.setAccessToken(payload.access);
    this.setRefreshToken(payload.refresh);
    this.currentUser.set(payload.user);
    this.writeStorage(USER_KEY, JSON.stringify(payload.user));
  }

  private setAccessToken(token: string): void {
    this.writeStorage(ACCESS_KEY, token);
  }

  private setRefreshToken(token: string): void {
    this.writeStorage(REFRESH_KEY, token);
  }

  private readStoredUser(): User | null {
    const raw = this.readStorage(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  private readStorage(key: string): string | null {
    if (!this.browser) {
      return null;
    }
    return localStorage.getItem(key);
  }

  private writeStorage(key: string, value: string): void {
    if (!this.browser) {
      return;
    }
    localStorage.setItem(key, value);
  }

  private removeStorage(key: string): void {
    if (!this.browser) {
      return;
    }
    localStorage.removeItem(key);
  }
}
