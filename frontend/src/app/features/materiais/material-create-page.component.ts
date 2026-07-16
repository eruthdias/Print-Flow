import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MaterialFormComponent } from './material-form.component';
@Component({selector:'app-material-create-page',standalone:true,imports:[RouterLink,MatButtonModule,MatIconModule,MaterialFormComponent],template:`<section class="page-shell form-page"><header class="page-header"><div><h1>Novo material</h1><p>Cadastre os dados de compra e controle de estoque.</p></div><a mat-button routerLink="/materiais"><mat-icon>arrow_back</mat-icon>Voltar</a></header><app-material-form /></section>`})
export class MaterialCreatePageComponent{}
