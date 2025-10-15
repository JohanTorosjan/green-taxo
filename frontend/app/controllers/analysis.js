import Controller from '@ember/controller';
import { inject as service } from '@ember/service';
import { action } from '@ember/object';
import { tracked } from '@glimmer/tracking';

export default class AnalysisDetailController extends Controller {
  @service router;
  @service store;
  
  @tracked isLoading = false;
  @tracked error = null;
@tracked expandedCriteria = [];

  get scorePercentage() {
    const analysis = this.model;
    return analysis?.score ? Math.round(analysis.score) : 0;
  }

  get scoreClass() {
    const score = this.scorePercentage;
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
    
    // Créer un map des résultats par nom
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
}