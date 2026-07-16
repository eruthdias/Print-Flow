import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { Producao } from './producoes.service';
import { ProducaoFormComponent } from './producao-form.component';

export interface ProducaoFormDialogData {
  producao?: Producao;
}

@Component({
  selector: 'app-producao-form-dialog',
  standalone: true,
  imports: [MatDialogModule, ProducaoFormComponent],
  template: `
    <mat-dialog-content>
      <app-producao-form [producao]="data.producao" (salvo)="dialogRef.close(true)" />
    </mat-dialog-content>
  `,
})
export class ProducaoFormDialogComponent {
  protected readonly dialogRef = inject(MatDialogRef<ProducaoFormDialogComponent>);
  protected readonly data = inject<ProducaoFormDialogData>(MAT_DIALOG_DATA);
}
