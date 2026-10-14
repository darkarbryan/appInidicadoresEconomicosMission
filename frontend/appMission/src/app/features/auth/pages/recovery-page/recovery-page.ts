import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/auth/auth.service';

/**
 * Password recovery request page.
 */
@Component({
  selector: 'app-recovery-page',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './recovery-page.html',
  styleUrl: './recovery-page.scss',
})
export class RecoveryPage {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly snackBar = inject(MatSnackBar);

  readonly submitting = signal(false);
  readonly sent = signal(false);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  /**
   * Request recovery instructions for the provided email.
   */
  submit(): void {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    const { email } = this.form.getRawValue();

    this.auth.passwordRecovery(email).subscribe({
      next: (data) => {
        this.submitting.set(false);
        this.sent.set(true);
        this.snackBar.open(data.detail, 'Cerrar', { duration: 5000 });
      },
      error: () => {
        this.submitting.set(false);
      },
    });
  }
}
