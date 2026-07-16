import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { Produto } from './produtos.service';
import { ProdutoFormComponent } from './produto-form.component';

export interface ProdutoFormDialogData {
  produto?: Produto;
}

@Component({
  selector: 'app-produto-form-dialog',
  standalone: true,
  imports: [MatDialogModule, ProdutoFormComponent],
  template: `
    <mat-dialog-content>
      <app-produto-form [produto]="data.produto" (salvo)="dialogRef.close(true)" />
    </mat-dialog-content>
  `,
})
export class ProdutoFormDialogComponent {
  protected readonly dialogRef = inject(MatDialogRef<ProdutoFormDialogComponent>);
  protected readonly data = inject<ProdutoFormDialogData>(MAT_DIALOG_DATA);
}
