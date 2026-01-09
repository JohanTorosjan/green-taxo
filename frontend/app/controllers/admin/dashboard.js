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
  @tracked selectedAnalysesIds = []; // Utiliser un array au lieu d'un Set

  // Initialisation explicite
  constructor() {
    super(...arguments);
    this.selectedAnalysesIds = [];
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
    this.isLoading = true;
    this.error = null;
    this.currentDate = date;
    this.selectedAnalysesIds = []; // Réinitialiser les sélections

    try {
    //   const token = this.session.data.authenticated.token;
      const response = await fetch(
        `http://localhost:8000/api/admin/dashboard/analyses?target_date=${date}`,
        {
          headers: {
            // 'Authorization': `Bearer ${token}`,
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
      // Sélectionner toutes les analyses
      this.selectedAnalysesIds = this.analyses.map(a => a.id);
    } else {
      // Désélectionner toutes les analyses
      this.selectedAnalysesIds = [];
    }
  }

  @action
  goToAnalysis(analysisId) {
    this.router.transitionTo('analysis', { queryParams: { id: analysisId } });
  }

  @action
  exportSelected() {
    // TODO: Implémenter la logique d'export
    console.log('Export des analyses:', this.selectedAnalysesIds);
    alert(`Export de ${this.selectedAnalysesIds.length} analyse(s) - À implémenter`);
  }
}