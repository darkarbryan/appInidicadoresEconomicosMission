/**
 * Standard Mission API response envelope.
 */
export type ApiMessage = 'OK' | 'WARNING' | 'ERROR';

export interface ApiResponse<T> {
  status: boolean;
  message: ApiMessage;
  data: T;
}

export interface PaginatedData<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page?: number;
  page_size?: number;
  results: T[];
}
