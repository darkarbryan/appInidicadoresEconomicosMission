import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { LoadingSpinner } from './shared/components/loading-spinner/loading-spinner';

/**
 * Root application component hosting the router outlet and global loader.
 */
@Component({
  imports: [RouterOutlet, LoadingSpinner],
  selector: 'app-root',
  styleUrl: './app.scss',
  templateUrl: './app.html',
})
export class App {}
