import assert from 'node:assert/strict';
import { createHoloStoryScene } from '../src/components/createHoloStoryScene.js';

// No GPU needed: validate animation/material state; visual rendering is checked in Chrome.
globalThis.document = { createElement: () => ({ getContext: () => new Proxy({ measureText: text => ({ width: text.length * 30 }) }, { get: (obj, key) => obj[key] ?? (() => {}) }) }) };
const card = createHoloStoryScene({ title: '测试', author: '作者', tag: '示例', text: '背面正文' });
const state = { aimX: -.1, aimY: -.3, flipped: false, auto: false, depth: .65, gloss: .65, finish: 'pearl' };
card.update(1 / 60, state, true, -.4);
const foil = card.scene.children.find(node => node.isGroup).children.find(node => node.material?.uniforms?.pearl);
assert.equal(foil.material.uniforms.pearl.value, 1);
const leftView = foil.material.uniforms.view.value.clone();
card.update(1 / 60, state, true, .4);
assert(leftView.distanceTo(foil.material.uniforms.view.value) > .5);
assert.equal(foil.material.uniforms.sweep, undefined);
assert.equal(card.scene.children.find(node => node.isGroup).children.filter(node => node.material?.isShaderMaterial).length, 1);
state.finish = 'theme'; card.update(1 / 60, state, false, 0);
assert.equal(foil.material.uniforms.pearl.value, 0);
assert.equal(foil.material.uniforms.gold.value, 0);
state.finish = 'gold'; card.update(1 / 60, state, false, 0);
assert.equal(foil.material.uniforms.gold.value, 1);
state.gloss = 0; card.update(1 / 60, state, false, 0);
assert.equal(foil.material.uniforms.gloss.value, 0);
card.dispose();
console.log('Holo material state checks passed');
