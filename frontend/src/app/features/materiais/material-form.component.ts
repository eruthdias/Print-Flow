import { CurrencyPipe } from '@angular/common';
import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { MateriaisService } from './materiais.service';
import { FeedbackService } from '../../core/feedback.service';

@Component({ selector: 'app-material-form', standalone: true, imports: [CurrencyPipe, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule, MatSelectModule], templateUrl: './material-form.component.html', styleUrl: './material-form.component.scss' })
export class MaterialFormComponent {
  @Output() readonly salvo = new EventEmitter<void>();
  private readonly service = inject(MateriaisService);
  private readonly feedback = inject(FeedbackService);
  protected readonly unidades = ['un', 'folha', 'pacote', 'ml', 'l', 'g', 'kg', 'cm', 'm', 'cm2', 'm2', 'cx', 'rolo'];
  protected readonly enviando = signal(false);
  protected readonly erro = signal<string | null>(null);
  protected readonly form = new FormGroup({
    nome: new FormControl('', { nonNullable: true, validators: Validators.required }),
    unidade_compra: new FormControl('', { nonNullable: true, validators: Validators.required }),
    unidade_base: new FormControl('', { nonNullable: true, validators: Validators.required }),
    fator_conversao: new FormControl(1, { nonNullable: true, validators: [Validators.required, Validators.min(.001)] }),
    valor_compra: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
    quantidade_atual: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
    quantidade_minima: new FormControl(0, { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
  });

  protected custoUnitarioPrevisto(): number {
    const { valor_compra, fator_conversao } = this.form.getRawValue();
    return fator_conversao > 0 ? valor_compra / fator_conversao : 0;
  }

  protected salvar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); this.feedback.erro('Preencha corretamente os campos obrigatórios.'); return; }
    this.enviando.set(true); this.erro.set(null);
    this.service.criar(this.form.getRawValue()).pipe(finalize(() => this.enviando.set(false))).subscribe({
      next: () => { this.form.reset({ nome: '', unidade_compra: '', unidade_base: '', fator_conversao: 1, valor_compra: 0, quantidade_atual: 0, quantidade_minima: 0 }); this.feedback.sucesso('Material cadastrado com sucesso.'); this.salvo.emit(); },
      error: (e) => { const mensagem=this.feedback.mensagemErro(e,'Não foi possível salvar o material.'); this.erro.set(mensagem); this.feedback.erro(mensagem); },
    });
  }
}
