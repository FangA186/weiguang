import * as T from 'three';

export function createHoloStoryScene(story, sourceTexture) {
  const resources = new Set();
  let palette = { bg: '#0a0a0a', text: '#faf3df', accent: '#fbf6ec' };
  const painters = [];
  const keep = r => (resources.add(r), r);
  const scene = new T.Scene(), camera = new T.PerspectiveCamera(34, 1, 0.1, 100);
  camera.position.set(0, 0, 11);
  const root = new T.Group(); scene.add(root);
  scene.add(new T.HemisphereLight(0xffffff, 0x414060, 3));
  const key = new T.DirectionalLight(0xffffff, 5); key.position.set(-3, 4, 6); scene.add(key);
  const rim = new T.DirectionalLight(0xc0a3ff, 3); rim.position.set(4, -2, 3); scene.add(rim);
  const shape = new T.Shape(); const w = 2.6, h = 4.05, r = .17;
  shape.moveTo(-w/2+r,-h/2); shape.lineTo(w/2-r,-h/2);
  shape.quadraticCurveTo(w/2,-h/2,w/2,-h/2+r); shape.lineTo(w/2,h/2-r);
  shape.quadraticCurveTo(w/2,h/2,w/2-r,h/2); shape.lineTo(-w/2+r,h/2);
  shape.quadraticCurveTo(-w/2,h/2,-w/2,h/2-r); shape.lineTo(-w/2,-h/2+r);
  shape.quadraticCurveTo(-w/2,-h/2,-w/2+r,-h/2);
  const edgeMaterial = keep(new T.MeshStandardMaterial({ color: 0xd7b77a, metalness: .8, roughness: .25 }));
  const clearFace=keep(new T.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}));
  const body = new T.Mesh(keep(new T.ExtrudeGeometry(shape,{depth:.055,bevelEnabled:true,bevelThickness:.018,bevelSize:.018,bevelSegments:3,steps:1})),[clearFace,edgeMaterial]);
  body.position.z=-.09; root.add(body);
  const uniforms = { view: {value:new T.Vector3()}, gloss:{value:.65}, gold:{value:0}, baseColor:{value:new T.Color('#0a0a0a')}, accentColor:{value:new T.Color('#fbf6ec')}, themeColor:{value:new T.Color('#000000')} };
  uniforms.pearl={value:1};
  const foil = keep(new T.ShaderMaterial({ uniforms,transparent:true,depthWrite:false,side:T.DoubleSide,
    vertexShader: 'varying vec2 uvCard; void main(){uvCard=position.xy/vec2(2.6,4.05)+.5;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: `varying vec2 uvCard; uniform vec3 view,baseColor,accentColor,themeColor; uniform float gloss,gold,pearl;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      void main(){ vec2 uv=uvCard; float phase=uv.x*1.8+uv.y*.85+view.x*2.8+view.y*1.7;
      float shift=.5+.5*cos(6.28318*phase);
      vec3 rainbow=mix(themeColor,accentColor,.2+.8*shift);
      vec3 iridescence=.55+.45*cos(6.28318*(phase+vec3(0.,.33,.67)));
      rainbow=mix(rainbow,mix(vec3(.8,.86,.96),iridescence,.72),pearl);
      rainbow=mix(rainbow,vec3(1.,.68,.23),gold);
      float bands=pow(.5+.5*sin(phase*6.28318),8.);
      vec2 grid=uv*vec2(90.,140.); float star=step(.993,hash(floor(grid)))*(1.-smoothstep(0.,.14,length(fract(grid)-.5)));
      float border=step(.477,max(abs(uv.x-.5),abs(uv.y-.5)));
      vec3 col=mix(rainbow,accentColor,border);
      float alpha=gloss*(.025+.35*bands+pearl*.11)+star*.55;
      alpha=mix(alpha,.7,border);
      gl_FragColor=vec4(col,alpha);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      }` }));
  root.add(new T.Mesh(keep(new T.ShapeGeometry(shape)),foil));
  function label(text, sub, width, height, x, y, z, back=false){
    const canvas=document.createElement('canvas'); canvas.width=1024; canvas.height=256;
    const c=canvas.getContext('2d');
    const texture=keep(new T.CanvasTexture(canvas)); texture.colorSpace=T.SRGBColorSpace;
    const paint=()=>{c.clearRect(0,0,1024,256);c.save();c.beginPath();c.roundRect(0,0,1024,256,38);c.clip();c.fillStyle=palette.bg;c.fillRect(0,0,1024,256);c.fillStyle=palette.accent;c.fillRect(0,248,1024,8);c.fillStyle=palette.text;c.font='64px "Songti SC", serif';c.fillText(text,50,112,924);c.font='32px sans-serif';c.fillText(sub,52,182,920);c.restore();texture.needsUpdate=true;};
    painters.push(paint);paint();
    const mesh=new T.Mesh(keep(new T.PlaneGeometry(width,height)),keep(new T.MeshBasicMaterial({map:texture,transparent:true,alphaTest:.01})));
    mesh.position.set(x,y,z); if(back)mesh.rotation.y=Math.PI;
    mesh.userData.depth=z;root.add(mesh);return mesh;
  }
  const title=label(story.title,story.tag+' · '+story.author+' · 示例故事',2.55,.64,-.10,1.65,.65);
  const frontLabel=label('微光 · 故事典藏','翻到背面，读这封来信',2.15,.54,.35,-1.55,.72);
  const letterCanvas=document.createElement('canvas');letterCanvas.width=1024;letterCanvas.height=1536;
  const letterTexture=keep(new T.CanvasTexture(letterCanvas));letterTexture.colorSpace=T.SRGBColorSpace;
  const paintLetter=()=>{
    const c=letterCanvas.getContext('2d');c.clearRect(0,0,1024,letterCanvas.height);
    c.fillStyle=palette.accent;c.fillRect(56,190,912,4);c.fillStyle='#faf6ef';c.font='52px "Songti SC", serif';c.fillText(story.title,56,120,912);
    c.font='58px "Songti SC", serif';
    let line='',y=320;for(const char of story.text){if(c.measureText(line+char).width>912){c.fillText(line,56,y);line='';y+=98;}line+=char;}if(line)c.fillText(line,56,y);
    c.font='38px sans-serif';c.fillText(story.author+' · '+story.tag+' · 示例故事',56,1430,912);
    letterTexture.needsUpdate=true;
  };painters.push(paintLetter);paintLetter();
  const caption=new T.Mesh(keep(new T.PlaneGeometry(2.3,3.65)),keep(new T.MeshBasicMaterial({map:letterTexture,transparent:true,alphaTest:.01,depthWrite:false})));
  caption.position.set(0,0,-.115);caption.rotation.y=Math.PI;root.add(caption);

  const texture=sourceTexture || null;
  const subject=new T.Mesh(keep(new T.PlaneGeometry(story.transparent ? 2.9 : 2.25, story.transparent ? 4.35 : 2.95)),keep(new T.MeshBasicMaterial({map:texture,transparent:true,alphaTest:.015,depthWrite:false})));
  subject.visible=!!sourceTexture;subject.position.set(0,.20,.28);root.add(subject);
  const dust = new T.Group();root.add(dust);
  for(let i=0;i<12;i++){
    const a=i*2.399;const mesh=new T.Mesh(keep(new T.OctahedronGeometry(.022+(i%3)*.012)),edgeMaterial);
    mesh.position.set(Math.cos(a)*(1.3+(i%2)*.17),Math.sin(a)*2.05,.38+(i%3)*.12);dust.add(mesh);
  }

  return {
    scene, camera, root,
    resize(width, height) {
      camera.aspect = width / height;
      camera.position.z = Math.max(9.6, 6.3 / camera.aspect);
      camera.updateProjectionMatrix();
    },
    update(dt, state, reduced, travel=0, viewerCamera=camera) {
    uniforms.pearl.value=state.finish==='pearl'?1:0;
    if(state.auto&&!reduced)state.aimY+=dt*.32;
    const amount=reduced?1:1-Math.exp(-dt*12);
    root.rotation.x=T.MathUtils.lerp(root.rotation.x,state.aimX,amount);
    root.rotation.y=T.MathUtils.lerp(root.rotation.y,state.aimY+(state.flipped?Math.PI:0),amount);
    for(const m of [title,frontLabel])m.position.z=.10+m.userData.depth*state.depth;
    subject.position.z=.08+.42*state.depth;dust.position.z=.25*state.depth;
    root.updateWorldMatrix(true,false);viewerCamera.getWorldPosition(uniforms.view.value);uniforms.view.value.x-=travel*viewerCamera.position.z*1.2;root.worldToLocal(uniforms.view.value);uniforms.view.value.normalize();
    uniforms.gloss.value=state.gloss;uniforms.gold.value=state.finish==='gold'?1:0;
    if(state.finish==='pearl')edgeMaterial.color.set('#bfc9df');
    else if(state.finish==='gold')edgeMaterial.color.set('#d7af56');
    else edgeMaterial.color.copy(uniforms.accentColor.value);
    edgeMaterial.metalness=state.finish==='gold'?.9:.8;
    edgeMaterial.roughness=state.finish==='gold'?.18:.25;

    },
    setTheme(next) { palette=next; uniforms.baseColor.value.set(next.surface);uniforms.accentColor.value.set(next.accent);uniforms.themeColor.value.set(next.base);rim.color.set(next.base); for(const paint of painters)paint(); },
    dispose() { for (const resource of resources) resource.dispose(); },
  };
}
