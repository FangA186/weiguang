<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const pages = {
  privacy: {
    title: "隐私政策",
    intro: "这份说明告诉你微光收集哪些信息、为什么使用，以及你可以如何管理它们。",
    sections: [
      ["我们处理的信息", "注册时会保存邮箱、昵称和账号状态。使用对话、截图导入、角色工坊或声音功能时，会处理你主动提交的文字、图片、视频、角色设置、导入记录和声音复刻相关文件，以及用于提供服务的用量与操作记录。"],
      ["语音与第三方服务", "聊天语音输入由浏览器的 SpeechRecognition 完成，微光当前不接收麦克风原始录音；浏览器厂商可能按其自身政策使用在线识别服务。你主动上传的图片、视频或参考音频会通过私有对象存储和相应的模型服务完成识别、生成或复刻，浏览器不会收到服务端 API Key。"],
      ["我们如何使用信息", "信息用于登录鉴权、保存你的对话和角色、执行额度与兑换、生成 AI 回复、处理安全问题和改进服务。不会把你的账号内容用于对外展示或出售；如法律要求、保护服务安全或你明确要求协助，可能需要在必要范围内处理。"],
      ["你的选择", "你可以在个人中心修改昵称和头像，在声音、角色和导入页面删除相应资产，并在个人中心提交账号注销。注销后的服务端结果会说明主数据和外部资产的清理状态；签名媒体链接会过期。"],
      ["安全与变更", "我们使用 HttpOnly 会话 Cookie、账号归属校验和短期签名媒体链接降低风险。任何在线服务都不能保证绝对安全；政策发生实质变化时，会在页面更新日期并提示关键变化。"],
    ],
  },
  terms: {
    title: "用户协议",
    intro: "使用微光前请阅读这些边界；注册、对话、导入或购买即表示你理解并同意适用条款。",
    sections: [
      ["服务性质", "微光提供明确标注为 AI 的陪伴、对话、声音合成和角色定制服务，不冒充或替代现实中的任何人。AI 输出可能不准确，不应替代医疗、法律、财务或危机处置建议。"],
      ["你提交的内容", "你应当拥有上传的图片、聊天记录、声音和其他内容的合法权利，并对其中包含的第三方信息负责。不得上传违法内容、未经授权的他人声音或试图绕过安全和额度限制的内容。"],
      ["套餐与兑换", "免费体验和付费套餐的额度、周期、可用能力以微光服务端当前返回结果为准。链动小铺是外部售卖渠道，购买、发货、支付和未兑换订单售后以该渠道订单页面为准；微光不把外部订单状态当作自动退款或自动续期结果。"],
      ["账号与终止", "请妥善保管密码，不要共享账号。你可以在个人中心注销账号；服务端会按返回结果处理账号关联数据，外部存储或备份中的清理可能异步完成。违反协议或危及服务安全时，微光可能限制相关账号。"],
      ["条款更新", "我们可能因功能、法律或安全要求更新协议。继续使用更新后的服务表示接受更新内容；如果你不同意，可以停止使用并注销账号。"],
    ],
  },
  "data-rights": {
    title: "数据保留与删除说明",
    intro: "这里集中说明当前版本能做什么、哪些清理可能需要时间，以及如何避免把“已提交”误解成“立即全部消失”。",
    sections: [
      ["默认保留范围", "账号邮箱、昵称、对话、角色与记忆、导入批次、声音设置和套餐兑换记录会在账号存续期间保留，用于提供对应功能和账务/安全追踪。当前没有对外承诺统一的固定保留天数；需要删除时请以服务端实际返回为准。"],
      ["账号注销", "进入个人中心的“隐私与数据”，先点击“开始注销”，阅读风险提示后再次点击“确认永久注销并删除”。请求成功后当前设备退出登录，服务端会返回可删除主数据的处理结果；该操作不可撤销。"],
      ["外部资产与备份", "对象存储、模型服务或备份中的副本可能无法与账号主数据同时完成清理。如果服务端返回 pending、partial、failed 或类似状态，页面会明确提示仍有外部清理任务；在清理完成前不应把相关资产视为已经彻底删除。"],
      ["其他管理入口", "个人中心可修改昵称和头像；声音设置、角色工坊与截图导入页提供各自的删除入口。当前没有伪造的“忘记密码”“邮箱验证”或一键导出功能；这些能力开放前，请妥善保存登录凭据。"],
      ["问题反馈", "如果删除结果与你的预期不一致，请保留页面显示的状态和时间，在购买渠道订单售后页提交需要人工处理的事项。不要在公开渠道粘贴密码、API Key、完整兑换码或完整聊天记录。"],
    ],
  },
} as const;

const pageKey = computed<keyof typeof pages>(() => (
  typeof route.name === "string" && route.name in pages
    ? route.name as keyof typeof pages
    : "privacy"
));
const page = computed(() => pages[pageKey.value]);
</script>

<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="legal-brand"><span></span>微光 · AI 陪伴</router-link>
      <router-link to="/pricing" class="legal-back">查看套餐</router-link>
    </header>

    <main class="legal-main" :aria-labelledby="`legal-title-${pageKey}`">
      <nav class="legal-tabs" aria-label="法律与数据说明">
        <router-link to="/privacy" :class="{ 'is-active': pageKey === 'privacy' }">隐私政策</router-link>
        <router-link to="/terms" :class="{ 'is-active': pageKey === 'terms' }">用户协议</router-link>
        <router-link to="/data-rights" :class="{ 'is-active': pageKey === 'data-rights' }">数据保留与删除</router-link>
      </nav>

      <article class="legal-card">
        <p class="legal-eyebrow">WEIGUANG · INFORMATION</p>
        <h1 :id="`legal-title-${pageKey}`">{{ page.title }}</h1>
        <p class="legal-intro">{{ page.intro }}</p>
        <p class="legal-updated">当前页面版本：2026-09-05 · 如页面与服务端返回不一致，以当前服务端结果为准。</p>
        <section v-for="[title, body] in page.sections" :key="title" class="legal-section">
          <h2>{{ title }}</h2>
          <p>{{ body }}</p>
        </section>
      </article>
    </main>
  </div>
</template>

<style scoped>
.legal-page { min-height: 100vh; background: radial-gradient(circle at 50% 0%, rgba(236,215,175,.08), transparent 34%), #090b0e; color: var(--text); font-family: var(--sans); }
.legal-header { min-height: 64px; display: flex; align-items: center; justify-content: space-between; padding: 0 28px; border-bottom: 1px solid var(--line); }
.legal-brand, .legal-back { color: var(--text-mid); text-decoration: none; font-size: .78rem; }
.legal-brand { display: inline-flex; align-items: center; gap: 9px; color: var(--text); font: 400 .9rem/1 var(--serif); }
.legal-brand span { width: 7px; height: 7px; border-radius: 50%; background: var(--light); box-shadow: 0 0 12px var(--light-glow); }
.legal-back:hover, .legal-tabs a:hover { color: #ecd7af; }
.legal-main { width: min(820px, calc(100% - 32px)); margin: 0 auto; padding: 54px 0 90px; }
.legal-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.legal-tabs a { padding: 8px 12px; border: 1px solid var(--line); border-radius: 999px; color: var(--text-dim); font-size: .74rem; text-decoration: none; }
.legal-tabs a.is-active { border-color: rgba(236,215,175,.45); background: rgba(236,215,175,.09); color: #ecd7af; }
.legal-card { padding: clamp(24px, 5vw, 48px); border: 1px solid var(--line); border-radius: 14px; background: rgba(255,255,255,.025); }
.legal-eyebrow { margin: 0 0 13px; color: #ecd7af; font-size: .68rem; letter-spacing: .18em; }
.legal-card h1 { margin: 0; font: 400 clamp(2rem, 5vw, 3rem)/1.25 var(--serif); }
.legal-intro { margin: 18px 0 8px; color: var(--text-mid); font-size: .88rem; line-height: 1.8; }
.legal-updated { margin: 0; color: var(--text-faint); font-size: .7rem; line-height: 1.6; }
.legal-section { margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.legal-section h2 { margin: 0 0 8px; font: 400 1rem/1.5 var(--serif); color: #ecd7af; }
.legal-section p { margin: 0; color: var(--text-mid); font-size: .8rem; line-height: 1.9; }
@media (max-width: 560px) { .legal-header { padding: 0 16px; } .legal-main { padding-top: 34px; } .legal-tabs a { flex: 1 1 auto; text-align: center; } }
</style>
