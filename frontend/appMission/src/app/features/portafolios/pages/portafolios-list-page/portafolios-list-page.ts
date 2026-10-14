import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/auth/auth.service';
import { Portfolio } from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { PortafoliosService } from '../../services/portafolios.service';

/**
 * Portfolio catalog with create form for analyst/admin users.
 */
@Component({
  selector: 'app-portafolios-list-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatButtonModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './portafolios-list-page.html',
  styleUrl: './portafolios-list-page.scss',
})
export class PortafoliosListPage implements OnInit {
  private readonly portafoliosService = inject(PortafoliosService);
  private readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);
  private readonly snackBar = inject(MatSnackBar);

  readonly loading = signal(true);
  readonly creating = signal(false);
  readonly portfolios = signal<Portfolio[]>([]);
  readonly columns = ['nombre', 'total_posiciones', 'es_publico', 'fecha_modificacion', 'acciones'];

  readonly canWrite = () => {
    const role = this.auth.currentUser()?.rol;
    return role === 'ADMIN' || role === 'ANALISTA';
  };

  readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(100)]],
    descripcion: ['', [Validators.maxLength(500)]],
    es_publico: [false],
  });

  ngOnInit(): void {
    this.load();
  }

  /**
   * Reload portfolios visible to the current user.
   */
  load(): void {
    this.loading.set(true);
    this.portafoliosService.list({ mios: 1, activo: true }).subscribe({
      next: (page) => {
        this.portfolios.set(page.results);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  /**
   * Create a new portfolio owned by the current user.
   */
  create(): void {
    if (!this.canWrite() || this.form.invalid || this.creating()) {
      this.form.markAllAsTouched();
      return;
    }

    this.creating.set(true);
    this.portafoliosService.create(this.form.getRawValue()).subscribe({
      next: () => {
        this.creating.set(false);
        this.form.reset({ nombre: '', descripcion: '', es_publico: false });
        this.snackBar.open('Portafolio creado correctamente.', 'Cerrar', { duration: 3500 });
        this.load();
      },
      error: () => this.creating.set(false),
    });
  }

  /**
   * Soft-delete a portfolio and refresh the list.
   */
  remove(id: number): void {
    if (!this.canWrite()) {
      return;
    }

    this.portafoliosService.remove(id).subscribe({
      next: (data) => {
        this.snackBar.open(data.detail, 'Cerrar', { duration: 3500 });
        this.load();
      },
    });
  }
}
