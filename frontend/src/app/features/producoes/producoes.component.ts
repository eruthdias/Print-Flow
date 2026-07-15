import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { FeedbackService } from '../../core/feedback.service';
import { Producao, ProducoesService } from './producoes.service';

@Component({
  selector: 'app-producoes',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, DecimalPipe, RouterLink, MatButtonModule, MatIconModule],
  templateUrl: './producoes.component.html',
  styleUrl: './producoes.component.scss',
})
export class ProducoesComponent implements OnInit {
  private readonly service = inject(ProducoesService);
  private readonly feedback = inject(FeedbackService);
  protected readonly producoes = signal<Producao[]>([]);

  ngOnInit(): void {
    this.carregar();
  }

  protected carregar(): void {
    this.service.listar().subscribe({
      next: ({ items }) => this.producoes.set(items),
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível carregar as produções.'),
      ),
    });
  }

  protected estornar(producao: Producao): void {
    if (!confirm(`Estornar a produção de ${producao.produto_nome}?`)) return;

    this.service.estornar(producao.id).subscribe({
      next: () => {
        this.feedback.sucesso('Produção estornada e estoque devolvido.');
        this.carregar();
      },
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível estornar a produção.'),
      ),
    });
  }
}
