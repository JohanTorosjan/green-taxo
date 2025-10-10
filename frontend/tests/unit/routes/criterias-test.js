import { module, test } from 'qunit';
import { setupTest } from 'frontend/tests/helpers';

module('Unit | Route | criterias', function (hooks) {
  setupTest(hooks);

  test('it exists', function (assert) {
    let route = this.owner.lookup('route:criterias');
    assert.ok(route);
  });
});
