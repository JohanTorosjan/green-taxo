import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';

export default class AdminDocumentsController extends Controller {
  @tracked isModalOpen = false;
  @tracked selectedFile = null;
  @tracked documentName = '';
  @tracked documentDate = '';

  @action openModal() {
    this.isModalOpen = true;
  }

  @action closeModal() {
    this.isModalOpen = false;
    this.selectedFile = null;
    this.documentName = '';
    this.documentDate = '';
  }

  @action handleFileChange(event) {
    let file = event.target.files[0];
    this.selectedFile = file;
    console.log("Fichier sélectionné :", file?.name);
  }

  @action updateName(event) {
    this.documentName = event.target.value;
  }

  @action updateDate(event) {
    this.documentDate = event.target.value;
  }

  @action uploadFile() {
    if (!this.documentName || !this.documentDate || !this.selectedFile) {
      alert("Veuillez remplir tous les champs et sélectionner un fichier !");
      return;
    }

    // Tu pourras envoyer ça à ton backend
    console.log("Nom :", this.documentName);
    console.log("Date :", this.documentDate);
    console.log("Fichier :", this.selectedFile);

    // Fermer la modale après import
    this.closeModal();
  }
}
