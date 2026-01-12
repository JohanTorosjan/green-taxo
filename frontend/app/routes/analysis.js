import Route from '@ember/routing/route';
import { inject as service } from '@ember/service';

export default class AnalysisRoute extends Route {
  @service router;
  @service store;


  queryParams = {
    id: {
      refreshModel: true,
    },
  };

  async model(params) {
    try {
      const response = await fetch(`http://localhost:8000/analysis/${params.id}`);

      if (!response.ok) {
        if (response.status === 404) {
          this.router.transitionTo('not-found');
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const analysis = await response.json();
      console.log('📥 Analyse chargée:', analysis);
      return analysis;
      
    } catch (error) {
      console.error('❌ Erreur lors du chargement de l\'analyse:', error);
      this.router.transitionTo('error');
    }
  }

  setupController(controller, model) {
    super.setupController(controller, model);
    
    // Initialiser le contrôleur avec le modèle
    controller.set('model', model);
    
    // Démarrer le polling si l'analyse est en cours
    controller.startPollingIfNeeded();
  }

  // Important: arrêter le polling quand on quitte la route
  resetController(controller, isExiting) {
    if (isExiting) {
      controller.stopPolling();
    }
  }
}