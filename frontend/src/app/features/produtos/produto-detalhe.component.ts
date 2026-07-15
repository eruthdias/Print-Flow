import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { finalize, switchMap } from 'rxjs';
import { Produto, ProdutosService } from './produtos.service';

@Component({
  selector: 'app-produto-detalhe', standalone: true,
  imports: [CurrencyPipe, DecimalPipe, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './produto-detalhe.component.html', styleUrl: './produto-detalhe.component.scss',
})
export class ProdutoDetalheComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(ProdutosService);
  protected readonly produto = signal<Produto | null>(null);
  protected readonly carregando = signal(true);
  protected readonly erro = signal<string | null>(null);

  ngOnInit(): void {
    this.route.paramMap.pipe(
      switchMap((params) => this.service.obter(Number(params.get('id')))),
      finalize(() => this.carregando.set(false)),
    ).subscribe({ next: (produto) => this.produto.set(produto), error: () => this.erro.set('Não foi possível carregar este produto.') });
  }
}
