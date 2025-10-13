// app/helpers/eq.js
import { helper } from '@ember/component/helper';

export default helper(function not([a, b]) {
  return a !== b;
});
