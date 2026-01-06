// app/components/modal.js
import Component from '@glimmer/component';
import { action } from '@ember/object';

export default class ModalComponent extends Component {
  @action
  handleBackdropClick(event) {
    // Fermer si on clique sur le backdrop (pas sur le contenu)
    if (event.target === event.currentTarget && this.args.onClose) {
      this.args.onClose();
    }
  }

  @action
  handleClose() {
    if (this.args.onClose) {
      this.args.onClose();
    }
  }
}