import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../auth/auth.service';

/**
 * Authenticated application shell with toolbar and side navigation.
 */
@Component({
  selector: 'app-main-layout',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss',
})
export class MainLayout {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { label: 'Países', path: '/paises', icon: 'public' },
    { label: 'Portafolios', path: '/portafolios', icon: 'account_balance_wallet' },
    { label: 'Alertas', path: '/alertas', icon: 'notifications' },
  ];

  /**
   * Clear the session and redirect to the login page.
   */
  logout(): void {
    const finish = () => {
      this.auth.clearSession();
      void this.router.navigate(['/auth/login']);
    };

    this.auth.logout().subscribe({
      next: finish,
      error: finish,
    });
  }
}
