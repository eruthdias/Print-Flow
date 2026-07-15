import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface ProducaoItem {
  material_id: number;
  material_nome: string;
  unidade_base: string;
  quantidade_consumida: number;
  custo_unitario_snapshot: number;
  custo_total_item: number;
}

export interface DesperdicioProducao {
  id: number;
  material_id: number;
  material_nome: string;
  unidade_base: string;
  quantidade_perdida: number;
  motivo: string;
  custo_perda: number;
}

export interface Producao {
  id: number;
  produto_id: number;
  produto_nome: string;
  quantidade_produzida: number;
  data_producao: string;
  custo_materiais: number;
  custo_desperdicios: number;
  custo_total: number;
  valor_total: number;
  lucro_total: number;
  itens: ProducaoItem[];
  desperdicios: DesperdicioProducao[];
}

export interface ProducaoCreate {
  produto_id: number;
  quantidade_produzida: number;
  data_producao?: string;
  desperdicios: { material_id: number; quantidade_perdida: number; motivo: string }[];
}

interface ListaProducoes {
  items: Producao[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class ProducoesService {
  private readonly http = inject(HttpClient);

  listar(): Observable<ListaProducoes> {
    return this.http.get<ListaProducoes>('/api/producoes');
  }

  obter(producaoId: number): Observable<Producao> {
    return this.http.get<Producao>(`/api/producoes/${producaoId}`);
  }

  criar(dados: ProducaoCreate): Observable<Producao> {
    return this.http.post<Producao>('/api/producoes', dados);
  }

  estornar(producaoId: number): Observable<void> {
    return this.http.delete<void>(`/api/producoes/${producaoId}`);
  }
}
