import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { forkJoin, finalize } from 'rxjs';

import { Material, MateriaisService } from '../materiais/materiais.service';
import { Produto, ProdutosService } from '../produtos/produtos.service';
import { DashboardResumo, DashboardService } from './dashboard.service';
import { FeedbackService } from '../../core/feedback.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CurrencyPipe,
    DecimalPipe,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly materiaisService = inject(MateriaisService);
  private readonly produtosService = inject(ProdutosService);
  private readonly feedback = inject(FeedbackService);

  protected readonly resumo = signal<DashboardResumo | null>(null);
  protected readonly materiais = signal<Material[]>([]);
  protected readonly produtos = signal<Produto[]>([]);
  protected readonly carregando = signal(true);
  protected readonly erro = signal<string | null>(null);

  ngOnInit(): void {
    this.carregar();
  }

  protected carregar(): void {
    this.carregando.set(true);
    this.erro.set(null);

    forkJoin({
      resumo: this.dashboardService.obter(),
      materiais: this.materiaisService.listar(),
      produtos: this.produtosService.listar(),
    })
      .pipe(finalize(() => this.carregando.set(false)))
      .subscribe({
        next: ({ resumo, materiais, produtos }) => {
          this.resumo.set(resumo);
          this.materiais.set(materiais.items.slice(0, 5));
          this.produtos.set(produtos.items.slice(0, 4));
        },
        error: (erro: HttpErrorResponse) => {
          const mensagem =
            erro.status === 401
              ? 'Sua sessão expirou. Entre novamente para carregar o dashboard.'
              : 'Não foi possível carregar o dashboard. Confirme se a API está ligada.';
          this.erro.set(mensagem);
          this.feedback.erro(mensagem);
        },
      });
  }
}
