import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface MaterialEstoqueBaixo {
  material_id: number;
  material_nome: string;
  quantidade_atual: number;
  quantidade_minima: number;
  unidade_base: string;
}

export interface DashboardResumo {
  data_inicio: string;
  data_fim: string;
  total_materiais: number;
  materiais_estoque_baixo_total: number;
  materiais_estoque_baixo: MaterialEstoqueBaixo[];
  total_produtos: number;
  producoes_realizadas: number;
  lucro_estimado: number;
  desperdicio_total: number;
  custo_total_producao: number;
  producoes_por_mes: { mes: string; quantidade: number; lucro: number }[];
  top_materiais_consumidos: { material: string; quantidade: number; unidade: string }[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  obter(): Observable<DashboardResumo> {
    return this.http.get<DashboardResumo>('/api/dashboard');
  }
}
