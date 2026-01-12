// app/routes/admin/users.js
import Route from '@ember/routing/route';
import { inject as service } from '@ember/service';
import AuthenticatedRoute from '../authenticated';
import ENV from 'frontend/config/environment';

export default class AdminUsersRoute extends AuthenticatedRoute {
  @service auth;

  async model() {
    try {
      const token = this.auth.token;
      
      const response = await fetch(`${ENV.APP.apiUrl}/api/users`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'a    pplication/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des utilisateurs');
      }
      
      const users = await response.json();
      return { users };
      
    } catch (error) {
      console.error('Erreur:', error);
      return { users: [] };
    }
  }

  // ⭐ AJOUT : Initialiser le contrôleur avec les données
  setupController(controller, model) {
    super.setupController(controller, model);
    // Initialiser la liste trackée dans le contrôleur
    controller.usersList = model.users;
  }
}