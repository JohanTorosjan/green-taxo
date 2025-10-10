import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class AdminDocumentsController extends Controller {
  @tracked isModalOpen = false;
  @tracked selectedFile = null;
  @tracked documentName = '';
  @tracked documentDate = '';
  @tracked documents = [];
  
  @service router;
  // Map pour stocker les intervalles de polling par document
  pollingIntervals = new Map();

  constructor() {
    super(...arguments);
    this.loadDocuments();
  }

  willDestroy() {
    super.willDestroy(...arguments);
    // Nettoyer tous les intervalles en cours
    this.pollingIntervals.forEach(interval => clearInterval(interval));
    this.pollingIntervals.clear();
  }

  async loadDocuments() {
    try {
      let response = await fetch("http://localhost:8000/api/documents");
      if (!response.ok) throw new Error("Erreur API");
      this.documents = await response.json();
      console.log(this.documents);
      
      // Démarrer le polling pour les documents en attente
      this.documents.forEach(doc => {
        if (doc.analysis_status === 'pending' ||doc.analysis_status === 'processing' ) {
          console.log("ICIIIIIIII")
          this.startPolling(doc.id);
        }
      });
    } catch (err) {
      console.error("Erreur chargement documents :", err);
    }
  }

  startPolling(docId) {
    // Éviter de créer plusieurs intervalles pour le même document
    if (this.pollingIntervals.has(docId)) {
      return;
    }
    console.log("laaaaaa")
    const intervalId = setInterval(async () => {
      await this.checkAnalysisStatus(docId);
    }, 3000); // Vérifier toutes les 3 secondes

    this.pollingIntervals.set(docId, intervalId);
  }

  stopPolling(docId) {
    const intervalId = this.pollingIntervals.get(docId);
    if (intervalId) {
      clearInterval(intervalId);
      this.pollingIntervals.delete(docId);
    }
  }

  async checkAnalysisStatus(docId) {
    try {
      let response = await fetch(`http://localhost:8000/api/documents/${docId}/analysis`);
      if (!response.ok) throw new Error("Erreur API analyse");
      
      let analysisData = await response.json();
      console.log(analysisData)
      // Mettre à jour le document dans la liste
      this.documents = this.documents.map(doc => {
        if (doc.id === docId) {
          return { ...doc, analysis_status: analysisData.analysis_status };
        }
        return doc;
      });

      // Si l'analyse est terminée, arrêter le polling
      if (analysisData.analysis_status === 'completed') {
        this.stopPolling(docId);
        console.log(`Analyse du document ${docId} terminée !`);
      } else if (analysisData.analysis_status !== 'processing') {
        // Si le statut n'est ni 'completed' ni 'pending', c'est une erreur
        this.stopPolling(docId);
        console.error(`Statut d'analyse inconnu pour le document ${docId}: ${analysisData.analysis_status}`);
      }
    } catch (err) {
      console.error(`Erreur lors de la vérification du statut d'analyse pour ${docId}:`, err);
      this.stopPolling(docId);
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
      let url = window.URL.createObjectURL(blob);
      let a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Erreur téléchargement :", err);
      alert("Impossible de télécharger le document !");
    }
  }

  @action openAnalysis(doc) {
    console.log("Ouverture de l'analyse pour:", doc);
    this.router.transitionTo('criterias', {
      queryParams: { id: doc.id },
    });
    // Ici vous pourrez implémenter l'ouverture d'une vue détaillée de l'analyse
  }
}