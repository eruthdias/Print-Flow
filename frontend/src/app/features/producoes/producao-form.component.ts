import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormArray, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { FeedbackService } from '../../core/feedback.service';
import { ComposicaoProduto, Produto, ProdutosService } from '../produtos/produtos.service';
import { ProducoesService } from './producoes.service';

type PerdaForm = FormGroup<{
  material_id: FormControl<number>;
  quantidade_perdida: FormControl<number>;
  motivo: FormControl<string>;
}>;

@Component({
  selector: 'app-producao-form',
  standalone: true,
  imports: [CurrencyPipe, DecimalPipe, ReactiveFormsModule, RouterLink, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule],
  templateUrl: './producao-form.component.html',
  styleUrl: './producao-form.component.scss',
})
export class ProducaoFormComponent implements OnInit {
  private readonly produtosService = inject(ProdutosService);
  private readonly service = inject(ProducoesService);
  private readonly feedback = inject(FeedbackService);
  private readonly router = inject(Router);

  protected readonly produtos = signal<Produto[]>([]);
  protected readonly enviando = signal(false);
  protected readonly form = new FormGroup({
    produto_id: new FormControl<number | null>(null, Validators.required),
    quantidade_produzida: new FormControl(1, { nonNullable: true, validators: [Validators.required, Validators.min(.001)] }),
    data_producao: new FormControl('', { nonNullable: true }),
    desperdicios: new FormArray<PerdaForm>([]),
  });

  ngOnInit(): void {
    this.produtosService.listar().subscribe({
      next: ({ items }) => this.produtos.set(items.filter((produto) => produto.ativo)),
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível carregar os produtos.'),
      ),
    });
    this.form.controls.produto_id.valueChanges.subscribe(() => this.montarDesperdicios());
  }

  protected material(perda: PerdaForm): ComposicaoProduto | undefined {
    return this.produtoSelecionado()?.composicao.find(
      (item) => item.material_id === perda.controls.material_id.value,
    );
  }

  protected consumoNormal(perda: PerdaForm): number {
    return Number(this.material(perda)?.quantidade_utilizada ?? 0) * this.quantidadeProduzida();
  }

  protected custoPerda(perda: PerdaForm): number {
    return Number(this.material(perda)?.custo_unitario_base ?? 0) * Number(perda.controls.quantidade_perdida.value || 0);
  }

  protected custoMateriais(): number {
    return Number(this.produtoSelecionado()?.custo_producao ?? 0) * this.quantidadeProduzida();
  }

  protected custoDesperdicios(): number {
    return this.form.controls.desperdicios.controls.reduce(
      (total, perda) => total + this.custoPerda(perda),
      0,
    );
  }

  protected custoReal(): number {
    return this.custoMateriais() + this.custoDesperdicios();
  }

  protected valorTotal(): number {
    return Number(this.produtoSelecionado()?.preco_venda ?? 0) * this.quantidadeProduzida();
  }

  protected lucroReal(): number {
    return this.valorTotal() - this.custoReal();
  }

  protected salvar(): void {
    const controlesComMotivoAusente = this.form.controls.desperdicios.controls.filter(
      (perda) => perda.controls.quantidade_perdida.value > 0 && !perda.controls.motivo.value.trim(),
    );
    controlesComMotivoAusente.forEach((perda) => {
      perda.controls.motivo.setErrors({ required: true });
      perda.controls.motivo.markAsTouched();
    });

    if (this.form.invalid || controlesComMotivoAusente.length) {
      this.form.markAllAsTouched();
      this.feedback.erro(
        controlesComMotivoAusente.length
          ? 'Informe o motivo de cada desperdício.'
          : 'Selecione um produto e informe uma quantidade válida.',
      );
      return;
    }

    const dados = this.form.getRawValue();
    const desperdicios = dados.desperdicios
      .filter((item) => item.quantidade_perdida > 0)
      .map((item) => ({ ...item, motivo: item.motivo.trim() }));

    this.enviando.set(true);
    this.service.criar({
      produto_id: Number(dados.produto_id),
      quantidade_produzida: dados.quantidade_produzida,
      ...(dados.data_producao ? { data_producao: dados.data_producao } : {}),
      desperdicios,
    }).pipe(finalize(() => this.enviando.set(false))).subscribe({
      next: () => {
        this.feedback.sucesso('Produção registrada e estoque atualizado com sucesso.');
        this.router.navigate(['/producoes']);
      },
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível registrar a produção.'),
      ),
    });
  }

  private produtoSelecionado(): Produto | undefined {
    return this.produtos().find((produto) => produto.id === this.form.controls.produto_id.value);
  }

  private quantidadeProduzida(): number {
    return Math.max(0, Number(this.form.controls.quantidade_produzida.value || 0));
  }

  private montarDesperdicios(): void {
    const desperdicios = this.form.controls.desperdicios;
    desperdicios.clear();
    for (const material of this.produtoSelecionado()?.composicao ?? []) {
      desperdicios.push(this.criarPerda(material));
    }
  }

  private criarPerda(material: ComposicaoProduto): PerdaForm {
    const perda = new FormGroup({
      material_id: new FormControl(material.material_id, { nonNullable: true }),
      quantidade_perdida: new FormControl(0, { nonNullable: true, validators: Validators.min(0) }),
      motivo: new FormControl('', { nonNullable: true, validators: Validators.maxLength(255) }),
    });
    perda.controls.quantidade_perdida.valueChanges.subscribe((quantidade) => {
      perda.controls.motivo.setValidators(
        quantidade > 0
          ? [Validators.required, Validators.maxLength(255)]
          : [Validators.maxLength(255)],
      );
      perda.controls.motivo.updateValueAndValidity({ emitEvent: false });
    });
    return perda;
  }
}
