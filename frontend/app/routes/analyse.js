// frontend/app/routes/analyse.js
import AuthenticatedRoute from './authenticated';

/**
 * Route pour la page d'analyse
 * Hérite de AuthenticatedRoute donc nécessite une connexion
 */
export default class AnalyseRoute extends AuthenticatedRoute {
  // Vous pouvez ajouter ici la logique spécifique à cette route
  // Par exemple charger des données :
  
  // async model() {
  //   return fetch('...');
  // }
}