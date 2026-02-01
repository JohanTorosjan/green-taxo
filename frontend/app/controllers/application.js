import Controller from '@ember/controller';
import { tracked } from '@glimmer/tracking';
import { action } from '@ember/object';
import { inject as service } from '@ember/service';

export default class ApplicationController extends Controller {
    @service auth;
    @service router;
    @action
    logout(){
        this.auth.logout()
    }

    @action
    goToHome(){
        this.router.transitionTo("home")
    }

    @action
    sendMeAMail(){
            const email = 'devgreentaxo@gmail.com'; // À MODIFIER avec l'adresse réelle
        const subject = 'Question about GreenTaxo';
    
        const mailtoLink = `mailto:${email}?subject=${encodeURIComponent(subject)}`;
        window.location.href = mailtoLink;
    }
    
}