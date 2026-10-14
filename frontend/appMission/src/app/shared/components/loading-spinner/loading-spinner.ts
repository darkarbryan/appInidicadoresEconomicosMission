import { Component, inject } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { LoadingService } from '../../../core/services/loading.service';

/**
 * Global full-screen loading overlay driven by LoadingService.
 */
@Component({
  selector: 'app-loading-spinner',
  imports: [MatProgressSpinnerModule],
  templateUrl: './loading-spinner.html',
  styleUrl: './loading-spinner.scss',
})
export class LoadingSpinner {
  readonly loading = inject(LoadingService);
}
