import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { Material } from './materiais.service';
import { MaterialFormComponent } from './material-form.component';

export interface MaterialFormDialogData {
  material?: Material;
}

@Component({
  selector: 'app-material-form-dialog',
  standalone: true,
  imports: [MatDialogModule, MaterialFormComponent],
  template: `
    <mat-dialog-content>
      <app-material-form [material]="data.material" (salvo)="dialogRef.close(true)" />
    </mat-dialog-content>
  `,
})
export class MaterialFormDialogComponent {
  protected readonly dialogRef = inject(MatDialogRef<MaterialFormDialogComponent>);
  protected readonly data = inject<MaterialFormDialogData>(MAT_DIALOG_DATA);
}
