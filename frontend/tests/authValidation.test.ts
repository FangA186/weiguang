import assert from 'node:assert/strict';
import test from 'node:test';
import {emailError,passwordChecks} from '../src/lib/authValidation.ts';

test('registration email and password rules match the form contract',()=>{
  assert.ok(emailError('a@b'));
  assert.ok(emailError('a..b@example.com'));
  assert.equal(emailError('user+tag@example.com'),'');
  assert.deepEqual(passwordChecks('abcdefghij').filter(x=>!x.ok).map(x=>x.label),['包含数字','包含特殊字符']);
  assert.ok(passwordChecks('Safe-pass9').every(x=>x.ok));
});
