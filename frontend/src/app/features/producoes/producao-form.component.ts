import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormArray, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { FeedbackService } from '../../core/feedback.service';
import { ComposicaoProduto, Produto, ProdutosService } from '../produtos/produtos.service';
import { Producao, ProducoesService } from './producoes.service';

type PerdaForm = FormGroup<{
  material_id: FormControl<number>;
  quantidade_perdida: FormControl<number>;
  motivo: FormControl<string>;
}>;

@Component({
  selector: 'app-producao-form',
  standalone: true,
  imports: [CurrencyPipe, DecimalPipe, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule],
  templateUrl: './producao-form.component.html',
  styleUrl: './producao-form.component.scss',
})
export class ProducaoFormComponent implements OnInit {
  @Input() producao?: Producao;
  @Output() readonly salvo = new EventEmitter<void>();
  private readonly produtosService = inject(ProdutosService);
  private readonly service = inject(ProducoesService);
  private readonly feedback = inject(FeedbackService);
  private producaoId?: number;

  protected readonly produtos = signal<Produto[]>([]);
  protected readonly enviando = signal(false);
  protected readonly editando = signal(false);
  protected readonly form = new FormGroup({
    produto_id: new FormControl<number | null>(null, Validators.required),
    quantidade_produzida: new FormControl(1, { nonNullable: true, validators: [Validators.required, Validators.min(.001)] }),
    data_producao: new FormControl('', { nonNullable: true }),
    desperdicios: new FormArray<PerdaForm>([]),
  });

  ngOnInit(): void {
    this.produtosService.listar().subscribe({
      next: ({ items }) => {
        this.produtos.set(items.filter((produto) => produto.ativo || produto.id === this.producao?.produto_id));
        if (this.producao) { this.preencherParaEdicao(this.producao); }
      },
      error: (erro) => this.feedback.erro(
        this.feedback.mensagemErro(erro, 'Não foi possível carregar os produtos.'),
      ),
    });
    this.form.controls.produto_id.valueChanges.subscribe(() => {
      if (!this.editando()) { this.montarDesperdicios(); }
    });
  }

  private preencherParaEdicao(producao: Producao): void {
    this.producaoId = producao.id;
    this.editando.set(true);
    this.form.patchValue({ produto_id: producao.produto_id }, { emitEvent: false });
    this.montarDesperdicios();
    const perdasExistentes = new Map(producao.desperdicios.map((item) => [item.material_id, item]));
    for (const perda of this.form.controls.desperdicios.controls) {
      const existente = perdasExistentes.get(perda.controls.material_id.value);
      if (existente) {
        perda.patchValue({ quantidade_perdida: existente.quantidade_perdida, motivo: existente.motivo });
      }
    }
    this.form.patchValue({
      quantidade_produzida: producao.quantidade_produzida,
      data_producao: producao.data_producao,
    });
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

    const payload = {
      produto_id: Number(dados.produto_id),
      quantidade_produzida: dados.quantidade_produzida,
      ...(dados.data_producao ? { data_producao: dados.data_producao } : {}),
      desperdicios,
    };

    this.enviando.set(true);
    (this.producaoId ? this.service.atualizar(this.producaoId, payload) : this.service.criar(payload))
      .pipe(finalize(() => this.enviando.set(false)))
      .subscribe({
        next: () => {
          this.feedback.sucesso(
            this.producaoId
              ? 'Produção atualizada e estoque ajustado com sucesso.'
              : 'Produção registrada e estoque atualizado com sucesso.',
          );
          this.salvo.emit();
        },
        error: (erro) => this.feedback.erro(
          this.feedback.mensagemErro(erro, 'Não foi possível salvar a produção.'),
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
