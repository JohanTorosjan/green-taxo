import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';

export default class HomeController extends Controller {
  @tracked isFrench = true;

  @action
  setLanguage(lang) {
    this.isFrench = lang === 'fr';
  }

  @action
  sendEmail() {
    // Remplacez 'contact@greentaxo.fr' par l'adresse email réelle
    const email = 'contact@greentaxo.com'; // À MODIFIER avec l'adresse réelle
    const subject = this.isFrench 
      ? 'Question concernant GreenTaxo' 
      : 'Question about GreenTaxo';
    
    const mailtoLink = `mailto:${email}?subject=${encodeURIComponent(subject)}`;
    window.location.href = mailtoLink;
  }
}