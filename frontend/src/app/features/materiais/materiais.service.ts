import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface MateriaisResumo {
  materiais_cadastrados: number;
  materiais_em_estoque: number;
  materiais_sem_estoque: number;
  produtos_cadastrados: number;
  desperdicios_registrados: number;
  precisando_compra: number;
}

export interface Material {
  id: number;
  nome: string;
  unidade_compra: string;
  unidade_base: string;
  fator_conversao: number;
  valor_compra: number;
  custo_unitario_base: number;
  quantidade_atual: number;
  quantidade_minima: number;
  quantidade_atual_unidade_compra: number;
  estoque_baixo: boolean;
  ativo: boolean;
}

export interface ListaMateriais {
  items: Material[];
  total: number;
}

export interface MaterialRequest {
  nome: string;
  unidade_compra: string;
  unidade_base: string;
  fator_conversao: number;
  valor_compra: number;
  quantidade_atual: number;
  quantidade_minima: number;
}

export type MaterialUpdatePayload = Omit<MaterialRequest, 'quantidade_atual'>;

@Injectable({ providedIn: 'root' })
export class MateriaisService {
  private readonly http = inject(HttpClient);

  obterResumo(): Observable<MateriaisResumo> {
    return this.http.get<MateriaisResumo>('/api/materiais/resumo');
  }

  listar(): Observable<ListaMateriais> {
    return this.http.get<ListaMateriais>('/api/materiais');
  }

  obter(materialId: number): Observable<Material> {
    return this.http.get<Material>(`/api/materiais/${materialId}`);
  }

  criar(dados: MaterialRequest): Observable<Material> {
    return this.http.post<Material>('/api/materiais', dados);
  }

  atualizar(materialId: number, dados: MaterialUpdatePayload): Observable<Material> {
    return this.http.put<Material>(`/api/materiais/${materialId}`, dados);
  }

  excluir(materialId: number): Observable<void> {
    return this.http.delete<void>(`/api/materiais/${materialId}`);
  }

  ajustarEstoque(materialId: number, dados: { quantidade: number; operacao: 'entrada' | 'saida'; observacao?: string }): Observable<Material> {
    return this.http.post<Material>(`/api/materiais/${materialId}/ajuste-estoque`, dados);
  }
}
