import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';

import { Country } from '../../../../core/models/domain.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';
import { PaisesService } from '../../services/paises.service';

/**
 * Paginated countries catalog with search and region filters.
 */
@Component({
  selector: 'app-paises-list-page',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './paises-list-page.html',
  styleUrl: './paises-list-page.scss',
})
export class PaisesListPage implements OnInit {
  private readonly paisesService = inject(PaisesService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly countries = signal<Country[]>([]);
  readonly total = signal(0);
  readonly columns = ['nombre', 'codigo_iso', 'region', 'moneda_codigo', 'poblacion'];

  readonly filters = this.fb.nonNullable.group({
    search: [''],
    region: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  /**
   * Reload the countries list using current filters.
   */
  load(): void {
    this.loading.set(true);
    const { search, region } = this.filters.getRawValue();

    this.paisesService
      .list({
        search: search || undefined,
        region: region || undefined,
        activo: true,
      })
      .subscribe({
        next: (page) => {
          this.countries.set(page.results);
          this.total.set(page.count);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
