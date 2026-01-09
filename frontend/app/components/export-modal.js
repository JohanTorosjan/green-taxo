// frontend/app/components/export-modal.js
import Component from '@glimmer/component';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';

export default class ExportModalComponent extends Component {
  // Colonnes cochées par défaut
  @tracked includeId = true;
  @tracked includeName = true;
  @tracked includeCreatedAt = true;
  @tracked includeDocDate = true;
  @tracked includeUserEmail = true;
  @tracked includeScore = true;

  // Colonnes JSON non cochées par défaut
  @tracked includeFullResults = false;
  @tracked includeCalculationModel = false;

  // Fichiers séparés non cochés par défaut
  @tracked exportResultsFiles = false;
  @tracked exportCalculationFiles = false;
  @tracked exportJustificationFile = false;

  get exportOptions() {
    return {
      // Colonnes de base
      columns: {
        id: this.includeId,
        name: this.includeName,
        created_at: this.includeCreatedAt,
        doc_date: this.includeDocDate,
        user_email: this.includeUserEmail,
        score: this.includeScore,
        full_results: this.includeFullResults,
        calculation_model: this.includeCalculationModel
      },
      // Fichiers séparés
      separateFiles: {
        results: this.exportResultsFiles,
        calculationModel: this.exportCalculationFiles,
        justification: this.exportJustificationFile
      }
    };
  }

  get hasAnySeparateFileSelected() {
    return this.exportResultsFiles || 
           this.exportCalculationFiles || 
           this.exportJustificationFile;
  }

  @action
  toggleColumn(columnName) {
    this[columnName] = !this[columnName];
  }

  @action
  closeModal() {
    if (this.args.onClose) {
      this.args.onClose();
    }
  }

  @action
  confirmExport() {
    if (this.args.onConfirm) {
      this.args.onConfirm(this.exportOptions);
    }
  }

  @action
  selectAll() {
    this.includeId = true;
    this.includeName = true;
    this.includeCreatedAt = true;
    this.includeDocDate = true;
    this.includeUserEmail = true;
    this.includeScore = true;
    this.includeFullResults = true;
    this.includeCalculationModel = true;
  }

  @action
  deselectAll() {
    this.includeId = false;
    this.includeName = false;
    this.includeCreatedAt = false;
    this.includeDocDate = false;
    this.includeUserEmail = false;
    this.includeScore = false;
    this.includeFullResults = false;
    this.includeCalculationModel = false;
  }
}