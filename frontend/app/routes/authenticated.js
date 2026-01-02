// frontend/app/routes/authenticated.js
import Route from '@ember/routing/route';
import { inject as service } from '@ember/service';

/**
 * Route de base pour toutes les routes qui nécessitent une authentification
 * Toutes les routes protégées doivent étendre cette classe
 */
export default class AuthenticatedRoute extends Route {
  @service auth;
  @service router;

  /**
   * beforeModel se lance AVANT de charger n'importe quelle route
   * C'est ici qu'on vérifie si l'utilisateur est connecté
   */
  beforeModel(transition) {
    // Si l'utilisateur n'est PAS connecté
    if (!this.auth.isAuthenticated) {
      console.log('⛔ Accès refusé : utilisateur non connecté');
      
      // Sauvegarder l'URL qu'il voulait visiter
      // Pour le rediriger après la connexion
      const attemptedTransition = transition.to.name;
      localStorage.setItem('redirectAfterLogin', attemptedTransition);
      
      // Rediriger vers la page de login
      this.router.transitionTo('login');
    } else {
      console.log('✅ Utilisateur connecté:', this.auth.currentUser.email);
    }
  }
}