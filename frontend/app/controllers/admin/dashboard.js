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
  @tracked allAnalyses = true;
  @tracked showExportModal = false;

  // === NOUVEAUX FILTRES ===
  @tracked filterName = '';
  @tracked filterCompany = '';
  @tracked filterEmail = '';
  @tracked filterScoreMin = '';
  @tracked filterScoreMax = '';
  @tracked filterStatus = ''; // 'all', 'completed', 'pending', etc.

  constructor() {
    super(...arguments);
    this.selectedAnalysesIds = [];
  }

  get specificDays() {
    return !this.allAnalyses;
  }

  // === COMPUTED PROPERTY POUR FILTRER ===
  get filteredAnalyses() {
    let filtered = this.analyses;

    // Filtre par nom
    if (this.filterName.trim()) {
      const searchName = this.filterName.toLowerCase().trim();
      filtered = filtered.filter(analysis => 
        analysis.name?.toLowerCase().includes(searchName)
      );
    }

    // Filtre par company
    if (this.filterCompany.trim()) {
      const searchCompany = this.filterCompany.toLowerCase().trim();
      filtered = filtered.filter(analysis => 
        analysis.company?.toLowerCase().includes(searchCompany)
      );
    }

    // Filtre par email
    if (this.filterEmail.trim()) {
      const searchEmail = this.filterEmail.toLowerCase().trim();
      filtered = filtered.filter(analysis => 
        analysis.user?.email?.toLowerCase().includes(searchEmail)
      );
    }

    // Filtre par score minimum
    if (this.filterScoreMin !== '') {
      const minScore = parseFloat(this.filterScoreMin);
      if (!isNaN(minScore)) {
        filtered = filtered.filter(analysis => 
          analysis.score !== null && analysis.score >= minScore
        );
      }
    }

    // Filtre par score maximum
    if (this.filterScoreMax !== '') {
      const maxScore = parseFloat(this.filterScoreMax);
      if (!isNaN(maxScore)) {
        filtered = filtered.filter(analysis => 
          analysis.score !== null && analysis.score <= maxScore
        );
      }
    }

    // Filtre par status
    if (this.filterStatus && this.filterStatus !== 'all') {
      filtered = filtered.filter(analysis => 
        analysis.analysis_status === this.filterStatus
      );
    }

    return filtered;
  }

  // === ACTIONS POUR METTRE À JOUR LES FILTRES ===
  @action
  updateFilterName(event) {
    this.filterName = event.target.value;
  }

  @action
  updateFilterCompany(event) {
    this.filterCompany = event.target.value;
  }

  @action
  updateFilterEmail(event) {
    this.filterEmail = event.target.value;
  }

  @action
  updateFilterScoreMin(event) {
    this.filterScoreMin = event.target.value;
  }

  @action
  updateFilterScoreMax(event) {
    this.filterScoreMax = event.target.value;
  }

  @action
  updateFilterStatus(event) {
    this.filterStatus = event.target.value;
  }

  @action
  resetFilters() {
    this.filterName = '';
    this.filterCompany = '';
    this.filterEmail = '';
    this.filterScoreMin = '';
    this.filterScoreMax = '';
    this.filterStatus = '';
  }

  get formattedDate() {
    if (!this.currentDate) return '';
    const date = new Date(this.currentDate);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    });
  }

  get hasSelectedAnalyses() {
    return this.selectedAnalysesIds.length > 0;
  }

  get selectedCount() {
    return this.selectedAnalysesIds.length;
  }

  get allSelected() {
    return this.filteredAnalyses.length > 0 && 
           this.selectedAnalysesIds.length === this.filteredAnalyses.length;
  }

  @action
  toogleDays() {
    if (this.allAnalyses) {
      this.loadAllAnalyses();
    }
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
    this.allAnalyses = true;

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
  loadAll() {
    this.loadAllAnalyses();
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
      this.selectedAnalysesIds = this.filteredAnalyses.map(a => a.id);
    } else {
      this.selectedAnalysesIds = [];
    }
  }

  @action
  toggleAllAnalysesButton(){
      this.selectedAnalysesIds = this.filteredAnalyses.map(a => a.id);

  }

  @action
  goToAnalysis(analysisId) {
    this.router.transitionTo('analysis', { queryParams: { id: analysisId } });
  }

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
  
  this.closeExportModal();
  
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

    // Créer un blob et déclencher le téléchargement
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

if(exportOptions.separateFiles.results){
  const response = await fetch('http://localhost:8000/api/admin/exportResultsFiles', {
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
    throw new Error('Erreur lors de l\'export des résultats');
  }

  // Télécharger le ZIP
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `export_results_${Date.now()}.zip`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

if(exportOptions.separateFiles.calculationModel){
  const response = await fetch('http://localhost:8000/api/admin/exportCalculationModel', {
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
    throw new Error('Erreur lors de l\'export des résultats');
  }

  // Télécharger le ZIP
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `calculation_model_${Date.now()}.zip`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

if(exportOptions.separateFiles.justification){
  const response = await fetch('http://localhost:8000/api/admin/exportJustifications', {
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
    throw new Error('Erreur lors de l\'export des résultats');
  }

  // Télécharger le ZIP
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `justifications_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}


  } catch (error) {
    console.error('Erreur:', error);
    alert('Erreur lors de l\'export');
  }
}
}