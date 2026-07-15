import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { Material, MateriaisService } from './materiais.service';
import { FeedbackService } from '../../core/feedback.service';

@Component({ selector: 'app-estoque-form', standalone: true, imports: [ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule, MatSelectModule], templateUrl: './estoque-form.component.html', styleUrl: './material-form.component.scss' })
export class EstoqueFormComponent {
  @Input({ required: true }) materiais: Material[] = [];
  @Output() readonly salvo = new EventEmitter<void>();
  private readonly service = inject(MateriaisService);
  private readonly feedback = inject(FeedbackService);
  protected readonly enviando = signal(false); protected readonly erro = signal<string | null>(null);
  protected readonly form = new FormGroup({ material_id: new FormControl<number | null>(null, Validators.required), quantidade: new FormControl(1, { nonNullable: true, validators: [Validators.required, Validators.min(.001)] }), operacao: new FormControl<'entrada'|'saida'>('entrada', { nonNullable: true }), observacao: new FormControl('', { nonNullable: true }) });
  protected salvar(): void { if (this.form.invalid) { this.form.markAllAsTouched(); this.feedback.erro('Selecione o material e informe uma quantidade válida.'); return; } const v=this.form.getRawValue(); this.enviando.set(true); this.service.ajustarEstoque(Number(v.material_id), { quantidade:v.quantidade, operacao:v.operacao, observacao:v.observacao||undefined }).pipe(finalize(()=>this.enviando.set(false))).subscribe({ next:()=>{this.form.reset({material_id:null,quantidade:1,operacao:'entrada',observacao:''});this.feedback.sucesso('Estoque ajustado com sucesso.');this.salvo.emit();}, error:e=>{const mensagem=this.feedback.mensagemErro(e,'Não foi possível salvar o ajuste.');this.erro.set(mensagem);this.feedback.erro(mensagem);} }); }
}
