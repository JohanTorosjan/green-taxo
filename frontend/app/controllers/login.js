// frontend/app/controllers/login.js
import Controller from '@ember/controller';
import { inject as service } from '@ember/service';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';

export default class LoginController extends Controller {
  @service auth;
  @service router;

  // Champs du formulaire (liés aux inputs)
  @tracked email = '';
  @tracked password = '';

  // État de l'interface
  @tracked isLoading = false;
  @tracked errorMessage = null;

  /**
   * Action appelée quand on soumet le formulaire
   */
  @action
  async handleLogin(event) {
    event.preventDefault(); // Empêche le rechargement de la page

    // Réinitialiser les erreurs
    this.errorMessage = null;

    // Validation basique
    if (!this.email || !this.password) {
      this.errorMessage = 'Veuillez remplir tous les champs';
      return;
    }

    // Afficher le loader
    this.isLoading = true;

    try {
      // Appeler le service d'authentification
      await this.auth.login(this.email, this.password);

      // Le service gère la redirection automatiquement
      // Soit vers la page sauvegardée, soit vers l'accueil
      const redirectTo = sessionStorage.getItem('redirectAfterLogin');
      if (!redirectTo || redirectTo === 'login') {
        console.log('✅ Connexion réussie, redirection vers accueil...');
        this.router.transitionTo('analyse');
      }
      // Sinon le service.login() a déjà redirigé

    } catch (error) {
      // Afficher l'erreur à l'utilisateur
      console.error('❌ Erreur:', error);
      this.errorMessage = error.message || 'Wrong Email or Password';
    } finally {
      // Cacher le loader
      this.isLoading = false;
    }
  }

  /**
   * Action pour mettre à jour l'email
   */
  @action
  updateEmail(event) {
    this.email = event.target.value;
  }

  /**
   * Action pour mettre à jour le mot de passe
   */
  @action
  updatePassword(event) {
    this.password = event.target.value;
  }
}