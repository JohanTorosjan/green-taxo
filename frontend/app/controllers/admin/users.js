// app/controllers/admin/users.js
import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class AdminUsersController extends Controller {
  @service auth;
  
  @tracked usersList = [];
  
  // Données du formulaire
  @tracked newUser = {
    nom: '',
    prenom: '',
    email: '',
    password: '',
    admin: false
  };
  
  @tracked editingUserId = null;
  
  // États de l'interface
  @tracked isLoading = false;
  @tracked successMessage = '';
  @tracked errorMessage = '';
  
  // ⭐ NOUVEAU : État de la modale
  @tracked isModalOpen = false;

  get isEditing() {
    return this.editingUserId !== null;
  }

  get users() {
    return this.usersList.filter(user => user.is_active);
  }

  /**
   * ⭐ NOUVEAU : Ouvrir la modale pour créer un utilisateur
   */
  @action
  openCreateModal() {
    this.resetForm();
    this.isModalOpen = true;
  }

  /**
   * ⭐ NOUVEAU : Ouvrir la modale pour modifier un utilisateur
   */
  @action
  openEditModal(user) {
    this.editingUserId = user.id;
    this.newUser = {
      nom: user.nom,
      prenom: user.prenom,
      email: user.email,
      password: '',
      admin: user.admin
    };
    this.isModalOpen = true;
  }

  /**
   * ⭐ NOUVEAU : Fermer la modale
   */
  @action
  closeModal() {
    this.isModalOpen = false;
    this.resetForm();
  }

  @action
  async handleSubmit(event) {
    event.preventDefault();
    
    this.successMessage = '';
    this.errorMessage = '';
    
    if (!this.validateForm()) {
      return;
    }
    
    this.isLoading = true;
    
    try {
      if (this.isEditing) {
        await this.updateUser();
      } else {
        await this.createUser();
      }
      
      // ⭐ CHANGEMENT : Fermer la modale après succès
      this.closeModal();
      
    } catch (error) {
      console.error('Erreur:', error);
      this.errorMessage = error.message || 'Une erreur est survenue';
    } finally {
      this.isLoading = false;
    }
  }

  async createUser() {
    const token = this.auth.token;
    
    const response = await fetch('http://localhost:8000/api/auth/register', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        nom: this.newUser.nom,
        prenom: this.newUser.prenom,
        email: this.newUser.email,
        password: this.newUser.password,
        admin: this.newUser.admin
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Erreur lors de la création de l\'utilisateur');
    }
    
    this.successMessage = `Utilisateur ${data.prenom} ${data.nom} créé avec succès !`;
    await this.refreshUsers();
    
    setTimeout(() => {
      this.successMessage = '';
    }, 5000);
  }

  async updateUser() {
    const token = this.auth.token;
    
    const updateData = {
      nom: this.newUser.nom,
      prenom: this.newUser.prenom,
      email: this.newUser.email,
      admin: this.newUser.admin
    };
    
    if (this.newUser.password && this.newUser.password.trim() !== '') {
      updateData.password = this.newUser.password;
    }
    
    const response = await fetch(`http://localhost:8000/api/users/${this.editingUserId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Erreur lors de la modification de l\'utilisateur');
    }
    
    this.successMessage = `Utilisateur ${data.prenom} ${data.nom} updated !`;
    await this.refreshUsers();
    
    setTimeout(() => {
      this.successMessage = '';
    }, 5000);
  }

  @action
  async refreshUsers() {
    try {
      const token = this.auth.token;
      
      const response = await fetch('http://localhost:8000/api/users', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const users = await response.json();
        this.usersList = users;
      }
    } catch (error) {
      console.error('Erreur lors du rechargement:', error);
    }
  }

  validateForm() {
    if (!this.newUser.nom || !this.newUser.nom.trim()) {
      this.errorMessage = 'Le nom est obligatoire';
      return false;
    }
    
    if (!this.newUser.prenom || !this.newUser.prenom.trim()) {
      this.errorMessage = 'Le prénom est obligatoire';
      return false;
    }
    
    if (!this.newUser.email || !this.newUser.email.trim()) {
      this.errorMessage = 'L\'email est obligatoire';
      return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.newUser.email)) {
      this.errorMessage = 'L\'email n\'est pas valide';
      return false;
    }
    
    if (!this.isEditing) {
      if (!this.newUser.password || this.newUser.password.length < 6) {
        this.errorMessage = 'Le mot de passe doit contenir au moins 6 caractères';
        return false;
      }
    } else {
      if (this.newUser.password && this.newUser.password.length < 6) {
        this.errorMessage = 'Le mot de passe doit contenir au moins 6 caractères';
        return false;
      }
    }
    
    return true;
  }

  @action
  resetForm() {
    this.newUser = {
      nom: '',
      prenom: '',
      email: '',
      password: '',
      admin: false
    };
    this.editingUserId = null;
    this.errorMessage = '';
  }

  @action
  cancelEdit() {
    this.closeModal();
  }


  @action
  async deleteUser(user){
    if (!confirm('Are you sure you want to delete this user ?')) {
      return;
    }
      const token = this.auth.token;
  
  const response = await fetch(`http://localhost:8000/api/users/${user.id}/deactivate`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'Erreur lors de la désactivation');
  }
  
  this.successMessage = data.message;
  await this.refreshUsers();
    
  }
}