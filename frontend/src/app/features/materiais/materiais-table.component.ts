import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { Material } from './materiais.service';
@Component({ selector:'app-materiais-table',standalone:true,imports:[CurrencyPipe,DecimalPipe,RouterLink,MatButtonModule,MatCardModule],templateUrl:'./materiais-table.component.html',styleUrl:'./materiais-table.component.scss'})
export class MateriaisTableComponent { @Input({required:true}) materiais: Material[]=[]; }
