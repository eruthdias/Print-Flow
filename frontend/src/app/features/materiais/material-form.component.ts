import { CurrencyPipe } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { Material, MateriaisService } from './materiais.service';
import { FeedbackService } from '../../core/feedback.service';

@Component({ selector: 'app-material-form', standalone: true, imports: [CurrencyPipe, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule, MatSelectModule], templateUrl: './material-form.component.html', styleUrl: './material-form.component.scss' })
export class MaterialFormComponent implements OnInit {
  @Input() material?: Material;
  @Output() readonly salvo = new EventEmitter<void>();
  private readonly service = inject(MateriaisService);
  private readonly feedback = inject(FeedbackService);
  private materialId?: number;
  protected readonly unidades = ['un', 'folha', 'pacote', 'ml', 'l', 'g', 'kg', 'cm', 'm', 'cm2', 'm2', 'cx', 'rolo'];
  protected readonly enviando = signal(false);
  protected readonly erro = signal<string | null>(null);
  protected readonly editando = signal(false);
  protected readonly form = new FormGroup({
    nome: new FormControl('', { nonNullable: true, validators: Validators.required }),
    unidade_compra: new FormControl('', { nonNullable: true, validators: Validators.required }),
    unidade_base: new FormControl('', { nonNullable: true, validators: Validators.required }),
    fator_conversao: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(.001)] }),
    valor_compra: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
    quantidade_atual: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
    quantidade_minima: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
  });

  ngOnInit(): void {
    if (this.material) {
      this.materialId = this.material.id;
      this.editando.set(true);
      this.form.patchValue({
        nome: this.material.nome,
        unidade_compra: this.material.unidade_compra,
        unidade_base: this.material.unidade_base,
        fator_conversao: this.material.fator_conversao,
        valor_compra: this.material.valor_compra,
        quantidade_atual: this.material.quantidade_atual,
        quantidade_minima: this.material.quantidade_minima,
      });
    }
  }

  protected custoUnitarioPrevisto(): number {
    const { valor_compra, fator_conversao } = this.form.getRawValue();
    return fator_conversao > 0 ? valor_compra / fator_conversao : 0;
  }

  protected salvar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); this.feedback.erro('Preencha corretamente os campos obrigatórios.'); return; }
    this.enviando.set(true); this.erro.set(null);
    const dados = this.form.getRawValue();
    const obs$ = this.materialId
      ? this.service.atualizar(this.materialId, {
          nome: dados.nome,
          unidade_compra: dados.unidade_compra,
          unidade_base: dados.unidade_base,
          fator_conversao: dados.fator_conversao,
          valor_compra: dados.valor_compra,
          quantidade_minima: dados.quantidade_minima,
        })
      : this.service.criar(dados);
    obs$.pipe(finalize(() => this.enviando.set(false))).subscribe({
      next: () => {
        if (!this.materialId) { this.form.reset({ nome: '', unidade_compra: '', unidade_base: '', fator_conversao: 0, valor_compra: 0, quantidade_atual: 0, quantidade_minima: 0 }); }
        this.feedback.sucesso(this.materialId ? 'Material atualizado com sucesso.' : 'Material cadastrado com sucesso.');
        this.salvo.emit();
      },
      error: (e) => { const mensagem=this.feedback.mensagemErro(e,'Não foi possível salvar o material.'); this.erro.set(mensagem); this.feedback.erro(mensagem); },
    });
  }
}
