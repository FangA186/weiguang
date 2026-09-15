<script setup lang="ts">
import { computed, watch } from 'vue';
import { instructionUnits, previewVoiceInstruction } from '../lib/voiceInstruction';
import type { VoiceProfile } from '../types';
const props = defineProps<{ modelValue: VoiceProfile; model?: string }>();
const emit = defineEmits<{ (e:'update:modelValue', value:VoiceProfile):void; (e:'validity', valid:boolean):void }>();
const instructionPreview = computed(() => previewVoiceInstruction(props.modelValue));
const usedUnits = computed(() => instructionUnits(instructionPreview.value));
const valid = computed(() => props.model !== 'cosyvoice-v3.5-plus' || usedUnits.value <= 100);
watch(valid, value => emit('validity', value), { immediate:true, flush:'sync' });
const paceMode = computed(() => props.modelValue.pace_mode || (props.modelValue.pace ? 'manual' : 'auto'));
const emotionMode = computed(() => props.modelValue.emotion_mode || (props.modelValue.emotion ? 'manual' : 'auto'));
function update(key: keyof VoiceProfile, value: unknown) { emit('update:modelValue', { ...props.modelValue, use_defaults:false, [key]:value }); }
function resetDefaults() { emit('update:modelValue', { use_defaults:true, rate:1, volume:50, pitch:1, emotion_mode:'auto', traits:[], instruction:'' }); }
function value(event: Event) { return (event.target as HTMLInputElement).value; }
function toggleTrait(trait:string) {
  const current = props.modelValue.traits || [];
  update('traits', current.includes(trait) ? current.filter(t=>t!==trait) : [...current,trait]);
}
const controls = ['sad','amazed','deep and loud shouting','trembling','angry','excited','sarcastic','curious','like dracula','bored','tired','scornful','shouting','asmr','panicked','mischievously','empathetic','whispers','reluctantly','crying','serious','very slowly','very fast'];
const effects = ['gasp','sighing','clears throat','giggles','laughing','cough','snorts'];
</script>

<template>
  <div class="voice-profile-form">
    <template v-if="model === 'cosyvoice-v3.5-plus'">
      <p class="voice-profile-note">当前音色：CosyVoice-v3.5-plus。保存后对新生成语音生效。</p>
      <button type="button" @click="resetDefaults">恢复默认设置（不传声音参数）</button>
      <p v-if="modelValue.use_defaults" class="voice-profile-note" role="status">已选择原始模式，点击保存后只发送文本、音色和音频格式。修改下方任一项会退出原始模式。</p>
      <div class="voice-profile-grid">
        <label>语速 rate（0.5–2倍）<input type="number" min="0.5" max="2" step="0.05" :value="modelValue.rate ?? 1" @change="update('rate',Number(value($event)))" /><small>1倍为默认速度。</small></label>
        <label>音量 volume（0–100）<input type="number" min="0" max="100" step="1" :value="modelValue.volume ?? 50" @change="update('volume',Number(value($event)))" /><small>默认50；0为静音。</small></label>
        <label>音调 pitch（0.5–2）<input type="number" min="0.5" max="2" step="0.05" :value="modelValue.pitch ?? 1" @change="update('pitch',Number(value($event)))" /><small>1为原始音调；数值越高，音调越高。</small></label>
        <label>情绪模式<select :value="emotionMode" @change="update('emotion_mode',value($event))"><option value="auto">跟随语境</option><option value="manual">固定情绪</option></select></label>
        <label>情绪<select :disabled="emotionMode === 'auto'" :value="modelValue.emotion || 'calm'" @change="update('emotion',value($event))"><option value="calm">平静</option><option value="gentle">温柔</option><option value="cheerful">开心</option><option value="playful">俏皮</option><option value="sad">低落</option><option value="angry">克制生气</option></select><small v-if="emotionMode === 'auto'">先把上方“情绪模式”改成“固定情绪”，即可手动选择。</small></label>
        <label>声音年龄感<select :value="modelValue.age_feel || ''" @change="update('age_feel',value($event))"><option value="">保持原音色</option><option v-for="a in ['儿童','青少年','青年','中年','老年']" :key="a">{{ a }}</option></select></label>
        <label>声音呈现<select :value="modelValue.presentation || ''" @change="update('presentation',value($event))"><option value="">保持原音色</option><option>男性</option><option>女性</option><option>中性</option></select></label>
      </div>
      <div class="voice-profile-traits"><label v-for="trait in ['磁性','清脆','沙哑','圆润','甜美','浑厚','有力']" :key="trait"><input type="checkbox" :checked="modelValue.traits?.includes(trait)" @change="toggleTrait(trait)" />{{ trait }}</label></div>
      <label>补充声音描述<textarea rows="3" maxlength="800" :aria-invalid="!valid" aria-describedby="voice-instruction-budget" :value="modelValue.instruction || ''" @input="update('instruction',value($event))" placeholder="例如：尾音干净，停顿自然" /></label>
      <p id="voice-instruction-budget" class="voice-profile-note" :class="{ 'voice-profile-error': !valid }" aria-live="polite">完整指令 {{ usedUnits }} / 100 单位 · {{ valid ? `剩余 ${100 - usedUnits} 单位` : `超出 ${usedUnits - 100} 单位，请缩短描述或减少选项后保存` }}。汉字按2单位计算；其他非ASCII字符也按2单位保守计算。</p>
      <div class="voice-profile-evidence"><strong>{{ emotionMode === 'auto' ? '完整指令预览（普通聊天示例）' : '完整指令预览' }}</strong><p>{{ instructionPreview || '原始模式：不发送声音指令' }}</p></div>
      <p class="voice-profile-note">跟随语境时，开头的四字情绪描述会随场景变化，长度不变。选项和补充描述共用100单位；超限时不会保存，也不会悄悄截短输入。</p>
    </template>
    <template v-else>
    <p class="voice-profile-note">语音聊天跟随整轮语境调整语气和语速，保持表达连贯；固定选项优先。保存后对新生成的语音生效，旧语音回放不会改变。</p>
    <p v-if="modelValue.evidence" class="voice-profile-evidence">文字依据：{{ modelValue.evidence }}</p>
    <div class="voice-profile-grid">
      <label>语速模式<select :value="paceMode" @change="update('pace_mode',value($event))"><option value="auto">跟随语境</option><option value="manual">固定语速</option></select></label>
      <label>固定语速（0.5–2倍）<input type="number" min="0.5" max="2" step="0.05" :disabled="paceMode === 'auto'" :value="modelValue.rate ?? ({slow:.85,normal:1,fast:1.15}[modelValue.pace || 'normal'])" @change="update('rate',Number(value($event)))" /><small v-if="paceMode === 'auto'">当前按语境在0.96–1.04倍间调整；切换固定语速后可修改。</small></label>
      <label>情绪模式<select :value="emotionMode" @change="update('emotion_mode',value($event))"><option value="auto">跟随语境</option><option value="manual">固定基调</option></select></label>
      <label>情绪基调<select :disabled="emotionMode === 'auto'" :value="modelValue.emotion || 'calm'" @change="update('emotion',value($event))"><option value="calm">平静</option><option value="gentle">温柔</option><option value="cheerful">开心</option><option value="playful">俏皮</option><option value="sad">低落</option><option value="angry">克制生气</option></select><small v-if="emotionMode === 'auto'">当前由语境决定；切换固定基调后可修改。</small></label>
      <label>拟声表达<select :value="modelValue.effects === 'manual' ? 'manual' : 'off'" @change="update('effects',value($event))"><option value="off">关闭（默认）</option><option value="manual">指定效果（每轮最多一次）</option></select><small>不自动插入笑声或叹息。</small></label>
      <label>输出采样率<select :value="modelValue.sample_rate || 24000" @change="update('sample_rate',Number(value($event)))"><option :value="24000">24 kHz（默认）</option><option :value="48000">48 kHz（数据量更大）</option></select></label>
    </div>
    <details>
      <summary>更多声音维度（可选）</summary>
      <div class="voice-profile-grid">
        <label>声音呈现<select :value="modelValue.presentation || ''" @change="update('presentation',value($event))"><option value="">保持音色原貌</option><option>男性</option><option>女性</option><option>中性</option></select></label>
        <label>声音年龄感<select :value="modelValue.age_feel || ''" @change="update('age_feel',value($event))"><option value="">未指定</option><option v-for="a in ['儿童','青少年','青年','中年','老年']" :key="a">{{ a }}</option></select></label>
        <label>音调倾向<select :value="modelValue.pitch_hint || '自然'" @change="update('pitch_hint',value($event))"><option>自然</option><option>偏高</option><option>偏低</option></select></label>
        <label>使用场景<select :disabled="emotionMode === 'auto'" :value="modelValue.scenario || '日常陪伴'" @change="update('scenario',value($event))"><option v-for="s in ['日常陪伴','朗读','讲解','新闻播报','广告配音','动画角色']" :key="s">{{ s }}</option></select><small v-if="emotionMode === 'auto'">跟随语境时自动选择场景。</small></label>
        <label v-if="emotionMode === 'manual'">固定风格标签<select :value="modelValue.control_tag || ''" @change="update('control_tag',value($event))"><option value="">不指定标签</option><option v-for="t in controls" :key="t">{{ t }}</option></select><small>指定标签后优先于情绪基调。</small></label>
        <label v-if="modelValue.effects === 'manual'">拟声标签<select :value="modelValue.effect_tag || ''" @change="update('effect_tag',value($event))"><option value="">不指定效果</option><option v-for="t in effects" :key="t">{{ t }}</option></select></label>
      </div>
      <div class="voice-profile-traits"><label v-for="trait in ['磁性','清脆','沙哑','圆润','甜美','浑厚','有力']" :key="trait"><input type="checkbox" :checked="modelValue.traits?.includes(trait)" @change="toggleTrait(trait)" />{{ trait }}</label></div>
      <p class="voice-profile-note">以上是目标声音偏好，效果取决于所选音色；不会重新训练或替换你的克隆音色。采样率不保证吐字更清楚。</p>
    </details>
    <label>补充声音描述<textarea rows="2" maxlength="800" :disabled="emotionMode === 'auto'" :value="modelValue.instruction || ''" @input="update('instruction',value($event))" placeholder="例如：停顿自然，表达亲近，避免过度夸张。" /><small v-if="emotionMode === 'auto'">描述会保留，但仅在固定基调模式下使用。</small></label>
    </template>
  </div>
</template>

<style scoped>
.voice-profile-form { display:flex; flex-direction:column; gap:14px; color:#ddd; font-size:13px; }
.voice-profile-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
label { display:flex; flex-direction:column; gap:7px; }
select,input[type=number],textarea { min-width:0; width:100%; border:1px solid #454039; border-radius:7px; padding:9px 10px; background:#101112; color:#eee; font:inherit; }
select:focus-visible,input:focus-visible,textarea:focus-visible { outline:2px solid #c7ac75; outline-offset:2px; }
select:disabled,input:disabled,textarea:disabled { opacity:.55; cursor:not-allowed; }
small { color:#aaa; line-height:1.5; }
.voice-profile-note { margin:0; color:#aaa; line-height:1.6; }
.voice-profile-error { color:#ffb4a9; }
.voice-profile-evidence { margin:0; padding:10px; background:#29261f; color:#e5cea4; border-radius:7px; }
summary { cursor:pointer; color:#e5cea4; margin-bottom:12px; }
.voice-profile-traits { display:flex; flex-wrap:wrap; gap:12px; margin:15px 0; }
.voice-profile-traits label { flex-direction:row; align-items:center; }
@media(max-width:600px) { .voice-profile-grid { grid-template-columns:1fr; } }
</style>
