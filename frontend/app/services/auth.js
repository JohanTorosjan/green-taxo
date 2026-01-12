// frontend/app/services/auth.js
import Service from '@ember/service';
import { tracked } from '@glimmer/tracking';
import { inject as service } from '@ember/service';
import ENV from 'frontend/config/environment';

export default class AuthService extends Service {
  @service router;

  // État réactif de l'authentification
  @tracked token = null;
  @tracked currentUser = null;
  @tracked isAuthenticated = false;

  constructor() {
    super(...arguments);
    // Au démarrage, vérifier si un token existe déjà dans sessionStorage
    this.loadStoredAuth();
  }

  /**
   * Charge le token et l'utilisateur depuis sessionStorage au démarrage
   */
  loadStoredAuth() {
    const storedToken = sessionStorage.getItem('auth_token');
    const storedUser = sessionStorage.getItem('current_user');

    if (storedToken && storedUser) {
      this.token = storedToken;
      this.currentUser = JSON.parse(storedUser);
      this.isAuthenticated = true;
      console.log('✅ Utilisateur connecté:', this.currentUser.email);
    }
  }

  /**
   * Connecte un utilisateur
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<object>} Les données de l'utilisateur
   */
  async login(email, password) {
    try {
      const response = await fetch(`${ENV.APP.apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur de connexion');
      }

      const data = await response.json();

      // Stocker le token et l'utilisateur
      this.token = data.access_token;
      this.currentUser = data.user;
      this.isAuthenticated = true;

      // Sauvegarder dans sessionStorage pour persister entre les rechargements
      sessionStorage.setItem('auth_token', data.access_token);
      sessionStorage.setItem('current_user', JSON.stringify(data.user));

      console.log('✅ Connexion réussie:', this.currentUser.email);

      // Rediriger vers la page qu'il voulait visiter (si sauvegardée)
      const redirectTo = sessionStorage.getItem('redirectAfterLogin');
      if (redirectTo && redirectTo !== 'login') {
        sessionStorage.removeItem('redirectAfterLogin');
        this.router.transitionTo(redirectTo);
      }
      return data.user;
    } catch (error) {
      console.error('❌ Erreur de connexion:', error);
      throw error;
    }
  }

  /**
   * Déconnecte l'utilisateur
   */
  logout() {
    this.token = null;
    this.currentUser = null;
    this.isAuthenticated = false;

    // Supprimer du sessionStorage
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('current_user');

    console.log('👋 Déconnexion réussie');

    // Rediriger vers la page de login
    this.router.transitionTo('login');
  }

  /**
   * Récupère le token pour les requêtes API
   * @returns {string|null}
   */
  getToken() {
    return this.token;
  }

  /**
   * Récupère les headers d'authentification pour fetch
   * @returns {object}
   */
  getAuthHeaders() {
    if (this.token) {
      return {
        'Authorization': `Bearer ${this.token}`,
      };
    }
    return {};
  }
}