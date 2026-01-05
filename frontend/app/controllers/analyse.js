import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class AnalyseController extends Controller {
  @tracked showModal = false;
  @tracked selectedFile = null;
  @tracked selectedFileName = '';
  @tracked documentName = '';
  @tracked documentDate = '';
  @tracked companyName = '';
  @service router;

  @service auth;

  @action
  handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) {
      return;
    }

    // Vérifier que c'est bien un PDF
    if (file.type !== 'application/pdf') {
      alert('Veuillez sélectionner uniquement des fichiers PDF.');
      event.target.value = ''; // Reset input
      return;
    }

    this.selectedFile = file;
    this.selectedFileName = file.name;

    // Pré-remplir les champs avec les infos du fichier
    this.extractFileInfo(file);

    // Ouvrir la modale
    this.showModal = true;
  }

  extractFileInfo(file) {
    // Extraire le nom du fichier sans l'extension
    const nameWithoutExtension = file.name.replace(/\.pdf$/i, '');
    this.documentName = nameWithoutExtension;

    // Utiliser la date de modification du fichier
    const fileDate = new Date(file.lastModified);
    this.documentDate = fileDate.toISOString().split('T')[0];

    // Laisser l'entreprise vide
    this.companyName = '';
  }

  @action
  updateField(fieldName, event) {
    this[fieldName] = event.target.value;
  }

  @action
  closeModal() {
    this.showModal = false;
    // Reset le file input
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
      fileInput.value = '';
    }
    this.selectedFileName = '';
  }

  @action
  stopPropagation(event) {
    event.stopPropagation();
  }

  @action
  async handleSubmit(event) {
    event.preventDefault();

    // Créer l'objet avec toutes les infos
    const documentData = {
      file: this.selectedFile,
      fileName: this.selectedFile.name,
      fileSize: this.selectedFile.size,
      fileType: this.selectedFile.type,
      documentName: this.documentName,
      documentDate: this.documentDate,
      companyName: this.companyName,
      uploadedAt: new Date().toISOString()
    };

    // Log dans la console
    console.log('Document soumis:', documentData);
    console.log('Détails du fichier:', {
      nom: documentData.fileName,
      taille: `${(documentData.fileSize / 1024).toFixed(2)} KB`,
      type: documentData.fileType
    });
    console.log('Informations extraites:', {
      nom: documentData.documentName,
      date: documentData.documentDate,
      entreprise: documentData.companyName
    });

        try {
                let formData = new FormData();
    formData.append("name", this.documentName);
    formData.append("doc_date", this.documentDate);
    formData.append("file", this.selectedFile);

      console.log("📤 Envoi du rapport...");
        const token = this.auth.token;

      let response = await fetch("http://localhost:8000/api/analysis", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`, // ← À répéter partout
        },
        body: formData
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
      let data = await response.json();
      console.log("✅ rapport créé :", data);
      this.analysis_id=data.id
    } catch (err) {
      console.error("❌ Erreur lors de l'upload :", err);
      alert("Erreur lors de l'upload du document !");
    }
    // Fermer la modale et réinitialiser
    this.showModal = false;
    this.selectedFile = null;
    this.selectedFileName = '';
    this.documentName = '';
    this.documentDate = '';
    this.companyName = '';

    // Reset le file input
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
      fileInput.value = '';
    }


    // Message de confirmation
    this.router.transitionTo('analysis', {
      queryParams: { id: this?.analysis_id },
    });    
  }
}