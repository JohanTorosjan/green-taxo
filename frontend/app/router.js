import EmberRouter from '@ember/routing/router';
import config from 'frontend/config/environment';

export default class Router extends EmberRouter {
  location = config.locationType;
  rootURL = config.rootURL;
}

Router.map(function () {
  this.route('admin', function () {
    this.route('dashboard');
    this.route('documents');
  });
  this.route('criterias');
});
