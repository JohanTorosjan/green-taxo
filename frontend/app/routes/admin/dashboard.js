// frontend/app/routes/admin/dashboard.js
import Route from '@ember/routing/route';
import { inject as service } from '@ember/service';

export default class AdminDashboardRoute extends Route {
  @service router;



  model() {
    // Initialiser avec la date du jour
    const today = new Date().toISOString().split('T')[0]; // Format YYYY-MM-DD
    
    return {
      currentDate: today,
      analyses: []
    };
  }

  setupController(controller, model) {
    super.setupController(controller, model);
    
    // Charger les analyses du jour
    controller.loadAnalyses(model.currentDate);
  }
}