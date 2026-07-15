import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { switchMap } from 'rxjs';
import { Producao, ProducoesService } from './producoes.service';

@Component({
  selector: 'app-producao-detalhe',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, DecimalPipe, RouterLink, MatButtonModule, MatIconModule],
  templateUrl: './producao-detalhe.component.html',
  styleUrl: './producao-detalhe.component.scss',
})
export class ProducaoDetalheComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(ProducoesService);
  protected readonly producao = signal<Producao | null>(null);
  protected readonly erro = signal<string | null>(null);

  ngOnInit(): void {
    this.route.paramMap.pipe(
      switchMap((params) => this.service.obter(Number(params.get('id')))),
    ).subscribe({
      next: (producao) => this.producao.set(producao),
      error: () => this.erro.set('Não foi possível carregar esta produção.'),
    });
  }
}
