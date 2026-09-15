# [未完成] Qwen Plus与CosyVoice接入调研

> **状态**：未完成 (Pending)
> **创建时间**：2026-09-13

## 官方核验结论

- 复刻API的target_model必须与后续合成模型一致，不能用Qwen Plus的voice_id驱动CosyVoice。https://help.aliyun.com/zh/model-studio/voice-clone-design-http-api
- cosyvoice-v3.5-plus支持HTTP/WebSocket、复刻与设计音色，不支持系统音色。https://help.aliyun.com/zh/model-studio/tts-model
- HTTP合成可沿用SpeechSynthesizer端点和SSE，支持instruction；Qwen情感方括号标签不能直接当CosyVoice协议使用。https://help.aliyun.com/zh/model-studio/cosyvoice-tts-http-api
- 北京合成单价：Qwen Plus 1.4元/万字符，CosyVoice v3.5 Plus 1.5元/万字符；不含复刻、存储、文本模型等费用，实际计费以供应商账单为准。https://help.aliyun.com/zh/model-studio/model-pricing

## 当前源码差距

- backend/providers/qwen_voice_clone.py用settings.tts_model作为复刻target_model，尚无每次创建时的模型选择。
- backend/app.py的_resolve_tts_voice_and_model已根据数据库音色target_model路由，可沿用；adaptive语音入口目前仅允许Qwen Flash/Plus，需要扩展到CosyVoice并按模型处理标签。
- 复刻需确认CosyVoice音色就绪状态；现有voice_exists仅验证对象存在，不能替代可合成状态验证。
- 管理端成本目前通用费率需要按实际模型分别计算，保留旧Flash历史音色及语音回放。

## 可行方案与待选分支

1. 以CosyVoice声音聊天为目标：直接为cosyvoice-v3.5-plus复刻，随后由同模型合成。新增CosyVoice路径，旧Qwen音色按原模型继续工作。
2. 两模型对比：同一原始参考音频分别创建Qwen Plus和CosyVoice音色，选择音色后按所属模型合成。需要两个供应商音色及明确槽位规则，不能静默消耗两份槽位。
3. 分开用途：用户自定义音色用Qwen Plus复刻和合成；默认声音聊天用单独的CosyVoice设计/复刻音色。需确定默认音色来源。

## 实施及验收

先明确上述分支；再接模型选择、允许列表、CosyVoice无标签指令合成、就绪状态、模型费率与设置提示。mock验证跨模型不误路由、旧音色兼容、额度和回放；真实短音频对比首包耗时、总耗时、听感及账单元数据。不以模型名称推断实际音质提升。

本轮完成官方资料与本地源码调研，未改变运行模型、创建音色或部署。

## 2026-09-13 接入进展

描述额度体验更新：取消固定30字上限，前端按整条指令实时计算100单位并显示预览；自动情绪标为普通聊天示例。超限阻止保存且保留输入，恢复默认归零。2项预算回归和前端构建通过；后端最终长度保护保留。

文本流失败后续：历史错误未记录内部异常，确切原因未确认；另确认并修复多行JSON解析缺陷，增加逐字符多对象回归。前端不再用“我在听。”冒充空回复；情绪auto模式增加切换提示。回归/构建通过，日志补充脱敏异常类型供后续定位。

### 最新策略：按用户要求关闭声音指令

#### 最新用户调整：恢复描述、pitch和原始模式开关

已恢复CosyVoice情绪/声音呈现/年龄感/traits及补充描述，以100单位内指令发送；pitch范围0.5–2，默认1。voice_style JSON增加pitch/use_defaults，无表结构变化。页面恢复默认后设置use_defaults=true并清空描述；保存后Provider仅传text/voice/format。编辑任一项退出原始模式。聊天计划记录pitch/use_defaults，直接朗读同步传递且缓存键包含设置。

验证：HTTP/SSE精确字段、指令上限、adaptive与额度回归通过；前端构建通过。真实CosyVoice音色自定义描述+pitch返回39450字节PCM，原始模式返回48480字节PCM，本地健康200。声音审美仍需试听，未发布。

最新调整：用户要求重新开放rate和volume。CosyVoice设置页仅显示0.5–2语速及0–100音量，按现有voice_style JSON保存；后端VoiceProfile增加volume验证，语音计划携带rate/volume用于合成与回放。直接朗读同步传volume，缓存键随配置变化。instruction仍关闭，采样率仍用22050默认。旧Qwen设置保留。请求参数/语音/额度回归和前端构建通过。

后续用户要求完全使用CosyVoice默认声音参数：公共Provider仅发送text、voice、format，不发送rate、sample_rate、instruction及其他声音设置。PCM流按官方默认22050Hz解码、存储与计时，额度预留按默认1倍语速。前端按要求保持不变，所有声音调节暂不影响CosyVoice新合成；Qwen不变。回归验证精确请求字段及PCM时长通过。

CosyVoice HTTP和SSE请求完全不发送instruction，计划记录也为空；旧回放即便有历史instruction，Provider仍不发送。保留rate、sample_rate、voice、format，清除Qwen标签。Qwen原有行为保留；设置页标注适用范围。HTTP/SSE及adaptive回归通过，本地健康200。

官方API参数复核：https://help.aliyun.com/zh/model-studio/cosyvoice-tts-http-api
- volume：0–100，默认50；本项目未显式发送，使用默认值。
- rate：0.5–2，默认1；已接入固定/自动语速。
- pitch：0.5–2，默认1；未接入数值参数，原音调倾向是指令描述，不等同于pitch。
- language_hints：数组只处理第一项，用于目标语言提示；未接入合成端（复刻language_hints含义不同）。
- 方言：官方用户指南通过instruction设置，当前关闭指令不提供强制方言。https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide
- sample_rate及format已接入；HTTP通过X-DashScope-SSE: enable返回流式PCM。官方控制台的显示选项不等于相同名称的API字段。

真实使用发现428无声音：CosyVoice instruction限100字符单位，汉字按2，原长指令未适配。已精简语境指令并在共享Provider入口限制长度；中英混合边界和原有回归通过，真实用户CosyVoice音色短指令成功返回PCM。官方依据：https://help.aliyun.com/zh/model-studio/error-code 。浏览器完整播放仍待用户确认。

用户已选择CosyVoice。新创建请求默认target_model=cosyvoice-v3.5-plus，按受限模型列表校验，现有数据库target_model路由保留；默认系统音色仍用现有Qwen，避免无CosyVoice音色时失败。复刻使用替换后的Settings实例，不改全局配置。合成前查询状态，非OK返回409；不把存在等同于就绪。

复用官方HTTP/SSE协议；CosyVoice去掉Qwen控制标签，手动风格转自然语言，指定拟声不支持且在UI说明。后台按实际模型估算CosyVoice 1.5元/万字符、Qwen Plus 1.4元/万字符，其余沿用配置。

验证：adaptive speech、HTTP/SSE参数及额度mock回归通过，新增CosyVoice路由、DEPLOYING/UNDEPLOYED拒绝、费率及Qwen回放兼容检查；两端构建和后端编译通过，本地健康200。未创建真实CosyVoice音色、未真实合成试听、未发布；方案仍为未完成，待真实音色验收。
