import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/auth/auth.service';

/**
 * Ensure password and confirmation fields match.
 */
function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirm = group.get('password_confirm')?.value;
  if (!password || !confirm || password === confirm) {
    return null;
  }
  return { passwordsMismatch: true };
}

/**
 * Password reset page that consumes uid/token from the recovery email link.
 */
@Component({
  selector: 'app-reset-page',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './reset-page.html',
  styleUrl: './reset-page.scss',
})
export class ResetPage {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  readonly submitting = signal(false);

  readonly uid = this.route.snapshot.queryParamMap.get('uid') ?? '';
  readonly token = this.route.snapshot.queryParamMap.get('token') ?? '';
  readonly linkValid = !!(this.uid && this.token);

  readonly form = this.fb.nonNullable.group(
    {
      password: ['', [Validators.required, Validators.minLength(8)]],
      password_confirm: ['', [Validators.required, Validators.minLength(8)]],
    },
    { validators: passwordsMatch },
  );

  /**
   * Submit the new password using the recovery link payload.
   */
  submit(): void {
    if (!this.linkValid || this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    const { password, password_confirm } = this.form.getRawValue();

    this.auth
      .passwordReset({
        uid: this.uid,
        token: this.token,
        password,
        password_confirm,
      })
      .subscribe({
        next: (data) => {
          this.submitting.set(false);
          this.snackBar.open(data.detail, 'Cerrar', { duration: 4500 });
          void this.router.navigate(['/auth/login']);
        },
        error: () => {
          this.submitting.set(false);
        },
      });
  }
}
