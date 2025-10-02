import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';

export default class AdminDocumentsController extends Controller {
  @tracked isModalOpen = false;
  @tracked selectedFile = null;
  @tracked documentName = '';
  @tracked documentDate = '';
  @tracked documents = []; // liste des documents

  constructor() {
    super(...arguments);
    this.loadDocuments(); // charger au montage
  }

  async loadDocuments() {
    try {
      let response = await fetch("http://localhost:8000/api/documents");
      if (!response.ok) throw new Error("Erreur API");
      this.documents = await response.json();
    } catch (err) {
      console.error("Erreur chargement documents :", err);
    }
  }

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
    this.selectedFile = event.target.files[0];
    console.log("Fichier sélectionné :", this.selectedFile?.name);
  }

  @action updateName(event) {
    this.documentName = event.target.value;
  }

  @action updateDate(event) {
    this.documentDate = event.target.value;
  }

  @action async uploadFile() {
    if (!this.documentName || !this.documentDate || !this.selectedFile) {
      alert("Veuillez remplir tous les champs et sélectionner un fichier !");
      return;
    }

    let formData = new FormData();
    formData.append("name", this.documentName);
    formData.append("doc_date", this.documentDate);
    formData.append("file", this.selectedFile);

    try {
      let response = await fetch("http://localhost:8000/api/documents", {
        method: "POST",
        body: formData
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
      let data = await response.json();
      console.log("Réponse backend :", data);

      // ✅ Recharge la liste après ajout
      await this.loadDocuments();

      this.closeModal();
    } catch (err) {
      console.error("Erreur lors de l'upload :", err);
      alert("Erreur lors de l'upload du document !");
    }
  }

  @action async downloadDocument(id, name) {
  try {
    let response = await fetch(`http://localhost:8000/api/documents/${id}/download`);
    if (!response.ok) throw new Error("Erreur API téléchargement");

    let blob = await response.blob();

    // Créer un lien temporaire pour déclencher le téléchargement
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = name; // nom du fichier
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Erreur téléchargement :", err);
    alert("Impossible de télécharger le document !");
  }
}

}
