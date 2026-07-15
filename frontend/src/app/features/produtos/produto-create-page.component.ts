import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ProdutoFormComponent } from './produto-form.component';
@Component({selector:'app-produto-create-page',standalone:true,imports:[RouterLink,MatButtonModule,MatIconModule,ProdutoFormComponent],template:`<section class="page-shell form-page"><header class="page-header"><div><h1>Novo produto</h1><p>Informe dados, composição e imagem do produto.</p></div><a mat-button routerLink="/produtos"><mat-icon>arrow_back</mat-icon>Voltar</a></header><app-produto-form /></section>`})
export class ProdutoCreatePageComponent{}
