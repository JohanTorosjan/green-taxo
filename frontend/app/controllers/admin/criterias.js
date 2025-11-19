import Controller from '@ember/controller';
import { action } from '@ember/object';
import { tracked } from '@glimmer/tracking';

export default class CriteriasController extends Controller {
  @tracked showModal = false;
  @tracked isEditMode = false;
  @tracked isLoading = false;
  @tracked successMessage = null;
  @tracked errorMessage = null;
  @tracked currentEditingId = null;

  @tracked formData = {
    nom: '',
    description: '',
    coefficient: '',
    dataString: '',
    dataError: null,
  };

  API_URL = 'http://195.220.87.129:8000';

  get criterias() {
    console.log('[Criterias] Getter criterias - model:', this.model);
    return Array.isArray(this.model) ? this.model : [];
  }

  @action
  openCreateModal() {
    console.log('[Criterias] Ouverture du modal de création');
    this.resetFormData();
    this.isEditMode = false;
    this.showModal = true;
  }

  @action
  openEditModal(criteria) {
    console.log('[Criterias] Ouverture du modal de modification pour:', criteria);
    this.formData = {
      nom: criteria.nom,
      description: criteria.description,
      coefficient: criteria.coefficient,
      dataString: criteria.data ? JSON.stringify(criteria.data, null, 2) : '',
      dataError: null,
    };
    this.currentEditingId = criteria.id;
    this.isEditMode = true;
    this.showModal = true;
  }

  @action
  closeModal() {
    console.log('[Criterias] Fermeture du modal');
    this.showModal = false;
    this.resetFormData();
  }

  @action
  resetFormData() {
    this.formData = {
      nom: '',
      description: '',
      coefficient: '',
      dataString: '',
      dataError: null,
    };
    this.currentEditingId = null;
    this.isEditMode = false;
  }

  @action
  updateFormData(field, event) {
    console.log(`[Criterias] Mise à jour du champ: ${field}`, event.target.value);
    if (field === 'coefficient') {
      this.formData.coefficient = parseInt(event.target.value) || '';
    } else {
      this.formData[field] = event.target.value;
    }

    if (field === 'dataString') {
      this.validateJSON();
    }
  }

  @action
  validateJSON() {
    if (!this.formData.dataString.trim()) {
      this.formData.dataError = null;
      return true;
    }

    try {
      JSON.parse(this.formData.dataString);
      this.formData.dataError = null;
      return true;
    } catch (error) {
      this.formData.dataError = `JSON invalide: ${error.message}`;
      return false;
    }
  }

  @action
  async saveCriteria(event) {
    event.preventDefault();
    console.log('[Criterias] Tentative de sauvegarde:', this.formData);

    if (!this.formData.nom || this.formData.coefficient === '') {
      this.errorMessage = 'Le nom et le coefficient sont obligatoires';
      console.error('[Criterias] Erreur validation:', this.errorMessage);
      return;
    }

    if (!this.validateJSON()) {
      console.error('[Criterias] Erreur JSON:', this.formData.dataError);
      return;
    }

    const documentId = this.queryParams.id || 1; // Récupère l'ID des query params
    const payload = {
      nom: this.formData.nom,
      description: this.formData.description,
      coefficient: this.formData.coefficient,
      data: this.formData.dataString ? JSON.parse(this.formData.dataString) : null,
      document_id: documentId,
    };

    try {
      let response;
      const url = this.isEditMode
        ? `${this.API_URL}/criterias/${this.currentEditingId}`
        : `${this.API_URL}/criterias`;

      const method = this.isEditMode ? 'PUT' : 'POST';

      console.log(`[Criterias] Envoi ${method} vers:`, url);
      console.log('[Criterias] Payload:', payload);

      response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      console.log(`[Criterias] Réponse ${method}:`, response.status, response);

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}`);
      }

      const result = await response.json();
      console.log('[Criterias] Résultat de la sauvegarde:', result);

      this.successMessage = this.isEditMode
        ? 'Critère modifié avec succès!'
        : 'Critère créé avec succès!';

      // Rechargement de la liste
      await this.reloadCriterias();
      this.closeModal();

      // Masquer le message après 3 secondes
      setTimeout(() => {
        this.successMessage = null;
      }, 3000);
    } catch (error) {
      console.error('[Criterias] Erreur lors de la sauvegarde:', error);
      this.errorMessage = `Erreur lors de la sauvegarde: ${error.message}`;
      setTimeout(() => {
        this.errorMessage = null;
      }, 5000);
    }
  }

  @action
  async deleteCriteria(id) {
    console.log('[Criterias] Tentative de suppression de l\'ID:', id);

    if (!confirm('Êtes-vous sûr de vouloir supprimer ce critère?')) {
      console.log('[Criterias] Suppression annulée par l\'utilisateur');
      return;
    }

    try {
      const url = `${this.API_URL}/criterias/${id}`;
      console.log('[Criterias] Envoi DELETE vers:', url);

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('[Criterias] Réponse DELETE:', response.status, response);

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}`);
      }

      console.log('[Criterias] Critère supprimé avec succès');
      this.successMessage = 'Critère supprimé avec succès!';

      // Rechargement de la liste
      await this.reloadCriterias();

      setTimeout(() => {
        this.successMessage = null;
      }, 3000);
    } catch (error) {
      console.error('[Criterias] Erreur lors de la suppression:', error);
      this.errorMessage = `Erreur lors de la suppression: ${error.message}`;
      setTimeout(() => {
        this.errorMessage = null;
      }, 5000);
    }
  }

  @action
  async reloadCriterias() {
    console.log('[Criterias] Rechargement de la liste');
    this.isLoading = true;
    try {
      const documentId = this.queryParams.id || 1;
      const url = `${this.API_URL}/criterias/${documentId}`;
      console.log('[Criterias] Fetch GET vers:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('[Criterias] Réponse GET:', response.status, response);

      if (response.status === 404) {
        this.model = [];
        return;
      }

      const data = await response.json();
      console.log('[Criterias] Données reçues:', data);
      this.model = Array.isArray(data) ? data : [data];
    } catch (error) {
      console.error('[Criterias] Erreur lors du rechargement:', error);
    } finally {
      this.isLoading = false;
    }
  }

  @action
  stopPropagation(event) {
    event.stopPropagation();
  }

  @action
  stringifyData(data) {
    if (!data) return '';
    return JSON.stringify(data, null, 2);
  }
}