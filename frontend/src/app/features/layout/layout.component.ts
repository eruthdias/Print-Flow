import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

interface ItemMenu {
  rota: string;
  rotulo: string;
  icone: string;
}

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss',
})
export class LayoutComponent {
  protected readonly itensMenu: ItemMenu[] = [
    { rota: '/dashboard', rotulo: 'Dashboard', icone: 'dashboard' },
    { rota: '/materiais', rotulo: 'Materiais', icone: 'inventory_2' },
    { rota: '/produtos', rotulo: 'Produtos', icone: 'category' },
    { rota: '/producoes', rotulo: 'Produções', icone: 'precision_manufacturing' },
    { rota: '/relatorios', rotulo: 'Relatórios', icone: 'bar_chart' },
  ];

  protected sair(): void {
    localStorage.removeItem('access_token');
    location.reload();
  }
}
