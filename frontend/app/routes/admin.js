// frontend/app/routes/admin.js
import AuthenticatedRoute from './authenticated';
import { inject as service } from '@ember/service';

/**
 * Route pour la page admin
 * Nécessite une connexion ET d'être admin
 */
export default class AdminRoute extends AuthenticatedRoute {
  @service auth;
  @service router;

  /**
   * Après avoir vérifié l'authentification (via AuthenticatedRoute),
   * on vérifie si l'utilisateur est admin
   */
  beforeModel(transition) {
    // D'abord vérifier l'authentification (appel la méthode parent)
    super.beforeModel(transition);

    // Ensuite vérifier si admin
    if (this.auth.isAuthenticated && !this.auth.currentUser.admin) {
      console.log('⛔ Accès refusé : utilisateur non admin');
      alert('Accès réservé aux administrateurs');
      
      // Rediriger vers la page d'accueil
      this.router.transitionTo('index');
    }
  }
}