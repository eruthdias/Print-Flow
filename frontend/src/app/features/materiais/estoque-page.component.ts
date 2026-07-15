import { Component,OnInit,inject,signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Material,MateriaisService } from './materiais.service';
import { EstoqueFormComponent } from './estoque-form.component';
@Component({selector:'app-estoque-page',standalone:true,imports:[RouterLink,MatButtonModule,MatIconModule,EstoqueFormComponent],template:`<section class="page-shell form-page"><header class="page-header"><div><h1>Ajuste de estoque</h1><p>Registre entradas ou saídas de materiais.</p></div><a mat-button routerLink="/materiais"><mat-icon>arrow_back</mat-icon>Voltar</a></header><app-estoque-form [materiais]="materiais()" /></section>`})
export class EstoquePageComponent implements OnInit{private readonly service=inject(MateriaisService);protected readonly materiais=signal<Material[]>([]);ngOnInit():void{this.service.listar().subscribe(r=>this.materiais.set(r.items.filter(m=>m.ativo)));}}
