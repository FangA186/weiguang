import assert from 'node:assert/strict';
import test from 'node:test';
import { instructionUnits, previewVoiceInstruction } from '../src/lib/voiceInstruction.ts';

test('description uses remaining combined budget rather than a 30 character cap', () => {
  const style = { emotion_mode:'auto', instruction:'好'.repeat(45) };
  assert.equal(instructionUnits(previewVoiceInstruction(style)), 100);
  assert.ok(instructionUnits(previewVoiceInstruction({...style, traits:['磁性']})) > 100);
  assert.equal(instructionUnits('a好🙂'), 5);
});

test('manual emotion, dimensions, and reset match composed request', () => {
  const style = {emotion_mode:'manual', emotion:'gentle', presentation:'男性', age_feel:'青年', traits:['磁性','甜美'], instruction:'自然'};
  assert.equal(previewVoiceInstruction(style), '温柔，男性，青年，磁性，甜美，自然');
  assert.equal(previewVoiceInstruction({...style, use_defaults:true}), '');
});
