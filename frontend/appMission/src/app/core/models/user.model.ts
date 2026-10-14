/**
 * Authenticated user profile returned by the backend.
 */
export type UserRole = 'ADMIN' | 'ANALISTA' | 'VIEWER';

export interface User {
  id: number;
  email: string;
  nombre_completo: string;
  rol: UserRole;
  activo: boolean;
  fecha_creacion: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthPayload extends AuthTokens {
  user: User;
}
