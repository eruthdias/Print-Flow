import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { finalize } from 'rxjs';
import { FeedbackService } from '../../core/feedback.service';
import { Material, MateriaisService } from './materiais.service';

@Component({
  selector: 'app-materiais',
  standalone: true,
  imports: [CurrencyPipe, DecimalPipe, RouterLink, MatButtonModule, MatIconModule],
  templateUrl: './materiais.component.html',
  styleUrl: './materiais.component.scss',
})
export class MateriaisComponent implements OnInit {
  private readonly service = inject(MateriaisService);
  private readonly feedback = inject(FeedbackService);

  protected readonly materiais = signal<Material[]>([]);
  protected readonly excluindo = signal(new Set<number>());

  ngOnInit(): void {
    this.service.listar().subscribe({
      next: ({ items }) => this.materiais.set(items),
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível carregar os materiais.'),
      ),
    });
  }

  protected excluir(material: Material): void {
    if (!confirm(`Excluir o material "${material.nome}"? Esta ação não pode ser desfeita.`)) return;

    this.alterarExclusao(material.id, true);
    this.service.excluir(material.id).pipe(
      finalize(() => this.alterarExclusao(material.id, false)),
    ).subscribe({
      next: () => {
        this.materiais.update((itens) => itens.filter((item) => item.id !== material.id));
        this.feedback.sucesso('Material excluído com sucesso.');
      },
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível excluir o material.'),
      ),
    });
  }

  protected estaExcluindo(materialId: number): boolean {
    return this.excluindo().has(materialId);
  }

  private alterarExclusao(materialId: number, adicionar: boolean): void {
    this.excluindo.update((atuais) => {
      const novos = new Set(atuais);
      adicionar ? novos.add(materialId) : novos.delete(materialId);
      return novos;
    });
  }
}
