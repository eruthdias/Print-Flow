import { Injectable, inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({ providedIn: 'root' })
export class FeedbackService {
  private readonly snackBar = inject(MatSnackBar);
  sucesso(mensagem: string): void { this.abrir(mensagem, 'mensagem-sucesso'); }
  erro(mensagem: string): void { this.abrir(mensagem, 'mensagem-erro'); }
  mensagemErro(erro: any, padrao: string): string { return erro?.error?.detail ?? padrao; }
  private abrir(mensagem: string, classe: string): void { this.snackBar.open(mensagem, 'Fechar', { duration: 4500, horizontalPosition: 'right', verticalPosition: 'top', panelClass: classe }); }
}
