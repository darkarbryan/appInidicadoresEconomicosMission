import { isPlatformBrowser } from '@angular/common';
import {
  Component,
  DestroyRef,
  OnInit,
  PLATFORM_ID,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { interval, startWith, switchMap } from 'rxjs';

import { AlertasService } from '../../../features/alertas/services/alertas.service';
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
    MatBadgeModule,
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss',
})
export class MainLayout implements OnInit {
  readonly auth = inject(AuthService);
  readonly alertas = inject(AlertasService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly platformId = inject(PLATFORM_ID);

  readonly sidenavOpened = signal(true);
  readonly isMobile = signal(false);

  readonly navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { label: 'Países', path: '/paises', icon: 'public' },
    { label: 'Portafolios', path: '/portafolios', icon: 'account_balance_wallet' },
    { label: 'Alertas', path: '/alertas', icon: 'notifications', badge: true },
  ];

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.updateViewport();
    window.addEventListener('resize', this.updateViewport);

    this.destroyRef.onDestroy(() => {
      window.removeEventListener('resize', this.updateViewport);
    });

    interval(60000)
      .pipe(
        startWith(0),
        switchMap(() => this.alertas.getSummary()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe();
  }

  /**
   * Toggle the sidenav on compact viewports.
   */
  toggleSidenav(): void {
    this.sidenavOpened.update((open) => !open);
  }

  /**
   * Close the sidenav after navigation on mobile.
   */
  onNavClick(): void {
    if (this.isMobile()) {
      this.sidenavOpened.set(false);
    }
  }

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

  private readonly updateViewport = (): void => {
    const mobile = window.innerWidth < 900;
    this.isMobile.set(mobile);
    this.sidenavOpened.set(!mobile);
  };
}
