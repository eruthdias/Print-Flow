import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, EventEmitter, OnInit, Output, inject, signal } from '@angular/core';
import { FormArray, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize, switchMap } from 'rxjs';
import { Material, MateriaisService } from '../materiais/materiais.service';
import { ProdutosService } from './produtos.service';
import { FeedbackService } from '../../core/feedback.service';

type ItemForm = FormGroup<{ material_id: FormControl<number | null>; quantidade_utilizada: FormControl<number> }>;

@Component({ selector:'app-produto-form',standalone:true,imports:[CurrencyPipe,DecimalPipe,ReactiveFormsModule,MatButtonModule,MatCardModule,MatFormFieldModule,MatIconModule,MatInputModule,MatSelectModule],templateUrl:'./produto-form.component.html',styleUrl:'./produto-form.component.scss' })
export class ProdutoFormComponent implements OnInit {
  @Output() readonly salvo = new EventEmitter<void>();
  private readonly produtos = inject(ProdutosService); private readonly materiaisService=inject(MateriaisService);
  private readonly feedback=inject(FeedbackService);
  protected readonly materiais=signal<Material[]>([]); protected readonly imagem=signal<File|null>(null); protected readonly preview=signal<string|null>(null); protected readonly enviando=signal(false); protected readonly erro=signal<string|null>(null);
  protected readonly form=new FormGroup({ nome:new FormControl('',{nonNullable:true,validators:Validators.required}), preco_venda:new FormControl(0,{nonNullable:true,validators:[Validators.required,Validators.min(0)]}), composicao:new FormArray<ItemForm>([this.novoItem()]) });
  ngOnInit():void{this.materiaisService.listar().subscribe({next:r=>this.materiais.set(r.items.filter(m=>m.ativo))});}
  protected adicionar():void{this.form.controls.composicao.push(this.novoItem());}
  protected remover(i:number):void{const composicao=this.form.controls.composicao;if(composicao.length>1){composicao.removeAt(i);return;}composicao.at(0).reset({material_id:null,quantidade_utilizada:1});}
  protected selecionar(event:Event):void{const file=(event.target as HTMLInputElement).files?.[0]??null;this.imagem.set(file);const old=this.preview();if(old)URL.revokeObjectURL(old);this.preview.set(file?URL.createObjectURL(file):null);}
  protected custoPrevisto():number{return this.form.controls.composicao.controls.reduce((total,item)=>{const v=item.getRawValue();const material=this.materiais().find(m=>m.id===v.material_id);return total+(material?.custo_unitario_base??0)*v.quantidade_utilizada;},0);}
  protected custoItemPrevisto(indice:number):number{const v=this.form.controls.composicao.at(indice).getRawValue();const material=this.materiais().find(m=>m.id===v.material_id);return (material?.custo_unitario_base??0)*v.quantidade_utilizada;}
  protected lucroPrevisto():number{return this.form.controls.preco_venda.value-this.custoPrevisto();}
  protected salvar():void{if(this.form.invalid){this.form.markAllAsTouched();this.feedback.erro('Preencha os dados e a composição do produto.');return;}const v=this.form.getRawValue();const imagem=this.imagem();this.enviando.set(true);this.erro.set(null);const criar=this.produtos.criar({nome:v.nome.trim(),preco_venda:v.preco_venda,composicao:v.composicao.map(i=>({material_id:Number(i.material_id),quantidade_utilizada:i.quantidade_utilizada}))});(imagem?criar.pipe(switchMap(p=>this.produtos.enviarImagem(p.id,imagem))):criar).pipe(finalize(()=>this.enviando.set(false))).subscribe({next:()=>{this.form.reset({nome:'',preco_venda:0});this.form.controls.composicao.clear();this.form.controls.composicao.push(this.novoItem());this.imagem.set(null);this.preview.set(null);this.feedback.sucesso('Produto cadastrado com sucesso.');this.salvo.emit();},error:e=>{const mensagem=this.feedback.mensagemErro(e,'Não foi possível salvar o produto.');this.erro.set(mensagem);this.feedback.erro(mensagem);}});}
  private novoItem():ItemForm{return new FormGroup({material_id:new FormControl<number|null>(null,Validators.required),quantidade_utilizada:new FormControl(1,{nonNullable:true,validators:[Validators.required,Validators.min(.001)]})});}
}
