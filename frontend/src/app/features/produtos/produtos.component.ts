import { CurrencyPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { finalize } from 'rxjs';

import { Produto, ProdutosService, TipoMidia } from './produtos.service';
import { ProdutoFormDialogComponent } from './produto-form-dialog.component';
import { FeedbackService } from '../../core/feedback.service';

@Component({
  selector: 'app-produtos',
  standalone: true,
  imports: [CurrencyPipe, RouterLink, MatButtonModule, MatCardModule, MatDialogModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './produtos.component.html',
  styleUrl: './produtos.component.scss',
})
export class ProdutosComponent implements OnInit {
  private readonly produtosService = inject(ProdutosService);
  private readonly feedback = inject(FeedbackService);
  private readonly dialog = inject(MatDialog);

  protected readonly produtos = signal<Produto[]>([]);
  protected readonly carregando = signal(true);
  protected readonly erro = signal<string | null>(null);
  protected readonly operacoes = signal(new Set<string>());

  ngOnInit(): void {
    this.carregarProdutos();
  }

  protected abrirCriacao(): void {
    this.abrirDialog();
  }

  protected abrirEdicao(produto: Produto): void {
    this.abrirDialog(produto);
  }

  private abrirDialog(produto?: Produto): void {
    const ref = this.dialog.open(ProdutoFormDialogComponent, { width: '720px', data: { produto } });
    ref.afterClosed().subscribe((salvou) => {
      if (salvou) { this.carregarProdutos(); }
    });
  }

  protected carregarProdutos(): void {
    this.carregando.set(true);
    this.erro.set(null);
    this.produtosService
      .listar()
      .pipe(finalize(() => this.carregando.set(false)))
      .subscribe({
        next: ({ items }) => this.produtos.set(items),
        error: () => { const mensagem='Não foi possível carregar os produtos.'; this.erro.set(mensagem); this.feedback.erro(mensagem); },
      });
  }

  protected selecionarArquivo(produto: Produto, tipo: TipoMidia, evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    input.value = '';
    if (!arquivo) return;

    this.executarOperacao(
      produto,
      tipo,
      this.produtosService.enviarMidia(produto.id, tipo, arquivo),
    );
  }

  protected removerMidia(produto: Produto, tipo: TipoMidia): void {
    this.executarOperacao(produto, tipo, this.produtosService.removerMidia(produto.id, tipo));
  }

  protected excluir(produto: Produto): void {
    if (!confirm(`Excluir o produto "${produto.nome}"? Esta ação não pode ser desfeita.`)) return;

    const chave = `${produto.id}-exclusao`;
    this.alterarOperacao(chave, true);
    this.produtosService.excluir(produto.id).pipe(
      finalize(() => this.alterarOperacao(chave, false)),
    ).subscribe({
      next: () => {
        this.produtos.update((itens) => itens.filter((item) => item.id !== produto.id));
        this.feedback.sucesso('Produto excluído com sucesso.');
      },
      error: (erro: HttpErrorResponse) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível excluir o produto.'),
      ),
    });
  }

  protected processando(produtoId: number, tipo: TipoMidia): boolean {
    return this.operacoes().has(`${produtoId}-${tipo}`);
  }

  protected estaExcluindo(produtoId: number): boolean {
    return this.operacoes().has(`${produtoId}-exclusao`);
  }

  private executarOperacao(
    produto: Produto,
    tipo: TipoMidia,
    requisicao: ReturnType<ProdutosService['removerMidia']>,
  ): void {
    const chave = `${produto.id}-${tipo}`;
    this.alterarOperacao(chave, true);
    this.erro.set(null);

    requisicao.pipe(finalize(() => this.alterarOperacao(chave, false))).subscribe({
      next: (atualizado) => {
        this.produtos.update((produtos) =>
          produtos.map((item) => (item.id === atualizado.id ? atualizado : item)),
        );
        this.feedback.sucesso(`${tipo === 'imagem' ? 'Imagem' : 'Vídeo'} atualizado com sucesso.`);
      },
      error: (erro: HttpErrorResponse) => {
        const mensagem=this.feedback.mensagemErro(erro,`Não foi possível atualizar o ${tipo} deste produto.`);
        this.erro.set(mensagem);
        this.feedback.erro(mensagem);
      },
    });
  }

  private alterarOperacao(chave: string, adicionar: boolean): void {
    this.operacoes.update((atuais) => {
      const novas = new Set(atuais);
      adicionar ? novas.add(chave) : novas.delete(chave);
      return novas;
    });
  }
}
