// frontend/app/routes/login.js
import Route from '@ember/routing/route';
import { inject as service } from '@ember/service';

export default class LoginRoute extends Route {
  @service auth;
  @service router;

  /**
   * beforeModel se lance AVANT de charger la page
   * Si l'utilisateur est déjà connecté, on le redirige
   */
  beforeModel() {
    if (this.auth.isAuthenticated) {
      console.log('✅ Déjà connecté, redirection...');
      this.router.transitionTo('index'); // Redirige vers la page d'accueil
    }
  }
}