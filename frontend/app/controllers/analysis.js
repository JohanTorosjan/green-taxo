import Controller from '@ember/controller';
import { inject as service } from '@ember/service';
import { action } from '@ember/object';
import { tracked } from '@glimmer/tracking';

export default class AnalysisDetailController extends Controller {
  @service router;
  @service store;
  @service auth;

  @tracked isLoading = false;
  @tracked error = null;
  @tracked expandedCriteria = [];
  @tracked pollingInterval = null;

  get scorePercentage() {
    const analysis = this.model;
    return analysis?.score ? Math.round(analysis.score) : 0;
  }

  get analysisStatus(){
    const analysis_status = this?.model.analysis_status;
    
    return analysis_status
  }

    get analysisScore(){
    const analysis_score = this?.model.score;
    
    return analysis_score
  }

  get scoreClass() {
    const score = this.scorePercentage;
    const status = this.model.analysis_status;
    if(status=='pending' ||status=='processing'){
      return 'loading'
    }
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-average';
    return 'score-poor';
  }

  get criteriaCount() {
    return this.model?.calculation_model?.length || 0;
  }

  get satisfiedCriteriaCount() {
    const results = this.model?.analysis_results || [];
    return results.filter(r => r.present === true).length;
  }

  get criteriaList() {
    const model = this.model?.calculation_model || [];
    const results = this.model?.analysis_results || [];
    
    const resultsMap = new Map(results.map(r => [r.name, r]));
    
    return model.map(criterion => {
      const result = resultsMap.get(criterion.nom);
      return {
        name: criterion.nom,
        description: criterion.description,
        coefficient: criterion.coefficient,
        present: result?.present || false,
        justification: result?.justification || null
      };
    });
  }

  // Démarrer le polling si nécessaire
  startPollingIfNeeded() {
    if ((this.model?.analysis_status === 'pending'|| this.model?.analysis_status === 'pending') && !this.pollingInterval ) {
      this.startPolling();
    }
  }

  // Démarrer le polling
  startPolling() {
    console.log('🔄 Démarrage du polling...');
    
    // Polling toutes les 3 secondes
    this.pollingInterval = setInterval(() => {
      this.refreshAnalysis();
    }, 3000);
  }

  // Arrêter le polling
  stopPolling() {
    if (this.pollingInterval) {
      console.log('⏹️ Arrêt du polling');
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  // Rafraîchir l'analyse
  async refreshAnalysis() {
    try {
      const response = await fetch(`http://localhost:8000/analysis/${this.model.id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const updatedAnalysis = await response.json();
      console.log('📊 Analyse mise à jour:', updatedAnalysis);
      
      // Mettre à jour le modèle
      this.model = updatedAnalysis;
      
      // Arrêter le polling si l'analyse est terminée
      if (updatedAnalysis.analysis_status !== 'pending' && updatedAnalysis.analysis_status !== 'processing') {
        console.log('✅ Analyse terminée, arrêt du polling');
        this.stopPolling();
      }
      
    } catch (error) {
      console.error('❌ Erreur lors du rafraîchissement:', error);
      this.error = error.message;
      this.stopPolling();
    }
  }

  @action
  toggleCriteria(criteriaName) {
    if (this.expandedCriteria.includes(criteriaName)) {
      this.expandedCriteria = this.expandedCriteria.filter(name => name !== criteriaName);
    } else {
      this.expandedCriteria = [...this.expandedCriteria, criteriaName];
    }
  }

  @action
  isCriteriaExpanded(criteriaName) {
    return this.expandedCriteria.includes(criteriaName);
  }

  @action
  goBack() {
    this.stopPolling(); // Important: arrêter le polling avant de quitter
    this.router.transitionTo('analysis.list');
  }

  @action
  downloadReport() {
    const analysis = this.model;
    const data = {
      id: analysis.id,
      name: analysis.name,
      score: analysis.score,
      status: analysis.analysis_status,
      date: analysis.created_at,
      criteria: this.criteriaList
    };
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(data, null, 2)));
    element.setAttribute('download', `analysis-${analysis.id}-report.json`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  // Nettoyage à la destruction du contrôleur
  willDestroy() {
    super.willDestroy(...arguments);
    this.stopPolling();
  }
  get isProcessing() {
  const status = this.model.analysis_status;
  return status === 'pending' || status === 'processing';
}
}

