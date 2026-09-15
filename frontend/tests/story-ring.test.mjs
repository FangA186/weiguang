import assert from 'node:assert/strict';
import { ringPose, ringRadius, frontIndex } from '../src/components/storyRingLayout.js';
const count=6, step=Math.PI*2/count;
for(let i=0;i<count;i++){
  const p=ringPose(i,count), next=ringPose((i+1)%count,count);
  assert(Math.abs(Math.hypot(p.x,p.z)-ringRadius)<1e-10);
  assert(Math.abs(Math.hypot(next.x-p.x,next.z-p.z)-2*ringRadius*Math.sin(step/2))<1e-10);
  assert.equal(frontIndex(-p.angle,count),i);
  assert.equal(frontIndex(-p.angle+Math.PI*4,count),i);
}
console.log('Ring radius, spacing and wrapped selection checks passed');
