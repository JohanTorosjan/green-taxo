// frontend/app/helpers/includes.js
import { helper } from '@ember/component/helper';

export function includes([array, value]) {
  if (!array || !Array.isArray(array)) {
    return false;
  }
  return array.includes(value);
}

export default helper(includes);