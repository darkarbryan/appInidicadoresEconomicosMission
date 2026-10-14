import { Injectable, signal } from '@angular/core';

/**
 * Tracks in-flight HTTP requests to drive the global loading overlay.
 */
@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly activeRequests = signal(0);

  readonly isLoading = signal(false);

  /**
   * Increment the pending-request counter and show the overlay.
   */
  show(): void {
    this.activeRequests.update((count) => count + 1);
    this.isLoading.set(true);
  }

  /**
   * Decrement the pending-request counter and hide the overlay when idle.
   */
  hide(): void {
    this.activeRequests.update((count) => Math.max(0, count - 1));
    if (this.activeRequests() === 0) {
      this.isLoading.set(false);
    }
  }

  /**
   * Force-reset the loader state (used after fatal navigation errors).
   */
  reset(): void {
    this.activeRequests.set(0);
    this.isLoading.set(false);
  }
}
