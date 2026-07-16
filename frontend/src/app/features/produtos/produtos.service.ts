import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface Produto {
  id: number;
  nome: string;
  preco_venda: number;
  ativo: boolean;
  imagem_url: string | null;
  video_url: string | null;
  custo_producao: number;
  lucro_estimado: number;
  composicao: ComposicaoProduto[];
}

export interface ComposicaoProduto {
  material_id: number;
  material_nome: string;
  unidade_base: string;
  valor_compra: number;
  quantidade_por_compra: number;
  quantidade_utilizada: number;
  custo_unitario_base: number;
  custo_item: number;
}

export interface ProdutoCreate {
  nome: string;
  preco_venda: number;
  composicao: { material_id: number; quantidade_utilizada: number }[];
}

interface ListaProdutos {
  items: Produto[];
  total: number;
}

export type TipoMidia = 'imagem' | 'video';

@Injectable({ providedIn: 'root' })
export class ProdutosService {
  private readonly http = inject(HttpClient);

  listar(): Observable<ListaProdutos> {
    return this.http.get<ListaProdutos>('/api/produtos');
  }

  obter(produtoId: number): Observable<Produto> {
    return this.http.get<Produto>(`/api/produtos/${produtoId}`);
  }

  criar(dados: ProdutoCreate): Observable<Produto> {
    return this.http.post<Produto>('/api/produtos', dados);
  }

  excluir(produtoId: number): Observable<void> {
    return this.http.delete<void>(`/api/produtos/${produtoId}`);
  }

  enviarMidia(produtoId: number, tipo: TipoMidia, arquivo: File): Observable<Produto> {
    const dados = new FormData();
    dados.append('arquivo', arquivo);
    return this.http.post<Produto>(`/api/produtos/${produtoId}/${tipo}`, dados);
  }

  enviarImagem(produtoId: number, arquivo: File): Observable<Produto> {
    return this.enviarMidia(produtoId, 'imagem', arquivo);
  }

  enviarVideo(produtoId: number, arquivo: File): Observable<Produto> {
    return this.enviarMidia(produtoId, 'video', arquivo);
  }

  removerMidia(produtoId: number, tipo: TipoMidia): Observable<Produto> {
    return this.http.delete<Produto>(`/api/produtos/${produtoId}/${tipo}`);
  }

  removerImagem(produtoId: number): Observable<Produto> {
    return this.removerMidia(produtoId, 'imagem');
  }

  removerVideo(produtoId: number): Observable<Produto> {
    return this.removerMidia(produtoId, 'video');
  }
}
