<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import portrait from '../../../marketing_assets/2026-08-24/04-lifestyle-v2.png';
import spirit from '../../../marketing_assets/2026-09-08/holo-card-experiment/weiguang-subject-transparent.png';
import { ringPose, ringRadius, frontIndex } from './storyRingLayout.js';
import { storyCardPalettes } from './storyCardPalettes.js';
// Explicit presentation fixtures; replace with approved public stories when the API is implemented.
const fixtures = [
  { id: 1, title: '把傍晚，慢慢还给自己', author: '小禾', tag: '重新出发', image: portrait, alt: '夕阳下坐在窗边的女孩，示例插画', text: '搬来这座城市的第一个月，最怕下班后开门的那一刻。后来我开始把一天里的小事说出来，今天的晚霞、路边的小猫，还有那碗终于没煮糊的面。日子好像又有了声音。' },
  { id: 2, title: '有些话，终于可以说完', author: '阿远', tag: '写给昨天', text: '以前总觉得，长大就是把所有的事放在心里。那天夜里，我说了很多没有头绪的话。没有急着得到答案，只是说完以后，心里空出了一点地方，能装下明天。' },
  { id: 3, title: '为自己留一束微光', author: '星野', tag: '深夜来信', image: spirit, transparent: true, alt: '漂浮的星光精灵，示例插画', text: '我给那些说不清的情绪画了一个小小的样子。它像一束光，提醒我：今天已经很努力了，可以先休息，明天再慢慢往前走。' },
  { id: 4, title: '那碗汤的味道，我还记得', author: '木木', tag: '关于想念', text: '照着记忆试着做了一次番茄汤，盐还是放多了。说起这件事时，忽然想起以前厨房里的笑声。想念没有消失，但我终于能带着它，好好吃一顿饭。' },
  { id: 5, title: '窗外的光，又亮了一些', author: '小满', tag: '平凡的一天', image: portrait, alt: '窗边温暖的日常，示例插画', text: '周末没有安排，也没再责怪自己无所事事。开窗，浇花，给朋友回一条消息。原来重新开始，可以只是一件很小很小的事。' },
  { id: 6, title: '不必每一天都很勇敢', author: '南枝', tag: '给此刻的你', text: '今天没能完成所有计划，但按时吃了饭，散了十分钟步。把这些告诉微光的时候，我也像是终于对自己说了一句：这样也很好。' },
];

const stories = [fixtures[2], fixtures[1], fixtures[0], ...fixtures.slice(3)];
const viewport = ref(null), active = ref(0), paused = ref(true), selected = ref(null), dialog = ref(null), ready = ref(false);
const state = reactive(stories.map(() => ({ aimX: 0, aimY: 0, flipped: false, auto: false, depth: .65, gloss: .65, finish: 'pearl' })));
const current = computed(() => state[active.value]);
watch(selected, value => { if (value) dialog.value?.showModal(); }, { flush: 'post' });
const scenes = [], textures = new Map();
const motion = matchMedia('(prefers-reduced-motion: reduce)');
let renderer, resizeObserver, visibilityObserver, themeObserver, dead=false, visible=false, hovered=false, focused=false, pointer=null, last=0;
let ringScene, ring, ringCamera, raycaster, pointerPoint, targetAngle=0, angle=0;
const increment=Math.PI*2/stories.length;
function applyTheme() {
  const palette=storyCardPalettes[document.documentElement.dataset.theme] || storyCardPalettes['weiguang-original'];
  scenes.forEach(scene=>scene.setTheme(palette));
}
function reset() { paused.value=true;targetAngle=-active.value*increment;Object.assign(current.value,{aimX:0,aimY:0,flipped:false,auto:false}); }
function down(e) {
  if(e.button!==0 || !ready.value)return;
  paused.value=true;pointer={id:e.pointerId,x:e.clientX,startX:e.clientX,startY:e.clientY};
  e.currentTarget.setPointerCapture(e.pointerId);
}
function move(e) {
  if(!pointer || pointer.id!==e.pointerId)return;
  targetAngle+=(e.clientX-pointer.x)*.008;pointer.x=e.clientX;
}
function selectAt(e) {
  const rect=viewport.value.getBoundingClientRect();
  pointerPoint.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
  raycaster.setFromCamera(pointerPoint,ringCamera);
  const hit=raycaster.intersectObjects(ring.children,true)[0];
  let node=hit?.object;
  while(node && node.userData.storyIndex===undefined)node=node.parent;
  if(!node)return;
  const index=node.userData.storyIndex;
  const desired=-index*increment;
  targetAngle=angle+Math.atan2(Math.sin(desired-angle),Math.cos(desired-angle));
  active.value=index;
}
function up(e) {
  if(pointer && Math.hypot(e.clientX-pointer.startX,e.clientY-pointer.startY)<6)selectAt(e);
  pointer=null;
}
function keyboard(e) {
  if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}
}
function step(direction) {paused.value=true;targetAngle=-Math.round(-targetAngle/increment)*increment-direction*increment;}
function sync(){renderer?.setAnimationLoop(visible&&!document.hidden?frame:null);last=0;}
function frame(time) {
  if(!ready.value)return;
  const dt=last && time>last?Math.min((time-last)/1000,.05):0;last=time;
  if(!paused.value&&!hovered&&!focused&&!pointer&&!selected.value&&!motion.matches)targetAngle-=dt*.18;
  angle+= (targetAngle-angle)*(motion.matches?1:1-Math.exp(-dt*10));
  ring.rotation.y=angle;
  active.value=frontIndex(angle,stories.length);
  scenes.forEach((view,index)=>view.update(dt,state[index],motion.matches,0,ringCamera));
  renderer.render(ringScene,ringCamera);
}
onMounted(async () => {
  try {
    const [T, { createHoloStoryScene }] = await Promise.all([import('three'), import('./createHoloStoryScene.js')]);
    if (dead) return;
    renderer = new T.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    renderer.domElement.className='story-3d-canvas'; renderer.domElement.setAttribute('aria-hidden','true');
    viewport.value.appendChild(renderer.domElement);
    renderer.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); ready.value=false; renderer.setAnimationLoop(null); });
    await Promise.all([...new Set(stories.map(s=>s.image).filter(Boolean))].map(async url => {
      try { const texture = await new T.TextureLoader().loadAsync(url); if(dead){texture.dispose();return;} texture.colorSpace=T.SRGBColorSpace; textures.set(url,texture); } catch { /* A failed image becomes a text card. */ }
    }));
    if (dead) return;
    for (const story of stories) scenes.push(createHoloStoryScene(story,textures.get(story.image)));
    ringScene=new T.Scene();ring=new T.Group();ringScene.add(ring);
    ringCamera=new T.PerspectiveCamera(34,1,.1,100);
    raycaster=new T.Raycaster();pointerPoint=new T.Vector2();
    scenes[0].scene.children.filter(node=>node.isLight).forEach(light=>ringScene.add(light.clone()));
    scenes.forEach((view,index)=>{const pose=ringPose(index,stories.length);const slot=new T.Group();slot.position.set(pose.x,0,pose.z);slot.rotation.y=pose.angle;slot.userData.storyIndex=index;slot.add(view.root);ring.add(slot);});
    applyTheme();
    themeObserver=new MutationObserver(applyTheme);themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
    ready.value=true;
    resizeObserver = new ResizeObserver(() => {
      const el=viewport.value;ringCamera.aspect=el.clientWidth/el.clientHeight;
      const distance=Math.max(16,(ringRadius+2.3)/(Math.tan(17*Math.PI/180)*ringCamera.aspect));
      ringCamera.position.set(0,distance*.30,distance);ringCamera.lookAt(0,0,0);ringCamera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth,el.clientHeight);frame(0);
    });
    resizeObserver.observe(viewport.value);
    visibilityObserver = new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();});
    visibilityObserver.observe(viewport.value); document.addEventListener('visibilitychange',sync);
  } catch { ready.value=false; }
});
onBeforeUnmount(()=>{
  dead=true; themeObserver?.disconnect(); resizeObserver?.disconnect(); visibilityObserver?.disconnect(); document.removeEventListener('visibilitychange',sync);
  renderer?.setAnimationLoop(null); scenes.forEach(s=>s.dispose()); textures.forEach(t=>t.dispose()); renderer?.dispose(); renderer?.domElement.remove();
});
</script>

<template>
  <div class="story-gallery">
    <div class="story-heading"><div><span class="eyebrow">STORIES WE KEEP</span><h2>每一个故事，都有自己的光</h2><p>一些想念，一些日常，一些重新开始的时刻。</p></div>
    <!-- <span class="sample-badge">示例故事 · 非真实投稿</span> -->
    </div>
    <div class="story-stage" :class="{ready}">
      <div ref="viewport" class="story-ring" role="group" tabindex="0" :aria-label="'故事圆环，拖动或左右方向键旋转，回车阅读全文。当前：'+stories[active].title" @pointerenter="hovered=true" @pointerleave="hovered=false" @focusin="focused=true" @focusout="focused=false" @pointerdown="down" @pointermove="move" @pointerup="up" @pointercancel="pointer=null" @lostpointercapture="pointer=null" @keydown="keyboard" @keydown.enter="selected=stories[active]" @dblclick="selected=stories[active]">
        <div v-if="!ready" class="story-fallback"><p>{{stories[active].title}}<br/>{{stories[active].text}}</p></div>
      </div>
      <div class="ring-pagination" aria-label="选择故事"><button v-for="(story,index) in stories" :key="story.id" type="button" :aria-label="story.title" :aria-pressed="active===index" @click="paused=true;targetAngle=angle+Math.atan2(Math.sin(-index*increment-angle),Math.cos(-index*increment-angle))"></button></div>
    </div>
    <div class="story-controls">
      <div class="story-control-title"><div class="story-buttons"><button type="button" aria-label="上一张故事" @click="step(-1)">←</button><button type="button" :aria-pressed="paused" @click="paused=!paused">{{paused?'旋转圆环':'暂停圆环'}}</button><button type="button" aria-label="下一张故事" @click="step(1)">→</button></div></div>
      <div class="material-controls"><div class="story-buttons"><button type="button" @click="current.flipped=!current.flipped">{{current.flipped?'查看正面':'翻到背面'}}</button><button type="button" :aria-pressed="current.auto" @click="current.auto=!current.auto">{{current.auto?'停止转动':'自动转动'}}</button><button type="button" @click="reset">复位</button></div><label>材质<select v-model="current.finish"><option value="theme">主题配色</option><option value="pearl">珍珠银</option><option value="gold">烫金</option></select></label><label>层次<input v-model.number="current.depth" type="range" min="0" max="1.5" step="0.01"/><output>{{Math.round(current.depth*100)}}%</output></label><label>光泽<input v-model.number="current.gloss" type="range" min="0" max="1" step="0.01"/><output>{{Math.round(current.gloss*100)}}%</output></label></div>
    </div>
    <dialog ref="dialog" v-if="selected" class="story-dialog" aria-labelledby="story-title" @cancel.prevent="selected=null"><div><button class="story-close" type="button" @click="selected=null" autofocus>关闭 ×</button><span class="eyebrow">示例故事 · {{selected.author}}</span><h2 id="story-title">{{selected.title}}</h2><img v-if="selected.image" :src="selected.image" :alt="selected.alt"/><p>{{selected.text}}</p></div></dialog>
  </div>
</template>
<style scoped>
.story-gallery{width:100%;color:var(--text);padding:0 4px}.story-heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:24px}.eyebrow{font:10px/1.5 sans-serif;letter-spacing:2px;color:var(--text-dim)}.story-heading h2{font:normal clamp(22px,3vw,30px)/1.5 var(--serif);margin:10px 0}.story-heading p{font-size:12px;color:var(--text-mid);margin:0}.sample-badge{font-size:10px;color:var(--text-mid);padding:8px 12px;border:1px solid var(--line);border-radius:20px;white-space:nowrap}.story-stage{position:relative;isolation:isolate;background:transparent;border-radius:12px;overflow:hidden}.story-viewport{overflow-x:auto;scrollbar-width:none;position:relative;z-index:1}.story-viewport::-webkit-scrollbar{display:none}.story-track{display:flex;gap:0;width:max-content}.story-item{width:336px;flex-shrink:0;min-width:0}.story-model{height:450px;position:relative;cursor:grab;touch-action:pan-y;background:transparent}.story-model:active{cursor:grabbing}.story-fallback{height:100%;display:flex;align-items:center;justify-content:center;padding:50px;color:var(--text)}.story-fallback img{width:100%;height:100%;object-fit:contain}.story-fallback p{font:18px/2 var(--serif)}button{cursor:pointer;color:var(--text);background:transparent;border:1px solid var(--line);border-radius:6px;padding:10px 13px;font-size:12px;min-height:40px}button:focus-visible,.story-model:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid #9b7c43;outline-offset:-3px}button[aria-pressed=true]{background:var(--light-faint)}.story-controls{display:flex;justify-content:space-between;gap:25px;padding:24px 0;border-top:1px solid var(--line);margin-top:24px}.story-control-title>span{font:22px var(--serif)}.story-control-title small{display:block;font-size:11px;color:var(--text-dim);margin:12px 0 22px}.story-buttons{display:flex;gap:8px}.material-controls{width:320px;display:grid;gap:12px}.material-controls label{display:flex;align-items:center;gap:16px;font-size:12px}.material-controls input{flex:1;min-width:0;accent-color:#9b7c43}.material-controls select{background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:10px 13px}.material-controls output{width:40px;text-align:right;font-variant-numeric:tabular-nums}.story-dialog{position:fixed;inset:0;z-index:1000;width:100vw;height:100vh;max-width:none;max-height:none;margin:0;padding:24px;background:#000b;border:0;display:grid;place-items:center;color:var(--text)}.story-dialog>div{width:min(100%,500px);max-height:85vh;overflow:auto;padding:30px;background:var(--bg);border:1px solid var(--line);border-radius:16px}.story-dialog h2{font:normal 25px/1.6 var(--serif);margin:20px 0}.story-dialog img{width:100%;max-height:260px;object-fit:contain}.story-dialog p{font:15px/2 var(--serif)}.story-close{float:right}@media(max-width:600px){.story-heading{display:block}.sample-badge{display:inline-block;margin-top:15px}.story-item{width:300px}.story-controls{flex-direction:column}.material-controls{width:100%}.story-model{height:430px}}
.story-ring{height:560px;position:relative;cursor:grab;touch-action:pan-y;outline-offset:-4px}.story-ring:active{cursor:grabbing}.ring-pagination{display:flex;justify-content:center;gap:6px}.ring-pagination button{min-height:32px;width:32px;border:0;padding:0;background:transparent;position:relative}.ring-pagination button::after{content:'';position:absolute;inset:13px;border-radius:50%;background:var(--text-dim)}.ring-pagination button[aria-pressed=true]::after{background:var(--light);box-shadow:0 0 10px var(--light-glow)}@media(max-width:600px){.story-ring{height:420px}}
</style>
<style>
.story-ring>.story-3d-canvas{position:absolute;inset:0;pointer-events:none;z-index:2;display:none}.story-stage.ready .story-3d-canvas{display:block}
</style>
