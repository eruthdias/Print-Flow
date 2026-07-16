import { Routes } from '@angular/router';
import { LayoutComponent } from './features/layout/layout.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { MateriaisComponent } from './features/materiais/materiais.component';
import { ProdutosComponent } from './features/produtos/produtos.component';
import { ProducoesComponent } from './features/producoes/producoes.component';
import { RelatoriosComponent } from './features/relatorios/relatorios.component';
import { ProdutoDetalheComponent } from './features/produtos/produto-detalhe.component';
import { MaterialCreatePageComponent } from './features/materiais/material-create-page.component';
import { EstoquePageComponent } from './features/materiais/estoque-page.component';
import { ProdutoCreatePageComponent } from './features/produtos/produto-create-page.component';
import { ProducaoFormComponent } from './features/producoes/producao-form.component';
import { ProducaoDetalheComponent } from './features/producoes/producao-detalhe.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'materiais', component: MateriaisComponent },
      { path: 'materiais/novo', component: MaterialCreatePageComponent },
      { path: 'materiais/ajuste', component: EstoquePageComponent },
      { path: 'produtos', component: ProdutosComponent },
      { path: 'produtos/novo', component: ProdutoCreatePageComponent },
      { path: 'produtos/:id', component: ProdutoDetalheComponent },
      { path: 'producoes', component: ProducoesComponent },
      { path: 'producoes/nova', component: ProducaoFormComponent },
      { path: 'producoes/:id', component: ProducaoDetalheComponent },
      { path: 'relatorios', component: RelatoriosComponent },
    ],
  },
];
