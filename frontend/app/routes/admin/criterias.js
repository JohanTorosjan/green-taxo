import Route from '@ember/routing/route';
import ENV from 'frontend/config/environment';

export default class CriteriasRoute extends Route {

    queryParams = {
    id: {
      refreshModel: true,
    },
  };

    async model(params) {
    try {

      const response = await fetch(
        `${ENV.APP.apiUrl}/criterias/${params.id}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        },
      );
    console.log(response)
        if (response.status===404){
            return[]
        }
      const criterias = await response.json();
      console.log(criterias)
      return criterias;
    } catch (error) {
      console.error('Erreur lors de la récupération des critères:', error);
      // Optionnel: redirection vers page d'erreur
      throw error;
    }
    }

}
