import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class AdminDocumentsController extends Controller {
  @tracked isModalOpen = false;
  @tracked isDeleteModalOpen = false;
  @tracked selectedFile = null;
  @tracked documentName = '';
  @tracked documentDate = '';
  @tracked documents = [];
  @tracked documentToDelete = null;
  @tracked skipAi = false
  
  @service router;
  pollingIntervals = new Map();

  constructor() {
    super(...arguments);
    this.loadDocuments();
  }

  willDestroy() {
    super.willDestroy(...arguments);
    this.pollingIntervals.forEach(interval => clearInterval(interval));
    this.pollingIntervals.clear();
  }

  async loadDocuments() {
    try {
      console.log("📥 Chargement des documents...");  
      let response = await fetch("http://localhost:8000/api/documents");
      if (!response.ok) throw new Error("Erreur API");
      this.documents = await response.json();
      console.log("✅ Documents chargés:", this.documents);
      
      this.documents.forEach(doc => {
        if (doc.analysis_status === 'pending' || doc.analysis_status === 'processing') {
          this.startPolling(doc.id);
        }
      });
    } catch (err) {
      console.error("❌ Erreur chargement documents :", err);
    }
  }

  startPolling(docId) {
    if (this.pollingIntervals.has(docId)) {
      return;
    }
    console.log(`⏱️ Démarrage du polling pour le document ${docId}`);
    const intervalId = setInterval(async () => {
      await this.checkAnalysisStatus(docId);
    }, 3000);

    this.pollingIntervals.set(docId, intervalId);
  }

  stopPolling(docId) {
    const intervalId = this.pollingIntervals.get(docId);
    if (intervalId) {
      clearInterval(intervalId);
      this.pollingIntervals.delete(docId);
      console.log(`⏹️ Arrêt du polling pour le document ${docId}`);
    }
    
    if(this.documents.find(d => d.id === docId).analysis_status==="completed"){
      this.documents = this.documents.map(doc => {
        if (doc.id === docId) {
          return { ...doc, used: true };
        }
        return doc;
      });
    }
  }

  async checkAnalysisStatus(docId) {
    try {
      let response = await fetch(`http://localhost:8000/api/documents/${docId}/analysis`);
      if (!response.ok) throw new Error("Erreur API analyse");
      
      let analysisData = await response.json();
      console.log(`🔄 Statut d'analyse pour ${docId}:`, analysisData);
      
      this.documents = this.documents.map(doc => {
        if (doc.id === docId) {
          return { ...doc, analysis_status: analysisData.analysis_status };
        }
        return doc;
      });

      if (analysisData.analysis_status === 'completed') {
        this.stopPolling(docId);
        console.log(`✅ Analyse du document ${docId} terminée !`);
      } else if (analysisData.analysis_status !== 'processing') {
        this.stopPolling(docId);
        console.error(`❌ Statut d'analyse inconnu pour le document ${docId}: ${analysisData.analysis_status}`);
      }
    } catch (err) {
      console.error(`❌ Erreur lors de la vérification du statut d'analyse pour ${docId}:`, err);
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
    this.documentName = this.selectedFile?.name
    const fileDate = new Date(this.selectedFile?.lastModified);
    this.documentDate = fileDate.toISOString().split('T')[0];
    console.log("📎 Fichier sélectionné :", this.selectedFile);
  }

  @action updateName(event) {
    this.documentName = event.target.value;
  }

  @action updateDate(event) {
    this.documentDate = event.target.value;
  }

  @action toogleSkipAi(){
  if (this.skipAi){
    this.skipAi=false
  }
  else{this.skipAi=true}
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
    console.log(this.skipAi)
    if(this.skipAi){
      try{
          let response = await fetch("http://localhost:8000/api/documents/skipAi", {
              method: "POST",
              body: formData
            });
          if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
          let data = await response.json();
          console.log("✅ Document créé :", data);
          await this.loadDocuments();
          this.closeModal();
          return
      }
      catch(err){
        alert("Error");
      }
    }
    try {
      console.log("📤 Envoi du document...");
      let response = await fetch("http://localhost:8000/api/documents", {
        method: "POST",
        body: formData
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
      let data = await response.json();
      console.log("✅ Document créé :", data);

      await this.loadDocuments();
      this.closeModal();
    } catch (err) {
      console.error("❌ Erreur lors de l'upload :", err);
      alert("Erreur lors de l'upload du document !");
    }
  }

  @action async downloadDocument(id, name) {
    try {
      console.log(`📥 Téléchargement du document ${id}...`);
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
      console.log("✅ Document téléchargé :", name);
    } catch (err) {
      console.error("❌ Erreur téléchargement :", err);
      alert("Impossible de télécharger le document !");
    }
  }

  @action openAnalysis(doc) {
    console.log("📊 Ouverture de l'analyse pour:", doc);
    this.router.transitionTo('admin.criterias', {
      queryParams: { id: doc.id },
    });
  }

  @action openDeleteModal(doc) {
    console.log("🗑️ Préparation de la suppression du document:", doc.id);
    this.documentToDelete = doc;
    this.isDeleteModalOpen = true;
  }

  @action closeDeleteModal() {
    this.isDeleteModalOpen = false;
    this.documentToDelete = null;
  }

  @action async deleteDocument() {
    if (!this.documentToDelete) return;
    
    try {
      console.log(`🗑️ Suppression du document ${this.documentToDelete.id}...`);
      let response = await fetch(`http://localhost:8000/api/documents/${this.documentToDelete.id}`, {
        method: "DELETE"
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
      console.log("✅ Document supprimé :", this.documentToDelete.id);

      this.closeDeleteModal();
      await this.loadDocuments();
    } catch (err) {
      console.error("❌ Erreur lors de la suppression :", err);
      alert("Erreur lors de la suppression du document !");
    }
  }

  @action async toggleDocumentUsed(doc) {
    try {
      console.log(`🔄 Mise à jour du statut 'used' pour le document ${doc.id}...`);
      let response = await fetch(`http://localhost:8000/api/documents/${doc.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ used: !doc.used })
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
      let updatedDoc = await response.json();
      console.log("✅ Document mis à jour :", updatedDoc);

      await this.loadDocuments();
    } catch (err) {
      console.error("❌ Erreur lors de la mise à jour :", err);
      alert("Erreur lors de la mise à jour du document !");
    }
  }

  @action stopPropagation(event) {
    event.stopPropagation();
  }

  @action openDetails(doc){
    if(doc.analysis_status==='completed' || doc.analysis_status==='skipped'){
      this.router.transitionTo('admin.criterias', {
        queryParams: { id: doc.id },
      });
    }
    else{return}

  }
}