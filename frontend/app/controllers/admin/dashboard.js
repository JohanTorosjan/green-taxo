// frontend/app/controllers/admin/dashboard.js
import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class AdminDashboardController extends Controller {
  @service auth;
  @service router;

  @tracked currentDate = null;
  @tracked analyses = [];
  @tracked isLoading = false;
  @tracked error = null;
  @tracked selectedAnalysesIds = [];
  @tracked allAnalyses=true;
  @tracked showExportModal = false; // Nouvelle propriété

  constructor() {
    super(...arguments);
    this.selectedAnalysesIds = [];
  }

  get specificDays(){
    return !this.allAnalyses;
  }


  @action toogleDays(){
    if(this.allAnalyses){
        this.loadAllAnalyses()
    }
  }

  get formattedDate() {
    if (!this.currentDate) return '';
    const date = new Date(this.currentDate);
    return date.toLocaleDateString('fr-FR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }

  get hasSelectedAnalyses() {
    return this.selectedAnalysesIds.length > 0;
  }

  get selectedCount() {
    return this.selectedAnalysesIds.length;
  }

  get allSelected() {
    return this.analyses.length > 0 && 
           this.selectedAnalysesIds.length === this.analyses.length;
  }

  @action
  async loadAnalyses(date) {
    this.allAnalyses = false;
    this.isLoading = true;
    this.error = null;
    this.currentDate = date;
    this.selectedAnalysesIds = [];

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/dashboard/analyses?target_date=${date}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des analyses');
      }

      const data = await response.json();
      this.analyses = data.analyses || [];
      
    } catch (error) {
      this.error = error.message;
      console.error('Erreur:', error);
    } finally {
      this.isLoading = false;
    }
  }



  @action
  async loadAllAnalyses() {
    this.isLoading = true;
    this.error = null;
    this.selectedAnalysesIds = [];
    this.allAnalyses=true;

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/dashboard/fullanalyses`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des analyses');
      }

      const data = await response.json();
      this.analyses = data.analyses || [];
      
    } catch (error) {
      this.error = error.message;
      console.error('Erreur:', error);
    } finally {
      this.isLoading = false;
    }
  }


  @action
  previousDay() {
    const date = new Date(this.currentDate);
    date.setDate(date.getDate() - 1);
    const newDate = date.toISOString().split('T')[0];
    this.loadAnalyses(newDate);
  }

  @action 
  loadAll(){
    this.loadAllAnalyses()
  }

  @action
  nextDay() {
    const date = new Date(this.currentDate);
    date.setDate(date.getDate() + 1);
    const newDate = date.toISOString().split('T')[0];
    this.loadAnalyses(newDate);
  }

  @action
  goToToday() {
    const today = new Date().toISOString().split('T')[0];
    this.loadAnalyses(today);
  }

  @action
  toggleAnalysisSelection(analysisId) {
    if (this.selectedAnalysesIds.includes(analysisId)) {
      this.selectedAnalysesIds = this.selectedAnalysesIds.filter(id => id !== analysisId);
    } else {
      this.selectedAnalysesIds = [...this.selectedAnalysesIds, analysisId];
    }
  }

  @action
  toggleAllAnalyses(event) {
    if (event.target.checked) {
      this.selectedAnalysesIds = this.analyses.map(a => a.id);
    } else {
      this.selectedAnalysesIds = [];
    }
  }

  @action
  goToAnalysis(analysisId) {
    this.router.transitionTo('analysis', { queryParams: { id: analysisId } });
  }

  // Nouvelles actions pour la modale
  @action
  openExportModal() {
    this.showExportModal = true;
  }

  @action
  closeExportModal() {
    this.showExportModal = false;
  }

  @action
  async handleExportConfirm(exportOptions) {
    console.log('Options d\'export:', exportOptions);
    console.log('Analyses à exporter:', this.selectedAnalysesIds);
    
    // Fermer la modale
    this.closeExportModal();
    
    // TODO: Implémenter l'appel API pour l'export
    try {
      const response = await fetch('http://localhost:8000/api/admin/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          analysis_ids: this.selectedAnalysesIds,
          export_options: exportOptions
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'export');
      }

      // Télécharger le fichier
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export_analyses_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('Export réussi !');
    } catch (error) {
      console.error('Erreur lors de l\'export:', error);
      alert('Erreur lors de l\'export: ' + error.message);
    }
  }
}