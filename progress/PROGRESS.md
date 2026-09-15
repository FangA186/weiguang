# 微光（Weiguang）项目进度跟踪与排障解决宝典

### 2026-09-15：手机背景恢复上一版铺满效果

- 按用户要求撤回完整图片contain调整，恢复手机首屏cover铺满和38%水平取景，保留文字叠加。桌面不变，生产构建通过，未发布。

### 2026-09-15：手机首屏完整图片置于文字背后

- 用户明确要求既完整显示横图，又保持图片在文字背后。手机断点图片层改为contain居中，遮罩层仍100%覆盖；取消38%取景和cover裁切，按原比例显示，余下区域为深色。
- 构建通过，Chrome 440×956截图确认整张3.png在标题背后显示。桌面规则不变，未发布。

### 2026-09-15：手机首屏恢复图片叠字

- 按用户澄清，手机背景需和PC一致处于文字后方。恢复100svh背景覆盖，横向取景38%，文字居中叠加；保留手机字号与间距修正。
- 构建通过，Chrome 375×667截图确认图片在文字下层、标题三行及按钮可见。未发布。

### 2026-09-15：手机首页背景适配

- 原因：横版3.png按100vh高度cover，竖屏大幅裁切人脸；标题18ch还造成中文单字换行。
- 修改landing.css手机断点：背景按原图1672:941比例置于导航下方，底部渐隐；文案排列在图片下方，压缩间距并使用100svh最小高度，标题宽度按可用空间显示。桌面规则不变。
- 构建通过；Chrome iPhone SE 375×667截图确认人像构图完整、标题三行，按钮底部567px位于首屏内，无横向溢出。未发布。

### 2026-09-14：克隆声音弹窗清理厂商与模型文案

- 移除厂商/OSS技术标题说明、模型版本说明和已绑定内部音色ID；列表仅显示用户音色名称与时长，参考音频仅显示名称；上传/处理/净化提示改为普通操作文案，未命名音色不再回退显示内部ID。保留模型调用参数、授权和录音指导。
- 前端构建通过，Chrome打开克隆声音弹窗，确认现有音色显示“我的音色”“9.5秒”，无厂商、模型及内部ID文案。未调用声音克隆或修改音色数据，未发布。

### 2026-09-14：取消聊天背景上传

- 用户取消背景上传功能。移除剩余消息区背景上传/清除、文件选择器、状态提示及背景渲染，清理前端API/store调用和导航插槽。数据库历史记录和后端兼容接口保留，聊天页不再使用。
- 前端构建通过，Chrome确认导航无背景按钮、整页和消息区background-image均为none。未发布。

### 2026-09-14：移除全局背景入口与展示

- 按用户要求移除聊天页全局背景显示及上传入口，只保留消息区上传/清除，保存固定scope=panel；历史全局字段与素材保留兼容。
- 构建通过，Chrome确认整页background-image为none且消息区原背景仍存在。未发布。

### 2026-09-14：上传背景等比完整适配

- 现象：竖图用于横向消息区时只显示放大的人脸局部。根因：全局和消息区使用cover强制铺满并裁切，移动端还重复覆盖该设置。
- 修复：chat.css将遮罩层维持100%填充、图片层改为contain，等比完整显示；消息区有单独背景时用主题底色填充留白，避免透出另一张图。清除移动端重复cover规则，ChatView用has-background标记控制底色。
- 验证：使用用户已上传的真实两张背景在新Chrome页面检查；桌面竖图完整显示，390×844手机截图及计算样式确认两处contain、无横向溢出，生产构建通过。未发布。

### 2026-09-14：全局与消息区背景分开设置

- 根据用户明确的范围，整页背景和右侧消息区背景分别上传；全局保存成功用同一SQL更新并清空消息区背景，失败保留原设置。单独清除消息区保留全局，恢复默认清空两者。021字段存数据库，账号删除资源清理同步纳入。
- mock验证范围、清空联动、失败保留及归属，生产构建通过；只读确认021迁移，Chrome新页确认原背景回显及两个入口。新范围真实上传覆盖未操作，未发布。

### 2026-09-14：聊天背景上传与恢复默认

- 聊天页右上角新增上传背景和恢复默认。复用OSS图片上传及账号store，新增020迁移及账号背景字段；后端校验归属、文件头和5MB上限，持久化对象键并签名回显。背景叠加暗色遮罩保证文字可读，不使用localStorage。
- 前端构建、背景mock回归、会话头像回归通过；只读确认本地迁移及字段存在，Chrome按钮打开单文件选择器。真实OSS上传、显示及刷新保留待选图验收，未发布。

### 2026-09-14：首屏恢复3.png

- 按用户选择将首屏4.png换回3.png，渐变与布局保持不变。生产构建通过，未发布。

### 2026-09-14：首屏试用4.png

- 首屏背景由3.png替换为4.png，保留原有渐变和布局。生产构建与Chrome显示检查通过，未发布。

### 2026-09-14：首屏切换3.png并移除双人照片段落

- 首屏背景替换为3.png，沿用底层背景及暗色渐变；移除下方女生、男生照片区及专属样式，原始素材保留。
- 生产构建通过，Chrome截图确认3.png显示，页面结构确认两张照片展示已移除。未发布。

### 2026-09-14：恢复人物底层单侧渐隐效果

- 按用户指定恢复原视觉效果：女生左侧渐隐、男生右侧渐隐，底部透明淡出，整体不透明度0.65。人物区域z-index -1，低于底光与粒子；移除容器宽度限制和水平留白，外侧贴页面边缘，避免外侧竖直分界。首屏1.png及先女右后男左顺序保留。
- 前端构建通过，Chrome截图确认女生内侧自然融入背景，计算样式确认男女反向遮罩、图片加载成功和底层层级。未发布。

### 2026-09-14：人物照片取消椭圆遮罩

- 现象与根因：照片显示为椭圆，来自landing.css新增的ellipse径向遮罩。改为水平和垂直线性遮罩交集，仅四边8%范围渐隐，保留矩形构图；男女照片共用修复。
- 生产构建通过，Chrome截图确认女生照片不再椭圆裁切。未发布。

### 2026-09-14：首页照片分段展示与光板移除

- 按用户要求移除首页HoloStoryCarousel入口及其控制区（组件文件保留），首屏使用1.png底层背景。原光板位置改为女生2.png靠右，下一段男生male-left.png靠左；图片保留柔和边缘，移动端宽度70%。
- 前端生产构建通过，Chrome逐段截图确认首屏1.png、女生右侧、男生下方左侧，光板及控制项不再显示。未发布。

### 2026-09-14：首页加入左侧男生照片

- 将male-left.png复制至前端public背景目录，LandingView新增装饰背景元素，复用右侧图片45%宽度、底层层级和0.65不透明度，反向渐隐形成左右对称布局。
- 前端构建通过，本地浏览器确认男左女右、中央文案清晰、边缘无竖直硬线；未发布。

### 2026-09-14：首页右侧背景硬边与层级修复

- 现象：图片左边出现竖直分界，图片视觉上覆盖原有底光。根因：首屏自身z-index为2，其负层级伪元素仍整体在底光层0之上；不透明主题色渐变遮住底光，导致边界颜色不连续。
- 修复：`frontend/src/assets/styles/landing.css` 将图片移至 `.landing::after`，以父级 `isolation: isolate` 和图片z-index -1置于底光、粒子、正文下方；左侧改用透明遮罩渐隐，并降低整体不透明度至0.65。仍仅占右侧45%。
- 依据：MDN [mask-image](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask-image) 与 [isolation](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/isolation)；渐隐范围与透明度为本页面视觉取值。
- 验证：生产构建通过；本地浏览器截图确认无竖直硬边，计算样式确认图片-1、底光0、正文2。未发布。

### 2026-09-14：首页2.png仅右侧显示

- 按用户要求恢复2.png，首屏图片区域固定在右侧45%宽度，左侧与底部渐变衔接主题背景，不再全屏铺图。文案位置保持现有布局。
- 前端构建通过，本地浏览器确认右侧图片显示；未发布。

### 2026-09-14：首页背景切换为1.png

- 按用户要求将首屏背景替换为 `assets/backgrounds/2026-09-14/1.png`，保留暗色渐变与等比铺满。前端构建通过，本地浏览器确认横图显示正常；未发布。

### 2026-09-14：首页首屏背景图片

- 将指定素材 `assets/backgrounds/2026-09-14/2.png` 复制至前端 public 同名背景目录，通过 `landing.css` 的首屏伪元素显示；图片等比铺满，叠加暗色渐变并在底部衔接主题背景。
- 前端生产构建通过，本地浏览器确认图片、首屏文案与按钮正常显示；未发布线上。

### 2026-09-14：AI消息与附件按钮左对齐

- 消息容器600px上限包含padding，而输入区600px上限不包含外层padding，造成宽屏偏移。消息最大宽度补上两侧padding，移动端同步对应数值。
- Chrome实测AI消息与附件按钮left均832.296875px。本地生效，未发布。

### 2026-09-14：会话列表行内编辑

- 用户反馈重命名不应弹窗、头像应在列表编辑。已改为列表原位标题输入/头像入口，移除消息头像上传按钮；列表编辑按钮定位显示，正文padding维持原值。
- Chrome实际展开输入框并自动聚焦，无原生prompt；正文计算padding为16px 28.8px 40px，max-width600px居中。构建通过，未发布。

### 2026-09-14：聊天会话头像与标题编辑

- 聊天页AI头像可点击更换，会话列表独立按钮重命名。复用头像上传签名，新增会话PATCH；数据库使用用户/会话双条件更新已有列，不新增表。更新会话头像不改变账号头像。
- 权限/标题/前缀mock、后端编译及前端构建通过；Chrome本地控件可见。真实保存后刷新验收待完成，未发布线上。

### 2026-09-14：恢复语音NDJSON场景规划

- 按用户要求恢复语音adaptive的scene/text规划及解析；纯文字聊天仍普通输出。structured提示与普通提示分开，多行JSON兼容保留，页面只展示text。
- adaptive及额度回归通过，本地健康200，未发布。

### 2026-09-14：恢复聊天提示词，移除NDJSON依赖

- 四个聊天入口恢复统一日常口语规则，保留历史，剔除传入人设system；提示不要求scene或NDJSON。语音生成移除运行时decoder分支，普通文本边生成边分句合成，仍保留内部音频回放记录。
- adaptive及额度mock通过，本地健康200，未发布。

### 2026-09-14：无聊天提示词试用

- 注释planning_prompt注入；四个聊天入口过滤system/developer消息，语音接收普通文本并分句生成内部回放计划。保留历史与TTS设置；OCR等专用任务不变。
- adaptive/额度mock、编译、本地健康通过；测试按拼接text.delta校验普通文本，不能在分片SSE原文搜索完整句子。未发布。

### 2026-09-13：声音描述动态额度与指令预览

- 删除CosyVoice描述固定30字限制。voiceInstruction.ts按后端相同组合顺序预览整条指令并计算100单位预算，非ASCII保守按2；自动模式预览普通聊天四字基调，其他场景长度一致。
- 页面显示已用/剩余/超出单位；超限不截输入，禁用保存且保存函数防重入检查。恢复原始模式预算归零。模型切换和字段变化触发有效性更新。
- 新增动态额度回归：45汉字可用、增加特点超限、混合字符计数、组合顺序与重置；2/2通过，前端类型编译与构建通过。未发布。

### 2026-09-13：情绪选择提示与文本流解析容错

- 情绪处于auto时禁用属设计行为，已补充切换固定情绪的明确提示。
- 用户单次文本流失败日志未保留异常，无法追溯确切原因；重新调用文本模型成功。源码确认PlanDecoder逐行解析会拒绝合法的多行排版JSON，已按完整JSON对象解析并兼容流式碎片/连续对象，逐字符回归通过。
- 前端空正文曾伪造“我在听。”再报错，已删除该成功占位及其写库路径；新增仅含请求ID、异常类型及已解析段数的日志，不记录聊天正文。后端adaptive回归、前端构建通过，历史失败根因仍未确认。

### 2026-09-13：恢复CosyVoice声音描述及pitch，支持原始模式

- 恢复情绪、年龄感、磁性/甜美等偏好，合成为不超过100单位的instruction；新增独立pitch 0.5–2。use_defaults保存于既有voice_style JSON，恢复默认后只发送text/voice/format，修改任一项退出默认模式。前端提示需保存，新语音生效。
- HTTP/SSE测试验证自定义参数、volume=0、原始模式完全省略字段；adaptive/额度回归和前端构建通过。真实当前音色两种模式均返回非空PCM，本地健康200；未发布。

### 2026-09-13：CosyVoice语速与音量设置

- 按音色模型显示CosyVoice专用rate/volume配置，旧模式、情绪和声音维度留在Qwen分支。复用voice_style JSON保存，新增volume范围验证；流式语音、直接朗读发送rate/volume，原始指令仍关闭，PCM仍按默认22050Hz。
- 参数测试验证volume=0不回退默认值，语音计划包含音量并支持回放；adaptive、HTTP/SSE、额度回归及前端构建通过。未发布。

### 2026-09-13：CosyVoice原始默认参数试听模式

- 用户要求前端保留、后端忽略全部声音调节。CosyVoice公共HTTP/SSE仅传text/voice/format，省略语速、采样率、指令；无音量、音调或语言覆盖。PCM播放及持久化元信息统一官方默认22050Hz，额度预留按1倍，防止采样率错配变速。
- 精确请求字段、PCM时长、adaptive回归通过，本地健康200。前端保留原样，其声音设置暂不影响CosyVoice。未发布。

### 2026-09-13：关闭CosyVoice声音指令并复核参数

- 按用户要求，CosyVoice的非流式和SSE公共入口均省略instruction，计划记录置空，旧记录重新合成也不会发送；语速与采样率保留，Qwen不变。UI说明指令类设置暂不用于CosyVoice。
- 官方HTTP参数核对：volume默认50/范围0–100、rate默认1/范围0.5–2、pitch默认1/范围0.5–2；合成language_hints与复刻语种提示不同；方言通过instruction控制。参数现状已写入接入方案。
- HTTP/SSE与adaptive回归通过，本地健康200。未发布。

### 2026-09-13：CosyVoice语音聊天有文字无声音

- 真实CosyVoice音色的流式请求HTTP 200但只有文字；直接复现供应商HTTP 400、Engine 428。同音色不传指令及短指令均返回PCM，证实长声音指令超限。
- 官方error-code说明CosyVoice instruction最多100字符单位，汉字按2计算。此前未适配该限制。speech_plan改用精简场景指令；qwen_tts公共HTTP/SSE入口按100单位限制，非ASCII保守按2，覆盖直接朗读和聊天。Qwen不受影响。
- HTTP参数和adaptive回归通过，包括中文、英文及混合长度边界；真实音色短指令已返回非空PCM。未发布。

### 2026-09-13：CosyVoice-v3.5-plus接入

- 按官方target_model必须一致的约束，新复刻默认CosyVoice，旧Qwen和默认系统音色保持原路由；增加CosyVoice自适应语音允许项、合成前就绪检查、去除Qwen专属标签，设置页说明拟声限制。
- 成本统计按CosyVoice 1.5元/万字符、Qwen Plus 1.4元/万字符分别累计，管理端修正单一费率提示。
- adaptive/HTTP参数/额度mock通过，两端构建、后端编译及本地健康通过。新增测试插入CosyVoice调用后旧回放断言错误比较了上一条CosyVoice请求，已改为比较原始Qwen调用并通过。
- 未创建或删除真实音色，真实CosyVoice试听待验收，未发布。详见plan/2026-09-13_QwenPlus与CosyVoice接入调研.md。

### 2026-09-12：音色设置面板同步自动表达策略

- VoiceProfileForm在自动语速/情绪模式禁用固定语速、情绪基调、场景和补充描述，并展示原因；保留原值，切换手动可继续编辑。使用与后端一致的旧配置模式回退。
- 拟声旧auto值显示为关闭，取消不存在的自动少量选项；说明指定效果每轮最多一次、风格标签优先于基调。提示改为整轮语境调整及新语音生效。
- 前端类型检查与生产构建通过，本地源码已更新，未发布。

### 2026-09-12：语音场景情感与整轮稳定表达

- 首轮关闭自动表达后用户反馈仍缺少情感。改为LLM选择六类语境，后端映射克制的声音指令和0.96–1.04语速；首段确定整轮风格，后续段落沿用，手动设置优先。自动模式不再叠加旧自由声音描述与播报/广告场景，避免指令冲突。
- 口语提示要求回应具体事情、自然情感、不编造经历，普通短回答合成一个完整段落。自动拟声保持关闭，不恢复角色人设注入。
- 修改backend/speech_plan.py、backend/app.py；现有test_adaptive_speech.py通过，新增覆盖场景映射、跨段稳定、手动覆盖和非法场景回退；编译通过。此为本地实现与mock验收，实际声音自然度待试听，未发布。

### 2026-09-12：语音聊天去人设与自然表达

- 用户反馈语气刻意、语速声调不自然。源码中角色compiled_prompt与逐句表演规划叠加，自动每句变速和情绪/拟声可能加重表演感；实际听感原因尚待试听确认。
- 语音自适应入口移除compiled_prompt注入，保留会话历史及音色选择，改为日常口语规则。自动模式固定1.0语速、无情绪和拟声标签、不使用模型逐句direction；手动参数保留。规划按1到3句完整语意段输出，减少短句切割。
- 官方依据：百炼非实时语音合成的Qwen-Audio-TTS指令与标签文档；上述为应用默认策略调整。文件：backend/app.py、backend/speech_plan.py。
- 验证：test_adaptive_speech.py无外部调用回归通过，覆盖角色词不注入、自动标签过滤、手动覆盖及原有回放/权限/额度/取消；后端编译通过，本地reload服务健康200。新生成语音生效；旧语音回放保持原记录。未发布，主观听感待用户试听。

### 2026-09-12：裁剪选区与净化试听时长不一致

- **现象**：裁剪面板选中6.9秒时，页面下方仍展示此前按9.4秒原音生成的DeepFilterNet净化试听，容易误认为降噪改变了时长。
- **根因**：裁剪选区只有点击“确认裁剪”后才会导出新WAV；裁剪面板打开期间，旧净化结果和净化按钮仍可见，展示了两个不同版本的音频状态。
- **修复**：裁剪期间隐藏旧净化结果，净化按钮保持可见但禁用并显示“确认裁剪后去除背景噪声”，同时禁止创建音色；确认后复用 `renderAudioFile` 清空旧上传/净化对象，再按新裁剪WAV重新净化。取消裁剪则保留原音及其原有净化结果。
- **验证**：新增源码回归断言，目标测试10/10、类型检查和生产构建通过；未发布线上。

### 2026-09-12：DeepFilterNet上传参考音频降噪接入（待浏览器最终验收）

- 官方DeepFilterNet 0.5.6 Linux amd64 musl静态二进制按固定SHA-256进入生产镜像，并附带校验后的MIT/Apache-2.0许可证；未引入PyTorch。完整ffmpeg会增加约466MiB依赖，已改用浏览器 `OfflineAudioContext` 原生转换48kHz单声道16-bit WAV。
- 新增账号隔离的 `/api/uploads/denoise`：OSS下载上限10MiB、用户/IP限频、单进程并发1、低优先级异步子进程和120秒超时；净化文件写回私有OSS，错误不暴露签名URL或内部路径。
- 克隆弹窗增加净化试听及原音/净化音选择，净化完成默认选中净化音，用户可切回原音；前端状态不持久化到Local Storage。
- 后端模块/归属/OSS闭环、声音槽位与额度回归、前端目标测试10/10、两端编译/构建和真实amd64镜像均通过。15秒合成音频在模拟amd64下约25秒、峰值约66MiB。
- 本地arm64开发二进制按SHA-256安装并接入启动脚本；临时账号真实HTTP闭环完成6秒上传、降噪和试听下载，净化文件约560KiB。OSS源/净化临时对象及测试账号全部清理，未调用百炼。
- 尚未发布；当前浏览器账号音色槽位已满，真实用户音频A-B试听、百炼克隆和生产原生x86性能仍待验收。

### 2026-09-12：移除Google Fonts阻塞与克隆音频降噪选型

- **字体现象**：公网聊天页请求 `fonts.googleapis.com`，经本地代理耗时约26秒，拖慢DOMContentLoaded；页面本身已有系统字体回退，无需依赖远端字体。
- **字体修复**：删除Google Fonts预连接和样式表，设计令牌改为Songti/PingFang/Microsoft YaHei/Noto CJK等系统字体栈。目标测试10/10、类型检查和生产构建通过；dist与浏览器DOM无Google字体地址。尚未发布线上。
- **降噪选型**：首选MIT/Apache-2.0的DeepFilterNet做克隆参考音频上传后的48kHz文件异步清洗；RNNoise适合未来实时前处理，MIT noisereduce作为频谱门基线，Apache-2.0 ClearerVoice-Studio仅考虑独立重型Worker。
- **产品约束**：原音和净化音必须A-B试听并由用户确认；过强降噪可能损伤音色特征。不得在FastAPI请求线程或20ms实时音频链路中同步运行模型。

### 2026-09-11：线上OSS直传被CORS预检拦截

- **现象**：公网 `http://47.114.50.170/chat` 上传克隆声音时，浏览器对 `voice-references/*` 签名URL的 `OPTIONS/PUT` 被OSS拒绝，控制台提示缺少 `Access-Control-Allow-Origin`，页面显示 `Failed to fetch`。
- **根因**：Bucket `weiguang-dev-20260823` 的唯一CORS规则只允许 `http://127.0.0.1:5173` 与 `http://localhost:5173`，没有公网IP来源。应用RAM密钥只有对象操作权限，不能读取或覆盖Bucket CORS。
- **修复**：通过阿里云主账号控制台编辑原规则，追加精确来源 `http://47.114.50.170`；保留 `GET/PUT/HEAD`、允许Headers `*`、暴露 `ETag/x-oss-request-id`、缓存600秒和 `Vary: Origin`，未开放来源 `*`。
- **验证**：公网来源的真实OPTIONS预检返回200、允许来源和 `content-type`；使用与业务相同的签名Content-Type执行PUT返回200并带正确CORS响应头，临时对象随后删除。无需重新发布应用代码。
- **后续约束**：启用正式HTTPS域名时必须将 `https://weiguang.chat`（以及实际使用的www来源）加入规则；Origin包含协议，HTTP IP规则不能覆盖HTTPS域名。

### 2026-09-11：生产发布包单入口脚本

- 新增 `scripts/publish-production.zsh`，单命令完成用户端与管理端检查/构建、后端编译、`linux/amd64` API 镜像构建、单个发布包和 SHA-256 生成；不包含 `.env`、密码、Key、原始卡密或数据库。
- 包内 `deploy/apply-release.sh` 在服务器保留现有 `.env.production` 与 PostgreSQL 数据卷，发布前导出数据库备份，只重建 API 服务，并为镜像、管理端静态文件、Compose 和 Nginx 配置保留失败回滚路径。
- 完整本地打包验证通过：用户端目标测试 10/10、管理端测试 1/1、两端类型检查/构建通过、镜像为 amd64；生成的验证包约 79 MiB且清单完整。
- 已配置项目专用 Ed25519 SSH 密钥：本机配置别名 `weiguang-prod` 并绑定 `root@47.114.50.170`，服务器只追加公钥、不覆盖已有授权。`DEPLOY_TARGET=weiguang-prod ./scripts/publish-production.zsh` 于2026-09-11完成首次自动生产发布 `20260911T151342Z`。发布前数据库备份约210 KiB，API单服务重建、Nginx配置、首页/聊天/管理端/健康接口均通过；PostgreSQL容器和数据卷未重建。400px克隆声音入口可见，管理端刷新保持登录，OSS预检仍为200。

### 2026-09-11：手机克隆声音入口与管理端刷新竞态

- **现象**：480px 以下聊天页顶部主动隐藏 `.cnav__voice`，手机无法进入克隆声音；管理端刷新偶发回到登录页。
- **根因**：手机样式明确写了 `display:none`。管理端路由守卫和 `App.vue onMounted` 同时调用 `ensureReady()`；第二个调用在 `isBootstrapping=true` 时提前返回，可能在首个 `/api/auth/me` 成功前按空 profile 重定向。
- **修复**：手机端恢复紧凑的“克隆声音”按钮；删除管理端 `App.vue` 重复初始化，只保留路由守卫等待 Session 恢复。本地启动脚本的管理端探活和输出地址统一为 `/admin/`。
- **验证**：400px Chrome 中按钮可见且可打开克隆上传弹窗；管理端鉴权源码回归、两端类型检查和生产构建通过。本地 `http://127.0.0.1:5174/admin/` 已由 launchctl 启动，普通有效 Session 刷新成本页后保持原路径且不跳登录页；管理端修复已同步发布线上 `/admin/` 并完成静态资源与健康回读。
- **测试边界**：用户端目标回归 10/10 通过；全量测试中既有 `chatImportClose.test.mjs` 一条 mock 状态测试失败，未被本次修改触及。

### 2026-09-11：管理端 TTS 零数据说明与成本表对齐

- **现象**：成本页 TTS 显示 0 字 / 0 秒，套餐平均单次文本成本的表头与数据列视觉错位。
- **核对**：线上当前只有 1 条已完成 `ai_reply` 用量流水；对应会话是一次纯文字问答，没有 `ai_voice_seconds` 流水，因此 TTS 为 0 是真实数据，不是漏记。纯文字聊天按产品设计不调用 TTS。
- **根因与修复**：`.data-table th` 的左对齐选择器优先级高于通用 `.text-right`，表头没有执行右对齐；改为表格单元格限定选择器，使表头与数据统一。TTS 为零时明确显示“尚未发生语音合成 · 纯文字回复不计入”。
- **成本口径**：北京地域 `qwen3.5-flash` 当前按输入 0.2 元/百万 Token、输出 2 元/百万 Token，`qwen-audio-3.0-tts-flash` 按 1 元/万字符估算；优惠与免费额度不抵扣，最终账单以百炼控制台为准。
- **验证**：管理端类型检查和生产构建通过，新静态包已发布；线上成本页、入口脚本与健康接口正常。

### 2026-09-11：运营管理后台公网部署

- **部署**：`frontend-admin` 按 Vite 官方嵌套路径方式构建为 `/admin/`，由宿主 Nginx 直接提供静态文件；`/admin` 重定向至 `/admin/`，内部路由通过 `try_files` 回退管理端 `index.html`，不影响用户端 SPA 与 `/api/`。
- **权限**：移除线上不存在的开发管理员 ID，将线上唯一已注册账号设为唯一管理员；后端白名单数量与数据库匹配管理员数量均为 1。未创建第二套账号或保存明文密码。
- **验证**：`/admin/login`、管理端 JS 资源与深层路由返回正常，公网健康接口保持 200；Chrome 已打开并检查管理后台登录页。
- **边界**：当前仍为公网 HTTP，账号密码传输不具备 TLS 保护；正式运营前必须启用 HTTPS。

### 2026-09-11：线上兑换码库存缺失与 SPA 刷新 404

- **现象**：公网新注册账号提交链动小铺新购 Plus 卡密，API 连续返回 400“兑换码无效或不可用”；Safari 直接刷新 `/pricing` 又返回 `{"detail":"Not Found"}`。
- **根因**：ECS 首次部署创建了全新 PostgreSQL，仅执行结构迁移，没有迁移本地权威库中已上传到链动小铺的未兑换卡密哈希。线上 `redemption_batches=0`、`redemption_codes=0`，而目标码在本地为 `issued/plus_30d/active`。StaticFiles `html=True` 不为未知 SPA 路径自动回退 `index.html`。
- **修复**：事务迁移两个有效批次的 27 张未兑换哈希（Plus 17、Pro 10），不迁移原始码、旧用户、已兑换/撤销码和历史授权；目标账号为线上唯一账号且处于 `free/active`，使用同一 `BillingStore.redeem_code` 原子事务完成已购码兑换。Nginx 将 `/api/` 保持真实状态码，其他路径 404 重写至 `/index.html`。
- **验证**：目标卡密回读为 `redeemed`；subscription 及 grant 均为 Plus，截止北京时间 2026-10-11 16:35。Safari 刷新后显示“当前为付费套餐”；`/pricing` 刷新正常，`/api/health` 仍为 200。剩余库存可继续线上兑换。
- **后续约束**：任何新环境首发前必须迁移仍在外部渠道售卖的 `issued` 卡密哈希，或从线上库生成新库存；不得只迁表结构。商品说明仍有正式网址和批次截止日期占位符，需在链动小铺商品后台另行修正。

### 2026-09-11：阿里云 ECS 公网 IP 部署

- **部署**：实例 `i-bp1e515soalhovys9z98` 使用 Docker Compose运行 FastAPI + PostgreSQL；服务器已有 Nginx通过回环端口 `127.0.0.1:8080` 代理。未安装宝塔。公网入口 `http://47.114.50.170/`。
- **配置**：HTTP阶段使用 staging、非Secure Cookie与精确IP Origin；百炼/OSS生产参数和随机数据库密码随加密包传输，未显示在文档或日志摘要中。域名两条A记录已存在，但暂不启用域名和HTTPS。
- **排障**：Docker官方RHEL仓库在ECS上TLS失败，按阿里云官方Alibaba Cloud Linux 3文档改用 `mirrors.cloud.aliyuncs.com` 与 releasever适配器。服务器拉Docker Hub超时，改为本地构建并加密传输官方amd64镜像。QEMU下esbuild出现`lfstack.push`/EPIPE，改为本机先构建前端dist，再由 `deploy/Dockerfile.prebuilt` 构建纯运行镜像。
- **传输**：Workbench上传会明文暂存其OSS，改为AES加密后经项目私有OSS临时中转；服务端下载、解密、SHA-256校验、Docker load成功后，两个临时OSS对象均已删除。
- **验证**：API/PostgreSQL均healthy；公网首页、健康接口、套餐接口200。Chrome验证首页、登录弹窗、3D圆环和图片加载正常且console error为空。健康响应为百炼LLM/TTS和阿里云OSS、missing空；套餐为free/plus/pro。未创建生产测试用户，实际登录/付费未写数据验证。
- **资源抽样**：API约172MiB、PostgreSQL约29MiB，整机约1.2GiB available，系统盘约6/40GiB；空载快照不能推导并发容量。正式运营前完成备案、HTTPS、production和Secure Cookie切换。

### 2026-09-10：故事卡旋转圆环

- 六张 mock 卡由横向滚动改为同一场景中的圆周等距排列；复用透明卡体、主题/珍珠银、背面故事，支持拖动整个圆环、方向键/箭头/圆点选择、自动旋转和当前卡翻面。反光改用场景相机世界位置。
- 新增 storyRingLayout.js 与 story-ring.test.mjs；半径、等距、环绕索引及原材质测试通过，构建通过。Chrome 拖转及当前卡切换已检查，390px 无横向溢出且单画布 ready；视觉验收待定。
- 尺寸变化触发 frame(0) 时可能出现负 dt，已用单调时间条件保护，防止插值反向爆增；未修改后端和用户已有文案。

### 2026-09-09：删除独立扫光，轮播驱动材质视角

- 用户澄清需要卡片自身反光，删除上一轮新增的前后白光网格和 sweepTime 计时，不再周期性生成扫光。
- 根据卡片在轮播可视区的位置调整传入原有镭射 Shader 的观察方向；旋转和轮播共用同一材质视角响应，珍珠银虹彩保留。
- 材质检查覆盖观察方向随位置变化、仅保留一个 Shader 网格、无 sweep uniform，检查通过；Chrome 播放无渲染错误。

### 2026-09-09：可见扫光与真正珍珠银

- 用户反馈此前扫光不可见：位置驱动太慢、透明度低且位于图片后方。新增独立前后扫光层，轮播播放时间推进约 3.8 秒一个周期，正面亮带位于图片上方，暂停/离屏不推进时间。
- 珍珠银恢复原实验 cosine 三通道虹彩与银色金属边；增加主题配色选项，烫金保留独立金色表现。透明卡底和背面直印保持。
- 构建与 `node frontend/tests/holo-material.test.mjs` 状态检查通过；Chrome 连续画面已观察到亮带从无图卡扫过、照片上方也出现高光，虹彩可见，无 console error。

### 2026-09-09：透明卡面、背面直印与轮播流光

- 用户希望去掉实色卡底和背面纸张：挤出体仅保留金属侧边，正反面使用低透明度流光；移除卡片周围径向底光。故事 CanvasTexture 清空底色，仅保留浅色字与装饰线，以透明材质贴合背面。
- 将卡片在轮播可视区中的相对位置传入 Shader travel，移动过程中高光带位置随之变化，保留手动旋转和光泽强度。
- 构建通过；Chrome 实测背面无纸底、文字可读，正面无实色色块，console error 为空，已开启轮播供视觉验收。

### 2026-09-09：轮播整像素顿挫与圆角文字牌

- 现象：低速轮播有跳动感。源码确认 22px/s 位移经 Math.floor 量化为整像素；Three.js r180 WebGLRenderer.setViewport 还会按物理像素 round，导致连续帧停顿/跳像素。
- 修正：保留 remainder，将亚像素位移通过 PerspectiveCamera.setViewOffset 补偿 viewport 取整；卡片布局读取改到 ResizeObserver，避免逐帧读取 12 个 DOM 边界。标题和底部文字纹理采用 roundRect 裁剪+透明材质。
- 验证：DPR 1/1.5/2 的 120 帧位移数学检查通过，Chrome 播放时 scrollLeft 推进、圆角可见、console error 为空。未获得可靠实时帧率采样，不宣称固定帧率或性能提升百分比。

### 2026-09-09：11 套卡片独立搭配色

- 卡片配色与页面主题做冷暖/明暗搭配，不再直接复制背景色；新增 storyCardPalettes.js，独立配置卡底、流光、金属边、纸面与墨色，故事仍在背面。
- 示例：黑底搭暮紫香槟、青蓝底搭赤陶亚麻、酒红底搭月青珍珠。弱化流光，深色正文配浅色纸面。构建通过，11 组文字色对比度计算均超过 4.5:1；Chrome 原色/青蓝搭配已检查。

### 2026-09-09：故事背面与全卡配色

- 根据用户澄清，完整故事移到背面固定文字层，正面保留图片/标题/作者；此前正面正文方案被替代。
- 消除 Shader、边框、金属卡体、星粒的固定金银/彩虹色，改用首页 bg-soft/theme-base/light，材质选项不再覆盖主题。Chrome 实测炽焰红及云白青蓝，卡体与背面均联动、文字朝向正确，无 console error；构建通过。

### 2026-09-09：全息故事卡主题与卡面文字

- 展示舞台改为透明并复用主题底光；3D 文字贴图监听主题切换，使用 bg-soft/text/light 统一背景、字色与装饰线。原先固定浅色舞台不适配首页主题的问题已修正。
- 作者、分类、标题、完整 mock 正文统一写到卡面；删除卡下重复文案和阅读按钮，无图卡扩大正文区域，操作控件保留。回车或双击可展开全文，无新增持久化或 API。
- Chrome 实测马尔斯绿切换后舞台与卡面同步配色；最终视觉验收待用户确认。

### 2026-09-09：首页全息卡改用实验原版 3D 实现

- 首轮 mock 使用平面 Shader + CSS 景深，未达到用户要求的原版效果。改为直接提取实验 App.vue 的卡体、原始镭射 Shader、灯光、相机、透明人物、浮动标签和星粒，新增 createHoloStoryScene.js。
- 首页共享一个 renderer 渲染各故事场景；6 条 mock 保留，第一张为同素材同参数的星辉对照卡；无图故事使用立体文字层。展示台沿用原版浅底，恢复拖转/翻面/自动转动/复位/材质/层次/光泽控件。
- 类型检查与构建通过；Chrome 实际检查人物和标签景深、拖转及背面渲染。没有执行像素差分，不声称像素级完全相等；最终视觉验收待定。未接入投稿或审核 API。

### 2026-09-09：首页故事全息卡 mock

- 首页评价轮播替换为 6 条明确标注的示例故事：3 条带图、3 条纯文字，普通配图和透明插画分别展示。未来业务为用户投稿、可选图片、管理员审核后展示，本轮未实现该后端流程。
- 新增 HoloStoryCarousel.vue，复用现有素材及实验镭射算法，一个 Three.js 画布绘制可见卡片；HTML 文字与 CSS 景深，支持暂停、切换、原生横向滚动、全文 modal、Esc 关闭及资源释放。
- 类型检查/构建通过；Chrome 桌面与 390px 无页面横向溢出，图片正常、画布一个、无 console error；全文 modal 和 Esc 已实测。移动触屏完整手势和 WebGL 故障降级未实测，用户视觉验收待定；图片原图约 3.95MB，正式发布需压缩。

### 2026-09-09：Vue与Three.js全息卡实验

- 独立实验目录 three/ 新增 App.vue，程序化圆角卡体、独立星空镭射Shader、透明人物、文字平面与星粒；支持拖转、翻面、材质、层次及光泽。沿用图片但不使用旧整卡作背景，消除重复人物；标签前移以避免遮挡。
- Vite构建通过；浏览器实测拖转、正反面、材质和滑块，console error为空，390px无横向溢出。未使用Blender，未接入主业务；人物仍为透明平面。预览 /three/dist/，旧版文件保留。用户视觉验收待定。

### 2026-09-09：多层全息卡网页实验

- **实现**：在不修改单图版的前提下新增 layered.html；卡底、透明人物、标题牌、说明牌、星光和镭射层使用不同 Z 轴景深，指针移动同步改变旋转与光点位置。继续使用原生 HTML/CSS/JavaScript，无 Blender、Three.js 或新增依赖。
- **素材**：人物提取路径再次产生棋盘格 RGB，按既有排障记录改为原生透明画布生成；最终人物素材为 1024×1536 RGBA PNG。
- **验证**：浏览器桌面视图中人物和标签明显浮出卡底；指针移动后旋转/光点 CSS 参数变化；390×844 视口无横向溢出。旧版 index.html 保留，分层页提供直接返回入口。

### 2026-09-09：透明全息卡网页实验

- **实现**：使用 GPT Image 生成带真实 Alpha 通道的“微光”全息卡 PNG；独立网页以原生 CSS mask、透视变换和少量指针事件实现倾斜、流光与景深错觉，不接入主 Vue 路由、不新增依赖。
- **问题与根因**：两次“从原图去背景”都把棋盘格画进 RGB，无法作为透明素材；改为从透明画布原生生成后得到 RGBA。浏览器首轮中等宽度检查发现卡牌右侧裁切，原因是卡牌宽度按视口而非可用布局空间计算。
- **修复**：拒绝假透明结果并用 `sips` 验证 Alpha；将卡牌宽度限制为 `min(460px, 42vw)`，移动端单独使用 `min(360px, 86vw)`。
- **验证**：HTML解析和内联JavaScript语法检查通过；浏览器实测桌面卡牌完整显示，指针移动后倾斜/流光参数变化；390×844视口无横向溢出。文件位于 `marketing_assets/2026-09-08/holo-card-experiment/`。

### 2026-09-08：首页全局撞色主题切换

- **实现**：保留原始黑底暖白“微光原色”，并逐张读取抖音《世界级经典撞色合集》的 10 组 HEX 配色，复用 `tokens.css` 将其映射为可读的深色全局主题；首页导航增加固定向下展开的项目内配色菜单与双色色样，支持 Escape 和点击外部关闭，粒子、背景、按钮、卡片和强调色同步变化。默认“微光原色”，当前单页会话内跨页面保持，不写入 `localStorage`，刷新恢复默认值。
- **验证**：主题专项测试和前端生产构建通过；Chrome 实测原始主题和 10 套新增主题切换正确，进入套餐页后保持主题；1470px 与 390px 均无横向溢出，首页 axe 明确违规 0。全量旧 `.mjs` 回归 18/19，通过项包含本次主题；唯一失败为既有 OCR 声音应用测试读取未定义 `id`，与本次修改文件无关，未扩大范围处理。

### 2026-09-07：聊天输入长度限制

- 聊天输入框使用原生maxlength限制2,000字符，达到1,600字符后显示计数，满额变色提示；覆盖手动输入和文本粘贴。前端生产构建和针对性源码测试通过。

### 2026-09-05：本地测试额度补充

- 按用户明确要求将当前管理员本期截图导入用量通过可审计负向调整恢复为0/10；保留所有导入记录。新增迁移018支持用户维度extra_limit，为当前账号增加1个音色槽位，现为1/2、剩余1；保留现有克隆音色和Plus套餐其他额度。配额原子性测试与健康检查通过。

### 2026-09-05：音色选择胶囊样式

- 将光球区原生小下拉框改为带麦克风图标的半透明胶囊，统一圆角、深色选项、悬停和焦点反馈，隐藏系统蓝色描边；保留原生select语义和自动保存逻辑，不增加自定义菜单代码。

### 2026-09-05：聊天细节与音色命名

- 聊天列表标题与导入按钮统一40px行高和垂直基线；音色下拉对旧时间戳文件名显示为“克隆音色N”，新克隆允许填写24字名称并持久化到原reference_filename显示字段；朗读按钮视觉尺寸缩至34px且hover改为弱背景；移除AI名称行。Vue生产构建通过。

### 2026-09-05：聊天入口与音色选择收敛

- 顶部移除导入图片和新对话；聊天列表标题右侧增加“＋ 导入”，点击按新会话方式打开OCR，同时审核页仍可改选已有会话。移除光球下方全屏语音入口，替换为克隆音色下拉框，选择即自动保存。Vue构建和11项界面回归通过。

### 2026-09-05：用户端改为零配置自动陪伴

- **问题**：角色工坊、MBTI、依恋类型、声音画像、完整Prompt和纠偏类型把内部实现转嫁给普通用户，造成配置负担。
- **改造**：用户端只保留聊天、截图导入、会话和声音克隆。OCR审核后“确认导入并自动学习”自动更新当前角色的人设、记忆、称呼及声音画像；隐藏所有内部画像表单和单独蒸馏按钮。声音克隆成功自动设为当前音色。
- **边界**：复杂结构、快照、纠偏和Prompt后端能力保留，但普通产品入口不暴露；自动分析仍经过称呼质量门、标签白名单和用户归属校验。
- **验证**：compileall、人设质量测试、用户端构建及11项界面回归通过。

### 2026-09-05：三代理上线整改与主线程复验

- **移动/无障碍**：手机聊天新增会话/聊天/语音三视图及核心会话操作；390px聊天宽390px、输入可见，桌面双栏不变。允许缩放、补main/H1、44px消息按钮；首页/聊天/全屏语音/套餐/管理登录axe明确违规0。
- **后端/生产**：统一版本化advisory-lock迁移器解决多Worker死锁；修复语音取消重复aclose；数据库限流覆盖登录/注册/上传/兑换；用户注销本地级联并报告远端pending；安全头、生产隐藏docs；Docker/Compose/Nginx/TLS模板和备份恢复脚本落地。Docker镜像真实构建成功，生产模式健康/安全头测试通过。
- **信任/体验**：隐私、协议、数据删除页可达；两步注销；普通声音设置隐藏完整Prompt；OCR称呼质量门并清理当前“欲.”污染；购买售后说明补齐；两端依赖审计0且管理端lockfile生成。
- **完整验证**：15个后端脚本、用户端19项前端测试、两套构建全绿；移动三视图及核心按钮浏览器实测；生产Compose结构解析通过。未消耗OCR、未支付、未执行真实远端删除。
- **测试污染事故及恢复**：旧`test_admin_endpoints.py`错误复用真实管理员ID，覆盖邮箱/密码哈希并遗留测试账号。已改随机管理员+atexit清理和权限恢复；清理6个明确测试账号，从PostgreSQL WAL恢复两名管理员原邮箱与密码哈希。复跑测试后账号ID/邮箱/哈希摘要保持不变。临时WAL副本已删除，未读取或输出明文密码。
- **范围与已验收项补充**：用户确认链动小铺真实付款、续期和退款均已测试完成；从上线剩余项移除。OCR长图明确不支持，继续在上传页禁止并引导裁成多张，不开发自动切片。
- **仍待外部验收**：真实域名证书和生产Compose启动、备份恢复演练、真实OSS/百炼注销清理、邮箱验证/找回、1/5/10/25并发及7天灰度。

### 2026-09-05：用户头像统一为个人资料来源

- **需求**：OCR不再上传用户侧头像；用户打字和语音消息都显示头像，并与个人资料一致。
- **实现**：OCR审核移除右侧我的头像上传，只保留左侧对方头像作为会话AI头像。所有user消息统一读取账号avatar_download_url，不区分打字、语音转写或OCR导入；无图/加载失败显示昵称或邮箱首字。确认导入不再把right_avatar写入用户消息元数据。
- **验证**：SFC规则回归确认无右侧入口且所有user消息使用账号头像；Vue生产构建通过。浏览器实测无头像账号的当前20条用户消息全部显示默认头像，0条遗漏；AI会话头像隔离保持通过。

### 2026-09-05：账号头像与注册校验

- **实现**：个人中心增加头像上传/更换，JPG/PNG/WEBP且最大5MB；私有OSS对象按用户目录隔离，app_users只保存对象键，资料读取续签链接，顶部账号入口显示头像。
- **注册校验**：前端邮箱结构、密码四项实时提示和确认密码；后端同样校验邮箱，注册密码至少10位且包含字母/数字/特殊字符，重复邮箱409。登录保留原校验以兼容已有8位账号。
- **涉及文件**：迁移015、auth_validation.py、app/app_data_store/OSS Provider、AccountDialog/AuthDialog/AppNav及相关Store/API/类型/样式。
- **验证**：真实PostgreSQL回滚测试覆盖合法/非法邮箱、弱密码、重复邮箱、头像所有权和持久化；前端规则测试、compileall、生产构建、服务健康检查通过。未向当前账号写测试头像，真实上传回显和新账号浏览器流程待用户使用时验收。

### 2026-09-05：纠正 AI 头像跨会话复用

- **用户反馈与根因**：未上传头像的“新的聊天”显示了“微光对话”的图片。此前将导入头像绑定到共享角色，并按activePersona渲染，错误扩大了头像作用范围。
- **修复**：普通AI回复只读取activeConversationId对应会话的avatar_download_url；空值/失败显示首字默认头像，不回退共享角色图片。导入审核去掉全局角色头像同步选项，保留已有按目标会话保存导入头像的链路。已按用户意图撤销上次给“欲.”添加的全局头像绑定，原图及会话头像保留。
- **验证**：数据库确认“新的聊天”无头像、“微光对话”有头像；浏览器切换实测前者5条AI消息均默认头像、图片0张，后者14张AI头像全部加载成功，检查后返回新的聊天。SFC回归与Vue构建通过。
- **说明**：本条更正此前“导入头像绑定角色”的展示设计；AI聊天头像现以会话为准。

### 2026-09-05：导入头像绑定角色并显示于 AI 回复

- **根因**：ChatView仅为imported消息渲染头像；导入左侧头像未绑定角色，普通AI回复只有名称。
- **实现**：迁移014给personas增加avatar_object_key。角色更新API可传avatar_import_id，由后端读取同用户批次的左侧头像并在角色行锁事务中绑定；列表、详情、激活及更新响应签发avatar_download_url。审核页增加独立头像同步勾选；自动生成角色带入左侧头像。普通AI回复显示当前角色头像，缺失/加载失败用名字首字回退。
- **本次绑定**：按用户明确要求，将其已有已确认导入批次21的左侧头像绑定至当前角色“欲.”；数据库回读确认绑定、原persona与voice_id未变化，签名URL已生成。
- **验证**：头像独立于声音设置的确认流程回归通过；PostgreSQL回滚测试验证绑定不覆盖其他字段及跨用户拒绝；自适应回归与Vue构建通过。浏览器需刷新获取最新绑定，未重新上传或调用OCR。

### 2026-09-05：开始提取无响应，后端重启被旧单会话索引阻塞

- **现象**：已选择截图，点击开始提取无进度；8080健康检查超时。启动日志显示 `UniqueViolation: uq_chat_conversations_active_user`。
- **根因**：各Store启动会重放backend迁移005；多会话迁移012删除了旧唯一索引，但005再次创建它，在已有多个会话时失败，后续012无法执行。前端先等待额度查询再显示忙碌状态，且查询没有超时，表现为按钮失效。
- **修复**：从005移除已被012淘汰的唯一索引创建语句，保留012对老数据库的移除逻辑，不修改聊天数据。提取流程在额度查询前显示进度并阻止重入；额度查询设置10秒超时，失败恢复上传页并保留已选图片，额度不可用时不继续上传。
- **官方依据**：[PostgreSQL CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)：UNIQUE创建时会检查已有重复值；IF NOT EXISTS仅在同名索引已存在时跳过，不解决旧约束被后续迁移移除再创建的问题。
- **验证**：`scripts/test_multi_conversation_bootstrap.py`在隔离schema中执行新安装→多会话→两轮重复迁移成功，事务完整rollback；SFC测试覆盖等待进度、重复点击、额度失败重试和额度耗尽。Vue构建通过，项目启动脚本确认FastAPI及前端正常。未重新执行用户OCR。

### 2026-09-05：OCR 声音画像应用到当前角色

- **现象与根因**：继续当前会话仅导入消息，声音画像仅保存在导入批次；用户以为确认导入会更新当前角色声音。
- **修复**：审核页显式显示“确认导入时，将声音画像应用到当前角色”复选框和目标名称，有当前角色时默认勾选，可取消。确认前保存批次，再通过既有角色更新API仅更新voice_style，成功后确认导入并刷新角色Store。保存修正仅保存批次，自动生成角色仍应用到新角色。应用成功但后续导入失败时保留应用成功提示。
- **数据保护**：后端对角色归属和VoiceProfile参数校验，行锁读取后合并声音字段，保留其他人设、记忆和音色；更新失败阻止继续确认，忙碌时声音表单禁止编辑。
- **验证**：实际SFC逻辑测试覆盖默认勾选、保存顺序、应用失败、取消勾选；PostgreSQL事务回读覆盖字段合并、其他字段不变、越权拒绝，测试全部回滚；自适应语音回归和Vue生产构建通过。

### 2026-09-04：截图导入页增加长截图提示

- **处理动作**：在截图上传区域下方增加“禁止上传长截图”警示，说明长截图可能因内容过长、缩放后文字过小或请求超时导致识别失败，并建议先裁剪成多张正常比例截图。
- **涉及文件**：`frontend/src/components/ChatImportDialog.vue`、`frontend/src/assets/styles/chat.css`。
- **验证方式**：SFC关闭逻辑测试补充文案断言通过；`frontend` `npm run build`通过。此次仅增加用户提示，没有改变上传接口或强制裁剪行为。

### 2026-09-04：截图导入弹窗被背景点击关闭

- **现象与根因**：上传/视觉识别中的导入弹窗点击外部即消失；`closeOnBackdrop` 将dialog背景点击直接转成close事件，`handleClose`也没有处理中保护，重新打开会清空前端步骤。
- **修复**：移除背景点击关闭；上传、processing、保存、头像上传、蒸馏期间统一保护关闭入口并禁用关闭按钮；原生cancel事件在忙碌时preventDefault，图片预览的Esc只关预览。蒸馏成功的程序关闭保留，空闲时关闭按钮与Esc正常使用。
- **依据**：[HTMLDialogElement cancel事件](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/cancel_event)支持阻止原生Esc关闭；业务忙碌保护为本项目逻辑。
- **验证**：`node --test frontend/tests/chatImportClose.test.mjs`对实际SFC编译后的setup逻辑回归背景绑定、忙碌各状态、预览、空闲关闭及蒸馏成功退出；Vue生产构建通过。不重跑OCR、不新增导入数据；未改服务端协议。

### 2026-09-04：语境自适应语音与 OCR 声音画像（功能已实现，听感待验收）

- **原问题**：整轮共用固定语速/指令，OCR建议与审核表单分离；语音回放重新生成时不能还原原来逐句表达。
- **实现**：后端复用同一次多模态LLM生成逐句计划，白名单标签仅进入TTS正文，固定项优先；会话归属校验、历史视觉附件续签、首计划超时/有界队列/供应商流关闭。完整语音和最终参数落库，音频有期限及大小上限，过期以原计划恢复。OCR审核与工坊共用可选声音维度表单。
- **边界修复**：审核保存失败阻止确认/蒸馏；非法rate/标签校验；中断和额度不足不保存完整音频；重播要求完整资产事件；同用户不同会话不能错绑音频。拟声和停顿预留额外时长，按实际交付PCM计费。
- **代码**：backend/speech_plan.py、speech_store.py、app.py、OCR/人设/历史Store、迁移013、VoiceProfileForm.vue、ChatView/VoiceView及API。
- **验证**：自适应mock覆盖当前图片/视频、历史附件/跨会话、超时、取消、额度与回放；真实PostgreSQL事务回读覆盖表单与音频过期，全部rollback；Provider参数、前端7项测试和构建通过。浏览器共享表单无横向溢出、旧值保持。真实共情/庆祝样本返回2.400秒/4.648秒PCM。
- **未验收**：主观听感、真实OCR上传整链、端到端延迟对照；新自适应仅作用于新语音回合，无计划的旧纯文字消息仍按基调朗读。不把测试通过写成已生产上线。

> **文档定位**：本项目唯一权威的进度追踪与排障沉淀文档。
> **协作守则**：所有 Agent 在遇到开发、测试或运行异常时，**必须先查阅本文档**；解决新问题后必须立即追加沉淀，形成排障知识闭环。
> **配套可视化**：可直接在浏览器打开 `progress/index.html` 交互式查阅。

> **2026-08-27 当前运行方向**：浏览器 `SpeechRecognition` 负责一轮语音转写，FastAPI 调用百炼 `qwen3.5-flash` 和 `qwen-audio-3.0-tts-flash`；第一阶段不接入 Qwen、MiMo 或其他独立 ASR。此前 MiniCPM-o、ElevenLabs 与 MiMo ASR 方案均保留为历史研究，不得报告为当前生产架构。

---

## 目录索引

- [1. 已开发上线功能清单 (Feature Manifest)](#1-已开发上线功能清单-feature-manifest)
- [2. 已修复问题与排障解决宝典 (Troubleshooting & Fixes)](#2-已修复问题与排障解决宝典-troubleshooting--fixes)
  - [ISSUE-01: 本机 19103 连接被拒绝 (connection refused)](#issue-01-本机-19103-连接被拒绝-connection-refused)
  - [ISSUE-02: MiniCPM-o WebSocket 1000 异常断开或会话初始化被拒绝](#issue-02-minicpm-o-websocket-1000-异常断开或会话初始化被拒绝)
  - [ISSUE-03: 模型陷入死循环只返回 listen，无文本和音频输出](#issue-03-模型陷入死循环只返回-listen无文本和音频输出)
  - [ISSUE-04: 语音重复播放、多段音频交织或旧音频串入新会话](#issue-04-语音重复播放多段音频交织或旧音频串入新会话)
  - [ISSUE-05: 音频开始播放时出现“咚”一声爆音/点击音 (Click/Pop)](#issue-05-音频开始播放时出现咚一声爆音点击音-clickpop)
  - [ISSUE-06: 文字回复与 TTS 中泄漏 \<think\> 思维链标签](#issue-06-文字回复与-tts-中泄漏-think-思维链标签)
  - [ISSUE-07: 单次手动 TTS 与实时双工语音播放冲突](#issue-07-单次手动-tts-与实时双工语音播放冲突)
  - [ISSUE-08: 本地开发 Vite 代理下 WebSocket 握手被 Origin 拒绝](#issue-08-本地开发-vite-代理下-websocket-握手被-origin-拒绝)
  - [ISSUE-09: 高并发请求下免费额度扣减不一致与重复扣减](#issue-09-高并发请求下免费额度扣减不一致与重复扣减)
  - [ISSUE-12: 官方 MiniCPM-o-Demo 替换后的运行边界与验证基线](#issue-12-官方-minicpm-o-demo-替换后的运行边界与验证基线)
  - [ISSUE-13: 现有 Vue 页面接入远端官方 Gateway](#issue-13-现有-vue-页面接入远端官方-gateway)
- [3. 当前进行中与规划方案 (Roadmap)](#3-当前进行中与规划方案-roadmap)

---

## 1. 已开发上线功能清单 (Feature Manifest)

| 模块 | 功能名称 | 状态 | 核心技术与设计点 | 涉及主要文件 |
|---|---|---|---|---|
| **账户体系** | 账号注册/登录与 HttpOnly 鉴权 | ✅ 已上线 | bcrypt 哈希存储，Redis 管理会话（720h TTL），HttpOnly Cookie 防 XSS 泄露。 | `internal/auth/auth.go`<br>`internal/auth/migrations/001_accounts.sql` |
| **额度体系** | 免费额度与调用流水审计 | ✅ 已上线 | PostgreSQL 事务原子扣减，`quota_usage` 唯一约束幂等防重，新用户默认赠送 20 次。 | `internal/auth/auth.go` |
| **实时语音** | 百炼 API 轮次语音对话 | ✅ 已迁移 | 浏览器负责 SpeechRecognition 转写，语音轮次通过 `/api/chat-and-tts/stream` SSE 推送 LLM 文本增量和 TTS 音频分片；纯文本轮次走 `/api/chat/stream`，不调用 TTS。旧 MiniCPM WebSocket、AudioWorklet 和引擎判断已移除。 | `backend/app.py`<br>`frontend/src/views/ChatView.vue`<br>`frontend/src/views/VoiceView.vue` |
| **半双工语音** | 官方 Demo 生命周期对齐的 Half-Duplex | ✅ 已实现 | 新增 `half_duplex` 模式、官方 VAD 参数、`vad_state → generating → chunk → turn_done` 事件；当前远端没有官方 SileroVAD Worker，由 Go 网关执行保守 VAD 并复用原生 Worker，Full-Duplex 保持不变。 | `internal/opensource/half_duplex_relay.go`<br>`frontend/src/views/ChatView.vue` |
| **负载均衡** | 双卡 RTX 4090 负载均衡与会话粘性 | ✅ 已上线 | Worker 0 (`:19080`) / Worker 1 (`:19082`) 轮询分发，会话连接后锁定单卡，避免 KV 缓存漂移。 | `internal/opensource/omni_relay.go` |
| **音频播放** | 百炼 PCM 分片流式播放 | ✅ 已迁移 | 后端 SSE 推送 Qwen-Audio-TTS PCM 分片，浏览器用单一 AudioContext 时间线顺序调度，首个分片到达即可开始播放。 | `backend/providers/qwen_tts.py`<br>`frontend/src/lib/pcmStreamPlayer.ts` |
| **音色管理** | 百炼声音克隆与 OSS 临时上传 | ⚠️ 待真实音频验收 | 百炼克隆入口使用 OSS 临时 PUT URL 和 `voice-enrollment`；旧开源参考音色上传及格式归一化路线不再由前端调用。 | `backend/providers/qwen_voice_clone.py`<br>`frontend/src/components/VoiceSettingsDialog.vue` |
| **情感合成** | 百炼 TTS 指令参数 | ✅ 已迁移 | 角色设定作为 system/instruction 传给 `/api/chat-and-tts/stream`；旧 IndexTTS 参数、情绪向量和本地 TTS 入口已移除。 | `backend/providers/qwen_tts.py`<br>`frontend/src/api/index.ts` |
| **字节服务** | 火山引擎 Realtime 与声音复刻 V3 | ✅ 已上线 | 统一抽象为 Provider 模式，支持字节端到端 Realtime 与开源自部署无缝切换。 | `internal/realtime/realtime.go`<br>`internal/voiceclone/voiceclone.go` |
| **前端交互** | 3D 粒子光球状态机与全屏语音 | ✅ 已上线 | 光球状态机（idle / listening / thinking / speaking），支持 Chat 伴聊视图与 Voice 全屏语音视图。 | `frontend/src/views/ChatView.vue`<br>`frontend/src/views/VoiceView.vue` |
| **故事星宇** | 故事星宇 3D 页面 UI 与灵动交互重构 | ✅ 已上线 | 基于 UI Designer & Whimsy Injector 规范重构：以呼吸星芒（Starlight Beacon）与轻巧微型名帖取代原 240px 大矩形重叠卡片；实现 Hover 平滑绽放星语浮笺（Whisper Card）；Canvas 引擎新增周期性金白流星（Shooting Stars）与点击星海触控涟漪；点赞时触发彩色星尘爱心粒子爆裂微动效；双击星空触发流星雨彩蛋；毛玻璃聚光灯卡片与无边框微光信笺交互全面升级。 | `frontend/src/views/StoriesView.vue`<br>`plan/2026-08-28_故事星宇页面UI与灵动交互重构方案.md` |
| **账户与会话持久化** | Local Storage 业务数据迁移 PostgreSQL | ✅ 已迁移（待浏览器面板复核） | 账户、HttpOnly 会话、角色设置、聊天记录和遗留故事寄语使用 PostgreSQL；一次性本机迁移在数据库回读成功后删除五个微光 Key，`fsmt_*` 不受影响。当前用户已迁入 5 条消息、1 份设置和 1 条故事。 | `backend/app_data_store.py`<br>`backend/migrations/005_app_data_persistence.sql`<br>`backend/app.py`<br>`frontend/src/api/index.ts` |
| **云 API 对象存储** | 阿里云 OSS 私有 Bucket 签名上传 | ✅ 已实现（前端已接入，待浏览器实传验收） | `oss2` 生成 `voice-references/` 临时 PUT URL；前端使用短时 URL 直传，RAM 用户使用 Bucket 级最小权限，长期密钥只在后端环境变量。 | `backend/providers/oss.py`<br>`backend/app.py`<br>`frontend/src/api/index.ts` |
| **百炼声音克隆接口** | Qwen-Audio-TTS `voice-enrollment` 与用户关联 | ⚠️ 待真实音频验收 | 后端 PostgreSQL 按本地用户 ID 保存 `voice_id`、OSS 对象键、文件元数据、目标模型和创建时间；刷新设置页可读取记录并生成临时预览 URL。后台任务、状态持久化之外的审核/删除和真实音频验收仍待实现。 | `backend/voice_store.py`<br>`backend/migrations/001_voice_clones.sql`<br>`backend/app.py`<br>`frontend/src/components/VoiceSettingsDialog.vue` |
| **多模态对话** | Qwen3.5-Flash 图片与视频多模态对话 | ✅ 已上线 | 支持 JPG/PNG/WEBP（≤10MB，≤4张）与 MP4/MOV/WEBM（≤50MB，≤120s，fps=2）直传私有 OSS，OpenAI-compatible 结构化 `content` 请求，图文/视频理解流式回答，语音融合提问与克隆音色朗读，大图弹窗与历史回显。 | `backend/providers/oss.py`<br>`backend/app.py`<br>`frontend/src/views/ChatView.vue`<br>`frontend/src/api/index.ts` |
| **按需朗读** | 纯文本消息按需朗读 | ✅ 已上线 | AI 消息气泡提供独立按需朗读按钮（▶/■）；后端 `POST /api/messages/tts` 自动绑定当前用户克隆音色或默认音色合成；单实例互斥播放，完全隔离左侧语音光球状态，刷新后可重新按需播放。 | `backend/app.py`<br>`frontend/src/views/ChatView.vue`<br>`frontend/src/api/index.ts` |
| **截图导入** | 聊天截图提取对话记录 | ✅ 已上线 | 支持上传微信/IM 聊天截图（≤10张），Qwen3.5-Flash 视觉结构化提取左右侧气泡、说话人、时间与顺序；支持图片/视频占位符补充上传、语音消息转写录入；提供双栏原图对照与编辑审核，确认后写入会话记录。 | `backend/chat_import_store.py`<br>`backend/providers/screenshot_extractor.py`<br>`frontend/src/components/ChatImportDialog.vue`<br>`frontend/src/views/ChatView.vue` |
| **角色与人格蒸馏** | Ex-Skill 五层人格蒸馏与多角色记忆工坊（含 OCR 零门槛一键提炼） | ✅ 已上线 | 基于 AgentSkills 开放标准与 ex-skill 规范构建：支持五层结构化 Persona（L0 硬规则 ~ L4 冲突模式）、Memories 共同记忆库（时间线/黑话/生活偏好/冲突敏感点）、运行时指令动态编译、支持从微信聊天截图 OCR 结果**一键全自动提取五层人设与共同回忆（零手动填表，自动推断角色称谓与画像并无缝打开工坊微调）**、对话动态调教/纠偏规则实时注入（越聊越像）、以及人设版本快照与一键回滚。 | `internal/auth/migrations/010_personas.sql`<br>`backend/persona_store.py`<br>`backend/persona_distiller.py`<br>`backend/prompt_compiler.py`<br>`backend/correction_handler.py`<br>`frontend/src/components/PersonaWorkshopDialog.vue`<br>`frontend/src/components/DistillWizardDialog.vue`<br>`frontend/src/components/CorrectionDialog.vue`<br>`frontend/src/stores/personaStore.ts` |
| **套餐与计费** | 浏览器转写保留、产品套餐展示与影子用量统计 | ✅ 已上线 | 保持浏览器端 `SpeechRecognition` 转写（服务端不接收麦克风原始音频）；创建公开套餐页 `/pricing`（免费体验、Plus 59元/月、Pro 129元/月三档对比与移动端适配）；后端 PostgreSQL 记录 `usage_events` 与 `user_subscriptions`，精准埋点 AI 回复、TTS 秒数、图片、视频、截图导入与音色槽位；个人中心重构为多维用量进度仪表盘。 | `backend/billing_store.py`<br>`backend/migrations/004_billing_and_usage.sql`<br>`frontend/src/config/plans.ts`<br>`frontend/src/views/PricingView.vue`<br>`frontend/src/components/AccountDialog.vue` |
| **外部套餐兑换** | 链动小铺一次性套餐兑换码与独立购买页 | ✅ 真实闭环已验收 | PostgreSQL保存兑换码哈希、批次和授权流水；支持一次性兑换、同档续期、跨档拦截、频控和并发幂等；真实付款、续期、退款已由用户验收。 | `internal/auth/migrations/006_redemption_codes.sql`<br>`backend/billing_store.py`<br>`backend/app.py`<br>`scripts/create_redemption_batch.py`<br>`frontend/src/views/PurchaseView.vue` |
| **运营与生产监控** | 生产监控 Web 页面与运营管理后台 UI | ✅ 已上线 | 唯一管理员统一后台：24h/7d 生产监控大盘（预估成本、完成/失败率、悬挂预留、活动告警、原生 SVG 趋势图、用量分布、模型拆分、30s自适应轮询与页面可见性感知）；Token与成本分析（用户级输入/输出Token、TTS字符、遥测完整性）；权益交易流水（卡密兑换账本，实付标注“渠道未同步”）；用户管理（搜索、过滤、资料/备注编辑、禁用并原子注销会话、启用、会话与消息正文审查）。 | `backend/app_data_store.py`<br>`backend/billing_store.py`<br>`backend/app.py`<br>`internal/auth/migrations/009_user_management_and_admin.sql`<br>`frontend/src/views/MonitoringView.vue`<br>`frontend/src/views/AdminCostsView.vue`<br>`frontend/src/views/AdminTransactionsView.vue`<br>`frontend/src/views/AdminUsersView.vue`<br>`frontend/src/views/AdminUserDetailView.vue` |
| **声音克隆与音频工具** | 参考音频在线可视化裁剪工具 (Audio Trimmer) | ✅ 已上线 | 纯前端 Web Audio API 解码音频波形并在 Canvas 上动态渲染发光峰值；支持双端滑块与 ±0.5s 微调设置起止时间；内置百炼声音复刻官方推荐合规标识（最佳 10–20 秒，允许 5–30 秒）；支持选区试听与动态播放指针；裁剪后纯客户端快速切片并编码为标准 16-bit PCM RIFF WAV 格式；保留原音频支持一键还原。 | `frontend/src/utils/audioEncoder.ts`<br>`frontend/src/components/AudioTrimmer.vue`<br>`frontend/src/components/VoiceSettingsDialog.vue`<br>`frontend/src/assets/styles/voice-api.css` |


---

## 2. 已修复问题与排障解决宝典 (Troubleshooting & Fixes)

### ISSUE-01: 本机 19103 连接被拒绝 (connection refused)

- **问题现象**：前端发起实时语音会话时报错 `connection refused 127.0.0.1:19103`，光球变红或提示“MiniCPM-o 原生接口连接失败”。
- **根本原因**：
  1. 本机与远端 GPU 服务器的 SSH 隧道未启动，或者启动隧道时使用了后台临时 Shell，终端关闭后 SSH 进程被系统级信号清理。
  2. 远端 GPU 上的 MiniCPM-o Worker 进程崩溃（如显存 OOM）导致端口未监听。
- **修复与排查方案**：
  1. 检查本机隧道端口：`lsof -nP -iTCP:19100-19104 -sTCP:LISTEN`。
  2. 启动前台持久在线隧道：`deploy/opensource/start-minicpm-tunnel.sh "$REMOTE_HOST" "$REMOTE_PORT"`。
  3. 登录远端服务器检查 Worker 状态：`supervisorctl status` 或 `ss -lntp | rg '19080|19082'`。
- **涉及文件**：[`deploy/opensource/start-minicpm-tunnel.sh`](file:///Users/fangzengxing/ZCodeProject/weiguang/deploy/opensource/start-minicpm-tunnel.sh)
- **验证方式**：执行 `curl -I http://127.0.0.1:19100` 或测试 WebSocket 握手，确认返回有效 HTTP 响应。

---

### ISSUE-02: MiniCPM-o WebSocket 1000 异常断开或会话初始化被拒绝

- **问题现象**：实时语音建立连接后立即收到 WebSocket Close 1000，提示 `MiniCPM-o 会话初始化被拒绝`。
- **根本原因**：
  1. 后端连接的远端路径错误，误连到了兼容 HTTP 端口而不是 MiniCPM-o 原生 `/backend` WebSocket 路径。
  2. 首帧 `session.init` 阶段，如果配置了参考音色（Reference Voice），GPU 显存 cold-start 加载耗时超过了默认的读取超时时间。
- **修复方案**：
  1. 在 `internal/opensource/omni_relay.go` 中，将会话初始化握手超时从默认简短超时放宽到 60 秒（`SetReadDeadline(time.Now().Add(60 * time.Second))`），覆盖冷启动预热窗口。
  2. 增加 Worker 容灾快速重试机制：当选中的 Worker 握手失败时，立即尝试下一个配置的 Worker 端点，而不是阻塞用户会话。
- **涉及文件**：[`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go#L158-L242)
- **验证方式**：重启远端 Worker 进程后立即连接，验证冷启动场景下能平稳完成握手并不再报 1000 异常。

---

### ISSUE-03: 模型陷入死循环只返回 listen，无文本和音频输出

- **问题现象**：用户在麦克风说话后，后端收到大量 `response.output.delta` 且 `kind` 全部为 `listen`，模型永远在“听”，既不输出文字也不输出音频。
- **根本原因**：
  1. 字段命名错误：使用了音色上传接口的 `audio_base64`，而 MiniCPM-o 原生 Full-Duplex 要求的字段是 `input.audio`。
  2. 强制倾听参数设置错误：误将 `force_listen` 设为 `true` 或省略，导致服务端推断为强制保持倾听状态，模型无法自主决策触发 speak。
  3. 输入门控全部丢弃：前端麦克风底噪或能量过低，被首帧门控拦截，导致 Worker 接收不到任何非静音帧。
- **修复方案**：
  1. 在 `omni_relay.go` 的 `input.append` 载荷中明确指定：
     ```json
     {
       "type": "input.append",
       "input": {
         "audio": "<base64 float32 PCM>",
         "force_listen": false,
         "max_slice_nums": 1
       }
     }
     ```
  2. 在 `session.init` 时显式声明 `"ls_mode": "explicit"`。
- **涉及文件**：[`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go#L275-L290)
- **验证方式**：开启语音对话后说一句话，观察后端日志是否出现 `chat.delta` 和 `tts.start`，确认能够正常输出语音。

---

### ISSUE-04: 语音重复播放、多段音频交织或旧音频串入新会话

- **问题现象**：AI 说话时有时会同一句话播放两次、重叠杂音，或者上一轮对话的尾音混入了新一轮对话中。
- **根本原因**：
  1. 回合结束标志绑定错误：误将 `response.done` 作为音频结束依据。官方 Full-Duplex 协议中，部分音频 delta 可能会在 `response.done` 之后到达，过早关闭播放器导致多段分立。
  2. 扬声器回声自激：AI 输出结束后，外放扬声器的残余尾音被麦克风采集再次上传，模型将其误判为用户输入而自问自答。
  3. 手动 TTS 与实时语音同时存在，未正确做 Request ID 与 Playback Epoch 互斥。
- **修复方案**：
  1. 严格以 `kind=listen` 作为官方 Full-Duplex 的回合结束边界。
  2. 引入扬声器尾音冷却门控：在 AI 输出结束后的 350ms 内（`inputIgnoreUntil`），丢弃采集音频，防止回声自激。
  3. 在浏览器端采用单例持久 `AudioWorklet`，每次新播放前递增 `playbackEpoch` 并清空旧队列。
- **涉及文件**：
  - [`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go#L400-L425)
  - [`frontend/public/playback-worklet.js`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/public/playback-worklet.js)
- **验证方式**：使用外放音箱进行 5 轮连续实时对话及手动打断，确认无重复播放与无回声自激。

---

### ISSUE-05: 音频开始播放时出现“咚”一声爆音/点击音 (Click/Pop)

- **问题现象**：每次 AI 开始说话或者用户打断切换时，耳机或扬声器中会出现明显的“咚”一声爆破音（DC Offset 突变）。
- **根本原因**：
  1. 队列清空时直接将正在输出的 PCM 缓冲区硬切断置为 0，波形瞬间从高电平跌落至零点产生直流阶跃冲击（Click/Pop）。
  2. 首帧音频采样未初始化或包含异常极大值。
- **修复方案**：
  1. 在 `playback-worklet.js` 中重构 `clearQueue()` 逻辑：在清空队列前，对当前正在输出的末尾 64 个采样应用极短线性淡出（Fade-out 曲线），平滑归零后再重置缓冲区指针。
  2. 限制 Float32 转 PCM16 的数值边界，使用 `math.Max(-1, math.Min(1, value))` 进行严格硬截断保护。
- **涉及文件**：
  - [`frontend/public/playback-worklet.js`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/public/playback-worklet.js)
  - [`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go#L521-L537)
- **验证方式**：佩戴耳机反复打断 AI 说话 20 次，确认无论何时打断或开始播放均完全无爆破杂音。

---

### ISSUE-06: 文字回复与 TTS 中泄漏 \<think\> 思维链标签

- **问题现象**：在文字聊天或单次 TTS 朗读时，页面文字中包含 `<think>...思考过程...</think>`，甚至 TTS 也把思考过程念了出来。
- **根本原因**：深度推理大模型在流式输出时会输出思考标签，而流式分片可能恰好将 `<think>` 拆分成 `<th` 和 `ink>` 跨 chunk 返回，简单 `strings.Replace` 无法匹配跨分片标签。
- **修复方案**：
  1. 编写专门的状态机过滤器 `thinkFilter`，维护内部缓冲状态，能够识别跨分片的 `<think>` 开头与 `</think>` 结尾，将标签及其内部所有思考内容完全剔除。
  2. 在流式下发给前端 `chat.delta` 以及送入 TTS 队列前统一执行 `thinkFilter.consume(text)`。
- **涉及文件**：[`internal/opensource/think_filter.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/think_filter.go)
- **验证方式**：开启高推理深度模型测试打字，观察聊天气泡及 TTS，确认思维链完全被隐藏，仅展示最终回答。

---

### ISSUE-07: 单次手动 TTS 与实时双工语音播放冲突

- **问题现象**：在文字聊天列表点击某条历史消息的“播放”按钮后，又点击左侧光球开启实时语音，结果两段声音同时播放，音画错乱。
- **根本原因**：手动 TTS 是通过 HTTP `/api/open-source/tts` 异步拉取整段 PCM，拉取完成后直接塞入播放器，未与当前是否处于实时语音会话建立状态互斥绑定。
- **修复方案**：
  1. 在 `ChatView.vue` 中统一引入 `audioRequestId`、`activeTTSAbort: AbortController` 和 `playbackEpoch`。
  2. 开启实时语音（`startVoice`）或发送新文本时，立即调用 `activeTTSAbort.abort()` 取消正在进行的 TTS HTTP 请求，并调用 `session.stopPlayback()` 强制停止旧播放。
  3. 在 TTS 数据返回后二次校验当前 `requestId === audioRequestId`，若已失效则直接丢弃数据。
- **涉及文件**：[`frontend/src/views/ChatView.vue`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/src/views/ChatView.vue#L320-L358)
- **验证方式**：点击长文本 TTS 并在音频加载过程中立刻点击光球说话，确认旧 TTS 请求被成功终止，实时语音顺畅启动。

---

### ISSUE-08: 本地开发 Vite 代理下 WebSocket 握手被 Origin 拒绝

- **问题现象**：在 `localhost:5173` 前端调试时，连接 `ws://localhost:5173/api/realtime` 报错 `403 Forbidden`。
- **根本原因**：Vite 代理将请求转发到 Go 后端 `:8080` 时，保留了浏览器原始的 `Origin: http://localhost:5173`，而 Go 服务端的 `Host` 头部被代理重写为 `localhost:8080`，默认跨域检查因端口不一致判定为跨域攻击而拒绝。
- **修复方案**：
  1. 在 Go 后端 `browserUpgrader.CheckOrigin` 中增加 `isLocalhost` 智能判断：当 Origin 和 Host 均为本机回环地址（`localhost`、`127.0.0.1`、`::1`）时，即便端口不同也判定为合法的本地开发代理并予以放行。
- **涉及文件**：
  - [`internal/realtime/realtime.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/realtime/realtime.go#L33-L64)
  - [`internal/opensource/opensource.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/opensource.go#L111-L136)
- **验证方式**：在 Vite 开发环境下刷新页面连接 WebSocket，确认连接正常建立不再返回 403。

---

### ISSUE-09: 高并发请求下免费额度扣减不一致与重复扣减

- **问题现象**：用户在网络不稳时连续快速点击发送文字，导致扣除了多次额度，或者并发扣费失败导致会话报错。
- **根本原因**：额度查询与更新分散在不同 SQL 语句中，缺乏行级锁与幂等流水号约束，客户端网络重试时可能被当做新请求重复扣减。
- **修复方案**：
  1. 建立 `quota_usage` 流水表，并对 `request_id` 施加唯一键约束（`UNIQUE(request_id)`）。
  2. 在同一个 PostgreSQL 数据库事务内执行 `UPDATE user_quotas SET quota_remaining = quota_remaining - $1 WHERE user_id = $2 AND quota_remaining >= $1` 以及 `INSERT INTO quota_usage ... ON CONFLICT (request_id) DO NOTHING`。
  3. 利用单事务原子性保证“扣减额度”与“记录流水”绝对一致，重试请求自动命中幂等。
- **涉及文件**：
  - [`internal/auth/auth.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/auth/auth.go#L280-L315)
  - [`internal/auth/migrations/001_accounts.sql`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/auth/migrations/001_accounts.sql)
- **验证方式**：运行单元测试 `go test -v ./internal/auth -run TestQuotaConcurrent`，高并发测试下额度计算完全准确。

---

### ISSUE-10: 原生双工语音对话下首句后识别器锁死与语音输入占位符冗余

- **问题现象**：语音对话时只有第 1 句话能识别出文字，从第 2 句开始右侧不再显示文字或出现冗余的 `（语音输入）` 占位符。
- **根本原因**：
  1. **转写器模式与生命周期拦截**：`SpeechRecognition` 开启 `continuous: true` 时在停顿后容易进入静音超时挂起状态，且 `startLocalTranscript()` 中被 `localRecognitionEnabled` 拦截无法触发重启；
  2. **前端 1500ms 短句去重逻辑**：`updateASR` 中误设了 1500ms 忽略逻辑，导致第 2 句紧随其后时被前端丢弃；
  3. **冗余占位符落库**：后端在每次 `kind=listen` 触发时，若当前未收到转写，误插入了人工占位符 `（语音输入）`，导致多轮对话后产生多个无意义气泡。
- **修复方案**：
  1. 将转写器配置为 **单次连贯模式（`continuous: false`）**：每句话说完停顿后，识别器立即触发 `onend` 并于 50ms 内无缝实例化重启，彻底杜绝 Chromium 长连接挂起与第 2 句漏字；
  2. 移除 `updateASR` 中的 1500ms 丢弃限制，并在 `playback.idle` / `asr.info` 时干净重置回合变量；
  3. 移除前后端所有的人工 `（语音输入）` 注入代码，转写文本自然产生、自然入库。
- **涉及文件**：
  - [`frontend/src/lib/realtimeClient.ts`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/src/lib/realtimeClient.ts)
  - [`frontend/src/views/ChatView.vue`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/src/views/ChatView.vue)
  - [`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go)
- **验证方式**：连续进行 5 轮语音对话，验证每一句话都准确转写为实际文字，不再出现 `（语音输入）`。

---

### ISSUE-11: 播放开始时的“咚”一声冲击音 (Pop/Thump) 与大模型历史对话上下文注入

- **问题现象**：
  1. 每次 AI 回答语音开始播放的瞬间，耳机或扬声器中会出现短促沉闷的“咚”一声爆音；
  2. 用户询问“我们之前对话有说一些什么聊天记录吗你看一下”，模型回答“之前的对话里面没有保存记录哦”。
- **根本原因**：
  1. **音频首帧跳跃**：`playback-worklet.js` 在从静音切换为播放时，若首个 PCM 样本存在 DC 偏移或高幅值，信号在 1 个采样周期内阶跃产生冲击波（Dirac Delta），听感表现为“咚”的一声爆破音；
  2. **双工会话未预填历史记忆**：`omni_relay.go` 在向原生 GPU Worker 发送 `session.init` 时，仅下发了静态系统提示词，未将历史对话拉取并注入 `system_prompt`，导致模型无法获知之前的聊天记录。
- **修复方案**：
  1. 在 `playback-worklet.js` 中增加 **20ms 线性淡入（Fade-in）**：当队列开始输出新音频时，对前 20ms（480 个采样点）应用平滑斜率淡入，彻底消除波形阶跃与“咚”声；
  2. 在 `omni_relay.go` 初始化双工会话时，调用 `o.base.initHistory(ctx)` 并将最近历史对话格式化注入大模型 `system_prompt`，赋予模型完整的跨会话上下文记忆。
- **涉及文件**：
  - [`frontend/public/playback-worklet.js`](file:///Users/fangzengxing/ZCodeProject/weiguang/frontend/public/playback-worklet.js)
  - [`internal/opensource/omni_relay.go`](file:///Users/fangzengxing/ZCodeProject/weiguang/internal/opensource/omni_relay.go)
- **验证方式**：佩戴耳机进行连续语音对话，确认 AI 每次发声前均丝滑平稳、无任何爆破杂音；询问大模型前几轮历史对话，确认模型能准确回答历史细节。

---

---

### ISSUE-12: 官方 MiniCPM-o-Demo 替换后的运行边界与验证基线

- **问题背景**：用户要求直接采用 OpenBMB 官方 Demo，并明确保留现有前端 UI。旧工作区是 Go/Gin + Vue 自定义链路，不能把旧 `/api/realtime` 或旧 Worker 事件映射当成官方协议。
- **官方依据**：核对官方仓库及提交 `50b0865c819c2f0ca24ec7994e05044e5f39d451`；官方运行入口为 `gateway.py`、`worker.py`、`py_backend/server.py`，官方网页在 `static/`，实时 WebSocket 为 `/v1/realtime`，内部 backend 路径为 `/backend`。
- **处理动作**：将官方工作树复制到项目根；移出旧 `cmd/`、`internal/`、`deploy/`、`scripts/`、`_legacy/`、`go.mod`、`go.sum` 和旧 `compose.yaml`；原 Vue UI 恢复到 `frontend/src/`，官方移动端保留在 `frontend/mobile/`；停止旧 `com.weiguang.backend`/`com.weiguang.frontend` launchd 服务并归档 plist；旧代码归档到 `/tmp/weiguang-pre-official.2ySsQJ`。
- **验证结果**：官方 Python `compileall` 通过；官方 JS 测试 38 个通过；`tests/test_runtime_media.py` 2 个通过；Gateway 导入通过；ASGI `/health` 返回 200/healthy，`/`、`/half_duplex`、`/realtime` 返回 200 HTML。
- **已知限制**：当前 macOS 无 NVIDIA CUDA 和 MiniCPM-o 权重，未宣称真实 GPU 推理或浏览器语音验收；官方 `tests/test_queue.py` 在当前 Python 3.14 环境为 30 通过、4 个 LRU/Worker 选择断言失败；`tests/test_schemas.py` 因未安装 PyTorch 无法收集。上述失败不修改官方实现，作为环境/上游基线记录。
- **后续接入边界**：保留的旧 Vue UI 依赖已移出的 Go `/api/*` 路由，当前只保证文件未删除；若要继续使用 `localhost:5173/chat`，必须另建 Vue 到官方 `/v1/realtime` 的适配方案并进行真实 Worker/GPU 验收。

### ISSUE-13: 现有 Vue 页面接入远端官方 Gateway

- **问题现象**：用户要求保留现有 `localhost:5173/chat` 页面，但模型服务必须迁移到远端 GPU 主机的官方 Gateway + Worker + Backend，不能再依赖本地 `8080/19103` 或旧 Go API。
- **官方依据**：当前官方提交 `50b0865c819c2f0ca24ec7994e05044e5f39d451` 的文档规定 Chat 使用 `/v1/realtime?mode=chat`，Audio Full-Duplex 使用 `/v1/realtime?mode=audio`；官方生命周期是 `session.queue_done → session.init → session.created → input.append → response.output.delta → response.done`。官方 Half-Duplex 文档示例使用 `/ws/half_duplex/{session_id}`，但当前 `gateway.py` 只公开 `/v1/realtime` 与 `/half_duplex` HTML 页面，实际请求该 WS 路由返回 403，因此页面入口不能伪造启用。
- **处理动作**：
  1. `frontend/vite.config.ts` 将 `/v1`、`/ws` 代理至本地隧道 `https://127.0.0.1:8006`；
  2. `frontend/src/lib/realtimeClient.ts` 改用官方 `/v1/realtime`，Chat/Audio 载荷遵循官方协议；本地 SpeechRecognition 只负责显示用户转写，删除人工“（语音输入）”占位符；半双工协议代码保留但 UI 禁用；
  3. `frontend/src/api/index.ts`、`stores/auth.ts` 将旧账号、设置、历史契约改为 localStorage，避免新增本地兼容后端；文本 Chat 明确 `tts.enabled=false`；手动朗读改用浏览器 `speechSynthesis`，进入实时语音时会取消；
  4. 远端 `/root/minicpm-official` 启动官方 Gateway `8006/8007`、Worker `22400/22401`，两个 Worker 分别注册到 GPU 0/1，并以 `--backend-server-url` 连接已有官方兼容 `llama-omni-server` `19080/19082`；
  5. 本地 SSH `-L 8006:127.0.0.1:8006` 隧道和 Vite `5173` 已启动。
- **验证结果**：远端 Gateway/Worker health 均 healthy；远端 Chat WebSocket 返回 `session.created`、文本 delta 与 `response.done`；远端 Audio WebSocket 返回 `session.created(mode=full_duplex)` 与 `response.output.delta(kind=listen)`；本地 Vite 代理 Chat WebSocket 端到端返回“本地代理已连通”；前端 `npm run build` 通过。
- **本次回归边界**：前端补丁回归期间本地 SSH 隧道 `127.0.0.1:8006` 断开，旧 GPU pod 的 SSH 握手被远端直接关闭；因此随后浏览器出现的 403/“实时会话已断开”是 Gateway 不可达，不是文本或气泡状态机的响应错误。恢复远端 pod 与隧道后，需重新执行语音→文本连续切换验收。
- **涉及文件**：`frontend/vite.config.ts`、`frontend/src/api/index.ts`、`frontend/src/stores/auth.ts`、`frontend/src/lib/realtimeClient.ts`、`frontend/src/views/ChatView.vue`、`HANDOFF.md`。
- **后续边界**：需要在 Chrome 页面中实际允许麦克风并说出自然语句，验收浏览器本地转写、远端 Audio 输出和打断；该项不能用服务器合成音调代替。

### ISSUE-14: 官方流式文本重复追加与文本/语音模式切换竞态

- **问题现象**：官方 Chat 返回一条 `response.output.delta(kind=text)` 后，又在 `response.done.text` 中携带完整回答，页面将同一句话显示两遍；文本会话结束后立即切换全双工语音时，远端 Worker 尚未释放，下一条 WebSocket 可能返回 HTTP 403。
- **根因**：前端适配器把增量文本和完成事件完整文本无条件相加；关闭流程只发送 `session.close` 后立即关闭浏览器 WebSocket，而官方 Worker 的 `finally` 清理会调用一个可能长期挂起的 `runtime.aclose()`，导致 Worker 长时间保持 `duplex_active`，下一条模式连接被 Gateway 以 HTTP 403 拒绝。
- **修复方案**：
  1. `frontend/src/lib/realtimeClient.ts` 按 `response_id` 记录已收到的文本增量，`response.done` 仅在没有对应增量时补发完整文本；
  2. `RealtimeClient.close()` 与 `useRealtimeSession.close()` 改为可等待；模式切换在旧连接真正 close 后再等待 3.5 秒让 Worker 回落到 idle，旧连接的迟到事件不再写入新回合；
  3. `worker.py` 对官方后端关闭 RPC 使用 `asyncio.wait_for(..., timeout=3.0)` 并显式释放 runtime socket，避免 close 卡住时永久占用 GPU Worker；该补丁已同步部署到远端 `/root/minicpm-official/worker.py` 并重启两个 Worker。
  4. Gateway 为动态注册模式，Gateway/Worker 重启后通过内部 `8007/internal/workers/{worker_id}` 显式登记 `22400/22401` 两个 Worker，确保路由表恢复。
- **验证方式**：`npm run build` 通过；Chrome 隔离页面回归中，文本→全双工进入“正在聆听…”；停止语音后立即发送“请只回复：语音退出无竞态”，AI 正常返回且无 HTTP 403、无 loading 残留；官方 Audio WebSocket 完成 `queue_done → session.created → response.output.delta(kind=listen) → session.closed`，4 秒后 Worker 0 health 为 `idle`；远端 Gateway、两个 Worker 当前均为 healthy（Worker 1 的 `busy_chat` 是保留测试页的正常占用）。

### ISSUE-15: 全双工播放回声触发本地转写与 loading 残留

- **问题现象**：用户说“在吗”后，页面右侧出现与 AI 回复相同或相近的重复用户气泡；AI 播放结束、用户已经停止说话后，聊天区仍保留等待中的三点 loading。
- **官方依据**：官方 Audio Realtime 文档规定音频与文本分别通过 `response.output.delta` 下发，`kind=listen` 表示模型已经回到听用户状态；不能把播放中的音频当成新的用户回合，也不能用 `response.done` 作为全双工每轮边界。
- **根因**：浏览器 `SpeechRecognition` 在扬声器播放期间仍持续接收本机回声；回声文本触发 `asr.ended`，前端无条件 `showTyping()`，而官方音频事件没有对应的本地播放状态门控。
- **修复方案**：
  1. `RealtimeClient` 在首个 `kind=audio` 发出 `realtime.speaking`，在 `kind=listen` 发出回听事件；
  2. `ChatView` 在 AI 播放期间及尾音冷却窗口内过滤与最近 AI 文本高度相同的本地转写，避免把 AI 声音显示到用户侧；不同内容仍可作为 Full-Duplex 打断；
  3. `realtime.listen`、`playback.idle`、`socket.closed` 统一清理 typing、watchdog 和回合状态。
- **验证方式**：`npm run build` 通过；Chrome 空闲全双工 12 秒后状态为“正在聆听…”且 loading 数为 0；停止语音后状态回到“轻触光球，开始说话”，loading 数为 0，控制台无 error/warn。

### ISSUE-16: Chrome 本地 SpeechRecognition 重启导致同一语句连续冒泡

- **问题现象**：全双工页面在一次用户发言后，右侧连续出现“你在干嘛 / 你在干 / 你”等相同或前缀相近的用户气泡；伪输入会让用户误以为后续 AI 没有回复。
- **官方依据**：官方 Audio Full-Duplex Demo 只持续发送 16 kHz 麦克风音频，并按 `response.output.delta(kind=text|audio|listen)` 更新模型输出，不使用浏览器 `SpeechRecognition` 作为官方输入链路。
- **根因**：当前 Vue 页面为显示用户字幕额外启用了 `continuous=false` 的 Chrome 识别器，并在 `onend` 后自动重启；Chromium 会在重启窗口重复返回相同 final 或前缀结果。
- **修复方案**：AI 首个音频增量到来时停止本地识别器，但保留原始麦克风 WebSocket 输入用于 Full-Duplex 打断；播放队列真正 idle 后再恢复识别器；跨识别实例对相同/高相似 final 结果做 8 秒去重，并将自动重启延迟到 250ms。识别器 `onend`/`asr.ended` 不再清空当前用户气泡，直到首个模型输出或官方 `listen` 事件到来才结束该回合，从而把“我”→“我不知道”这类前缀结果更新在同一条气泡中。
- **验证方式**：`npm run build` 通过；远端 Audio WebSocket 用官方测试语音 WAV 验证可返回 `kind=text`；Chrome 开启/退出全双工后 loading 清零，文本链路仍可正常回复。自然麦克风语句需在用户环境最终验收。

### ISSUE-17: TTS 音频事件迟到、旧会话占用 Worker 与 WebSocket 并发发送

- **问题现象**：远端日志能生成 TTS WAV，但页面偶尔只看到文本或后续请求不再回复；旧 Chrome 标签页保持全双工后，Gateway 状态长期显示 `duplex_active` / `busy_chat`。官方协议中音频增量可能在 `response.done` 之后到达，若客户端过早把 `response.done` 当作音频结束会丢声音。
- **官方依据**：核对 OpenBMB MiniCPM-o 官方 Gateway、Worker 和 `examples/realtime/audio_probe.py`；音频/文本均通过 `response.output.delta` 分发，`kind=listen` 才表示回到聆听态。当前版本的 C++ backend 在 T2W 回调线程发送音频事件，因此发送必须和其他 WebSocket 事件串行化。
- **根因**：C++ backend 的文本事件与 T2W 音频回调可能同时调用同一个 WebSocket `send`；同时，浏览器或旧标签页未完成关闭时，Worker 仍被官方 Gateway 视为活动会话。
- **修复方案**：
  1. 在远端 `llama.cpp-omni/tools/server/ws_handler.cpp` 为文本、listen、response 和 TTS 音频增量共用发送互斥锁，避免并发 `ws.send` 破坏事件帧；音频发送失败记录明确日志。
  2. `worker.py` 后端关闭 RPC 使用 3 秒有界等待；前端关闭流程等待 WebSocket close，并在模式切换前留出交接窗口。
  3. Gateway/Worker/backend 重启后重新登记 `22400/22401`，清理旧 C++ WebSocket 会话；浏览器停止语音后恢复文本发送。
- **验证方式**：远端 C++ `llama-omni-server` 构建通过；官方协议原始 WebSocket 保持连接到 `listen`，实际收到 `response.output.delta(kind=text)`、`response.done` 之后的 `response.output.delta(kind=audio)`（Base64 分片 128000/51200 等）及后续 `listen`；Gateway `/health` healthy、backend `19080/19082/health` 为 `status=ok`。Chrome 页面回归中，进入语音后停止，状态回到“轻触说话”、loading 为 0；随后发送文本并收到完整回复。浏览器扩展无法稳定接管另一张旧标签页，因此该标签页的自然麦克风输入仍需用户手动确认，不能冒充已完成。

### ISSUE-18: 旧 MiniCPM / IndexTTS 前端兼容链路残留

- **问题现象**：声音设置页已移除旧模型参数，但聊天和全屏语音仍引用 `/v1/realtime`、MiniCPM 引擎判断、AudioWorklet 和旧开源 provider 标识。
- **根因**：上一轮只清理了设置页和 TTS 参数，没有同步替换旧实时适配器。
- **处理动作**：聊天与全屏语音统一改为浏览器 SpeechRecognition 采集一轮文本，调用 FastAPI `/api/chat-and-tts` 获取百炼 LLM 回答与 TTS 音频 URL；删除 `realtimeClient.ts`、`useRealtimeSession.ts`、两个 AudioWorklet 文件、MiniCPM/IndexTTS 类型和旧 provider 切换 UI。
- **验证方式**：`rg` 检索前端、后端和 public 目录无 MiniCPM、IndexTTS、`/v1/realtime`、AudioWorklet 残留；前端 `npm run build`、后端 `.venv/bin/python -m compileall -q backend` 通过；`/api/health` 返回 Bailian LLM/TTS 与 OSS 配置完整。

### ISSUE-19: 百炼音频播放被浏览器语音识别当成下一轮输入

- **问题现象**：API 返回的 AI 音频播放期间，Chrome `SpeechRecognition` 被提前重新启动，扬声器回声被识别为新的用户消息并再次提交 `/api/chat-and-tts`。
- **根因**：`HTMLAudioElement.play()` 只代表开始播放，旧逻辑在 Promise 返回后立即把 `busy` 清零并启动识别器，没有等待 `ended`；播放中的回声因此进入下一轮。
- **修复方案**：增加播放状态和 700ms 尾音冷却门控；音频播放或冷却期间禁止创建/重启 `SpeechRecognition`，仅在 `ended`/`error` 后重新进入聆听状态；`play` 事件将光球切换为“回应中”，播放期间点击光球可停止本地音频并恢复聆听；聊天页和全屏语音页统一处理。
- **验证方式**：前端 `npm run build` 通过；检查 `ChatView.vue`、`VoiceView.vue` 的识别器启动均受 `audioPlaying`/`audioCooldownUntil` 保护。需要在 Chrome 外放场景连续完成多轮自然语音做最终验收。

### ISSUE-20: 完整音频 URL 导致首包等待和非流式播放

- **问题现象**：文本需要完整生成后才调用 TTS，浏览器还要等待完整音频 URL 才开始播放。
- **根因**：旧 `/api/chat-and-tts` 串行执行完整 LLM 和非流式 TTS，只返回一个音频 URL。
- **处理动作**：新增 `/api/chat-and-tts/stream` SSE；LLM 按增量输出文本，按完整句子排队调用 Qwen-Audio-TTS SSE，浏览器通过 `PCMStreamPlayer` 按时间线播放 PCM 分片。
- **验证方式**：真实本地 smoke 返回 HTTP 200，并收到 `text.delta`、`text.done`、`audio.delta`、`audio.url`、`stream.done`；句子级策略已应用到聊天页和全屏语音页；前端 `npm run build` 与后端 compileall 通过。

### ISSUE-21: 纯文本聊天不应驱动左侧语音状态或 TTS

- **问题现象**：发送文字时左侧光球进入“正在想想”，文本聊天也复用了语音接口。
- **根因**：聊天回合统一调用 `/api/chat-and-tts/stream`，`submitTurn` 不区分文本和语音状态。
- **处理动作**：新增 `/api/chat/stream` 文本专用 SSE；文本回合只更新右侧对话和 typing，不改变左侧语音状态，也不调用 TTS；只有语音回合才进入 listening/thinking/speaking 状态。
- **验证方式**：文本流真实 smoke 返回 `text.delta`、`text.done`、`stream.done` 且无音频事件；前端 build、后端 compileall 通过。

### ISSUE-22: 声音克隆刷新后丢失用户绑定和参考音频状态

- **问题现象**：克隆成功后刷新页面，文件选择框为空，页面无法确认当前用户绑定的 `voice_id` 和参考音频。
- **根因**：旧实现只把 `voice_id` 写入浏览器 localStorage，后端没有保存用户、OSS 对象键和音频元数据；本地 File 对象本来也不能跨刷新恢复。
- **处理动作**：新增 PostgreSQL `voice_clones` 表和 `/api/voice-clones` GET/POST；请求通过稳定的本地用户 ID 关联记录，保存 voice、对象键、文件名、大小、时长、目标模型、创建时间；读取时生成短时 OSS GET URL，设置页展示已绑定音色和参考音频元数据。
- **验证方式**：本地 Docker PostgreSQL `weiguang-voice-postgres`（`127.0.0.1:55433`）健康，迁移表创建成功；前端 build、后端 compileall 通过。已有历史克隆没有对象键记录，需要重新克隆一次建立完整关联。

### ISSUE-23: 文本转语音未读取用户已克隆音色与模型未对齐

- **问题现象**：聊天页在进行纯文本按需朗读（▶）或实时语音回复时，播放的声音依然是系统默认音色（`longanhuan_v3.6`），未生效用户已克隆或已保存配置的音色。
- **根因**：
  1. 前端 `ChatView.vue` 在初始化时未加载 `voice.ensureReady()`，且 `playOrSynthesizeMessage` 调用 `synthesizeMessageTTS` 时未显式携带当前激活的 `voice.speaker` 音色 ID；
  2. 后端 `MessageTTSRequest` 与 `POST /api/messages/tts` 未接收 `voice` 字段，且单纯依靠 Header 用户 ID 查询数据库，若用户在面板保存配置或本地有音色时未命中；
  3. `POST /api/chat-and-tts/stream` 和 `POST /api/messages/tts` 在使用克隆音色时未自动关联解析其注册时的 `target_model`，模型与音色不匹配时导致接口回退默认系统音色。
- **处理动作**：
  1. 后端 `backend/app.py` 抽象统一音色与模型解析方法 `_resolve_tts_voice_and_model`，优先使用请求中的 `voice`、再查询用户绑定的最新激活克隆音色，并自动检索其注册时的 `target_model`；
  2. `backend/voice_store.py` 增加 `get_by_voice_id` 辅助查询；
  3. 前端 `frontend/src/api/index.ts` 中 `synthesizeMessageTTS` 增加 `voice` 与 `instruction` 传参支持；
  4. 前端 `ChatView.vue` 在 `onMounted` 及 `playOrSynthesizeMessage` 中主动调用 `voice.ensureReady()` 确保音色就绪，并将 `voice.speaker` 明确传递给合成接口。
### ISSUE-24: 截图导入弹窗未全局居中与入口布局优化

- **问题现象**：
  1. 打开截图导入弹窗时，`<dialog>` 偏向屏幕左上方，未在视口内垂直与水平居中；
  2. 导入入口放置在底部输入框工具栏容易与实时发送媒体附件混淆，用户体验不佳。
- **根因**：
  1. `.chat-import-dialog` 缺少 `margin: auto; position: fixed; inset: 0;`，导致部分浏览器默认将 `<dialog>` 布局在 `(0, 0)` 坐标；
  2. 入口按产品设计规范应作为页面级特性置于顶部导航栏 `AppNav.vue` 的操作区。
- **处理动作**：
  1. 在 `frontend/src/assets/styles/chat.css` 中为 `.chat-import-dialog` 补齐 `margin: auto; position: fixed; inset: 0; overflow: hidden;`，并调整高宽自适应与模糊遮罩；
  2. 在 `frontend/src/components/AppNav.vue` 的右上角操作区（`cnav__actions`）新增 **「导入图片」** 按钮，并通过 `openImport` 事件向上通知；
  3. 在 `frontend/src/views/ChatView.vue` 中绑定 `@open-import` 事件打开弹窗，并清理底部输入框中的冗余 📸 按钮。
- **验证方式**：
  1. 前端 `npm run build` 0 错误构建通过；
  2. 浏览器验证弹窗完美居中于屏幕正中央，右上角点击「导入图片」平滑调起。

### ISSUE-25: 截图导入审核页左侧原图不支持点击放大与交互缩放

- **问题现象**：审核页左侧“原图参考”容器尺寸受限，在核对密集文字、时间戳或长图时，点击原图无响应，无法看清细节。
- **根因**：原左侧视图仅渲染了固定容器的缩略图 `<img>`，未绑定图片放大灯箱（Lightbox）与缩放交互事件。
- **处理动作**：
  1. 在 `ChatImportDialog.vue` 中增加全屏放大灯箱（Teleport 到 `body`），支持点击图片/按钮随时调起；
  2. 支持 `+` 放大、`-` 缩小、`1:1` 重置缩放等级（50% ~ 300% 动态缩放）；
  3. 支持多张截图时的上一张/下一张切换（键盘 `←` / `→` 与按钮导航）；
  4. 支持键盘 `Esc` 或点击遮罩快捷退出。
- **验证方式**：
  1. 前端 `npm run build` 0 错误构建通过；
  2. 浏览器点击左侧原图及“🔍 放大查看”按钮，能流畅调起大图灯箱并支持多级缩放与键盘导航。

### ISSUE-26: 个人中心体验优化、退出登录闭环与 Vite 代理 500 修复

- **问题现象**：
  1. 个人中心内仍残留“上传授权记录”与“任务管理”等无用区块，弹窗默认拉伸且原生滚动条粗重突兀；
  2. 点击“退出登录”后页面无变化，无法真正退出登录状态；
  3. 请求 `GET http://localhost:5173/api/billing/summary` 偶发报错 `500 (Internal Server Error)`。
- **根因**：
  1. 个人中心仍沿用早期测试版本的 Tab 结构与未接真实业务的授权上传组件；
  2. `localProfile()` 默认生成了 `local@weiguang` 兜底资料并保存至 `localStorage`，导致 `isLoggedIn` 判定永远为真，且 `logout()` 未清除会话缓存；
  3. Vite 开发服务器在沙箱未 Bypass 启动时，反向代理连接宿主机 `127.0.0.1:8080` 被操作系统沙箱阻断（`EPERM`），导致 Vite 向浏览器返回 500。
- **处理动作**：
  1. 在 `AccountDialog.vue` 中移除 Tab 切换栏与“上传授权记录”模块，高度自适应并引入全局精致暗色细滚动条（`::-webkit-scrollbar` + `scrollbar-width: thin`）；
  2. 彻底重构前端认证状态流：未登录时 `fetchMe()` 返回 `null`，登录时写入用户资料，登出时清除 `localStorage` 缓存并重定向至首页；
  3. 彻底清理前端无用任务管理组件与接口；
  4. 启动 Vite 开发服务器时配置网络直通，消除代理 `EPERM` 导致的 500 错误。
- **验证方式**：
  1. 前端 `npm run build` 0 错误通过；
  2. 浏览器打开个人中心，布局紧凑美观无冗余模块，无原生滚动条；
  3. 点击“退出登录”瞬间生效并重置登录状态；
  4. `curl -i http://localhost:5173/api/billing/summary` 返回 200 OK。

## 3. 当前进行中与规划方案 (Roadmap)

| 方案名称 | 归档位置 | 状态 | 当前进展 |
|---|---|---|---|
| **生产监控与运营管理后台UI** | [`plan/2026-09-01_生产监控Web页面与UI开发方案.md`](../plan/2026-09-01_生产监控Web页面与UI开发方案.md) | `[未完成]` 单管理员方案待确认 | 已简化为唯一管理员：监控、Token成本、权益交易、用户编辑/禁用和对话正文直接查看；不做RBAC、访问审核或审计日志，尚未编码。 |
| **生产监控与成本告警** | [`plan/2026-09-01_生产监控与成本告警方案.md`](../plan/2026-09-01_生产监控与成本告警方案.md) | `[已完成]` 第一版 | 内部管理员API、24h/7d聚合、Token/字符成本估算、预算/失败率/悬挂预留/遥测缺失告警及退出码脚本已完成并通过真实数据验收。 |
| **免费体验一次性权益** | [`plan/2026-08-31_免费体验一次性权益改造方案.md`](../plan/2026-08-31_免费体验一次性权益改造方案.md) | `[已完成]` | 一次性体验标记、过期零额度、shadow/hard强制阻断、付费恢复与前端明确文案均已完成；数据库回归和页面回显通过。 |
| **语音中断取消与计费一致性** | [`plan/2026-08-31_语音中断取消与计费一致性方案.md`](../plan/2026-08-31_语音中断取消与计费一致性方案.md) | `[未完成]` Chrome交互待确认 | 聊天页/全屏页已用 AbortController 端到端取消 SSE 与 Provider；真实中断只结算0.40秒且后续稳定、预留归零，待自然麦克风点击光球复核。 |
| **微信与支付宝支付接入调研** | [`plan/2026-08-29_微信与支付宝支付接入调研方案.md`](../plan/2026-08-29_微信与支付宝支付接入调研方案.md) | `[未完成]` 调研完成，待资质与实施 | 已明确桌面微信 Native + 支付宝电脑网站支付、手机微信 H5 + 支付宝 WAP 的分阶段路线；订单、回调验签、幂等履约、退款、对账和自动续费边界已设计，尚未开通商户能力或编码。 |
| **链动小铺套餐兑换码售卖** | [`plan/2026-08-29_链动小铺套餐兑换码售卖接入方案.md`](../plan/2026-08-29_链动小铺套餐兑换码售卖接入方案.md) | `[未完成]` 真实闭环已验收 | ¥0.10 Plus真实订单已完成支付、自动发码、兑换、买家售后、商家主动退款和人工权益回滚；待未兑换退款/库存耗尽/错误码实单、商品文案修正、到账确认及API自动对账。 |
| **套餐硬额度与原子用量治理** | [`plan/2026-08-29_套餐硬额度与原子用量治理方案.md`](../plan/2026-08-29_套餐硬额度与原子用量治理方案.md) | `[未完成]` 内部hard灰度中 | A-C已完成本地回归；全局继续shadow，1个内部账号通过稳定用户ID白名单进入hard并由个人中心回显。待7天账单核对、边界验收、真实链动支付/退款/对账和真实百炼验收。 |
| **Local Storage 业务数据迁移 PostgreSQL** | [`plan/2026-08-28_LocalStorage业务数据迁移PostgreSQL方案.md`](../plan/2026-08-28_LocalStorage业务数据迁移PostgreSQL方案.md) | `[未完成]` 浏览器面板待复核 | 数据库表、HttpOnly 会话、迁移 API 和前端切换已完成；当前用户 5 条消息、1 份设置、1 条故事与有效 Session 已回读，待确认浏览器五个微光 Key 已清除。 |
| **聊天记录持久化与历史回显** | [`plan/2026-08-22_聊天记录持久化与历史回显方案.md`](file:///Users/fangzengxing/ZCodeProject/weiguang/plan/2026-08-22_%E8%81%8A%E5%A4%A9%E8%AE%B0%E5%BD%95%E6%8C%81%E4%B9%85%E5%8C%96%E4%B8%8E%E5%8E%86%E5%8F%B2%E5%9B%9E%E6%98%BE%E6%96%B9%E6%A1%88.md) | `[已完成]` | 数据表迁移（006）、异步非阻塞落库、REST 接口、历史回显与新对话重置已全链路交付并通过测试。 |
| **Qwen3.5-Flash 图片与视频多模态对话** | [`plan/2026-08-25_Qwen3.5-Flash图片视频多模态对话方案.md`](file:///Users/fangzengxing/ZCodeProject/weiguang/plan/2026-08-25_Qwen3.5-Flash%E5%9B%BE%E7%89%87%E8%A7%86%E9%A2%91%E5%A4%9A%E6%A8%A1%E6%80%81%E5%AF%B9%E8%AF%9D%E6%96%B9%E6%A1%88.md) | `[已完成]` | 后端 OSS 直传签名（`POST /api/uploads/presign-media`）、OpenAI 格式多模态 messages 转发、前端文件上传/预览/拖拽/粘贴、消息气泡媒体缩略图/视频预览、全屏大图查看及语音融合朗读已全链路交付并通过测试。 |
| **纯文本消息按需朗读** | [`plan/2026-08-25_纯文本消息按需朗读方案.md`](file:///Users/fangzengxing/ZCodeProject/weiguang/plan/2026-08-25_%E7%BA%AF%E6%96%87%E6%9C%AC%E6%B6%88%E6%81%AF%E6%8C%89%E9%9C%80%E6%9C%97%E8%AF%BB%E6%96%B9%E6%A1%88.md) | `[已完成]` | 后端 `POST /api/messages/tts`、前端按需合成请求、气泡播放/停止/加载态交互及语音状态机隔离已全链路交付并通过测试。 |
| **聊天截图提取对话记录** | [`plan/2026-08-26_聊天截图提取对话记录方案.md`](file:///Users/fangzengxing/ZCodeProject/weiguang/plan/2026-08-26_%E8%81%8A%E5%A4%A9%E6%88%AA%E5%9B%BE%E6%8F%90%E5%8F%96%E5%AF%B9%E8%AF%9D%E8%AE%B0%E5%BD%95%E6%96%B9%E6%A1%88.md) | `[已完成]` | 数据表迁移（003）、Qwen3.5-Flash 视觉结构化提取、REST 接口、前端双栏原图对照与编辑审核弹窗、媒体占位符补充及确认导入已全链路交付并通过端到端测试。 |
| **官方 MiniCPM-o-Demo 替换** | [`plan/2026-08-23_官方MiniCPM-o-Demo替换方案.md`](../plan/2026-08-23_官方MiniCPM-o-Demo替换方案.md) | `[未完成]` 浏览器语音待验收 | 现有 Vue UI 已接入官方 `/v1/realtime`；远端 Gateway/Worker/backend 健康，Chat/Audio 协议验证通过，等待 Chrome 自然语音验收。 |
| **ElevenLabs 纯 API 语音迁移** | [`plan/2026-08-23_ElevenLabs纯API语音克隆与端到端对话方案.md`](../plan/2026-08-23_ElevenLabs纯API语音克隆与端到端对话方案.md) | 历史备选 | Speech Engine + 外部 LLM API 方案未实施；已被浏览器转写 + 百炼 LLM/TTS 当前路线替代。 |
| **SSH 隧道自动重连与守护化** | `deploy/opensource/` | 待规划 | 计划将前台 SSH 脚本改造为 launchd 或 autossh 守护进程，提升本地开发体验。 |
| **参考音频对象存储迁移** | `internal/openvoice/` | 待规划 | 计划将 PostgreSQL `BYTEA` 中的音频文件平滑迁移至 MinIO/S3 兼容对象存储。 |
| **百炼 + OSS 国内云 API 迁移** | [`plan/2026-08-23_云API语音对话架构与分阶段实施方案.md`](../plan/2026-08-23_云API语音对话架构与分阶段实施方案.md) | `[未完成]` | 百炼 LLM/TTS、OSS 签名 URL 已真实验证；克隆 API 前端上传链路已接入并完成生产构建。聊天和全屏语音已切换到 `/api/chat-and-tts/stream`，文本增量和 PCM 分片已通过真实短句 smoke；仍待真实音频克隆和 Chrome 长回复端到端验收。 |
| **产品套餐与商业化计费** | [`plan/2026-08-27_产品套餐与商业化计费方案.md`](../plan/2026-08-27_产品套餐与商业化计费方案.md) | `[未完成]` | 已形成免费体验、Plus 59 元、Pro 129 元的首版套餐，明确 AI 回复、AI 语音时长、多模态、音色槽位、单位经济和分阶段计费方案；真实用量埋点、影子配额、支付退款与对账尚未实现。 |
| **浏览器转写保留与套餐前端改造** | [`plan/2026-08-27_浏览器转写保留与套餐前端改造方案.md`](../plan/2026-08-27_浏览器转写保留与套餐前端改造方案.md) | `[未完成]` | 已决定第一阶段不接 Qwen/MiMo ASR，保留浏览器 SpeechRecognition；已设计 `/pricing`、个人中心用量、导航改造、影子用量接口和分阶段验收，运行代码尚未修改。 |
### 验收复测：聊天截图提取对话记录（2026-08-26）

- 基础构建、后端编译、健康检查、PostgreSQL 导入表和前端入口通过。
- 图片签名上传、Qwen 图像理解流和导入批次用户隔离 smoke 通过；非聊天图片返回可控失败状态。
- 真实聊天截图、真实视频以及多图重叠去重/乱序纠正/缺口报告尚未完成独立验收；当前功能状态应视为“已交付，待素材验收”，不应据此宣称全部通过。
### ISSUE-26: Qwen 返回 null 字段导致整张截图提取失败
- **问题现象**：多张截图导入时，某条消息返回 `speaker: null` 或 `text: null`，Pydantic 校验失败，整张截图被记为提取异常，最终只保留其他截图的消息。
- **根因**：`ExtractedMessageItem` 原先要求 `speaker`、`text` 必须是字符串，没有兼容 Qwen 对不可读字段返回 JSON `null` 的情况。
- **处理动作**：在 `backend/providers/screenshot_extractor.py` 增加 `model_validator(mode="before")`，将空字段归一化为“对方”、`[图片]`/`[视频]`/`[语音]`/`[未识别文本]`，同时标记 `needs_review=true`；其他非法字段降级为 `unknown` 或低置信度。
- **验证方式**：`scripts/test_screenshot_extractor_parse.py` 回归测试通过；后端 compileall、前端 build、`/api/health` 均通过。
### ISSUE-27: 截图审核页按图切换 OCR 记录与原图放大

- **问题现象**：多张截图的 OCR 消息全部堆叠在右侧；底部缩略图只能切换左侧原图，原图放大层在原生 dialog 上方无法正常显示。
- **根因**：审核列表没有按 source_attachment_id 过滤；全屏预览通过 Teleport 渲染到 body，可能被原生 dialog top layer 覆盖。
- **处理动作**：按当前截图筛选右侧消息；服务端附件 ID 与本地预览合并；缩略图支持切换/双击放大；全屏预览移入 dialog top layer，并保留缩放和左右导航。
- **验证方式**：前端 npm run build、后端 compileall、/api/health 均通过。

### ISSUE-28: 故事星宇节点点击出现双弹窗与连续拖拽失效问题

- **问题现象**：
  1. 点击故事星球上的星子节点时，页面同时出现了旁边的悬浮星语浮笺（`.node-whisper-card`）与右下角的聚光灯详情卡片（`.spotlight-card`），造成两个弹窗重叠杂乱；
  2. 鼠标拖拽星球时仅第一次生效，后续再次拖拽无法旋转。
- **根因**：
  1. 星子节点在被点击后获得了 DOM focus 状态（`:focus-within`），且鼠标仍处于 hover 范围内，原样式未设置选中状态下的互斥隐藏规则，导致悬浮卡片与聚光灯卡片同时展示；
  2. 拖拽移动与松开事件原先仅绑定在 stage 内部元素上，当鼠标快速移动或在非舞台区域释放时未能触发 `mouseup`，导致 `isDragging` 标志位未能及时复位；且点击与拖拽未做位移阈值防误触隔离。
- **处理动作**：
  1. 在 `StoriesView.vue` 模板中添加 `v-if="!selectedStory || selectedStory.id !== pt.story.id"`，并在 CSS 中严格定义 `.story-node.is-selected .node-whisper-card, .story-node:focus .node-whisper-card { display: none !important; }`，实现选中态与悬浮态的严格互斥；
  2. 将 `mousemove`、`mouseup`、`touchmove`、`touchend` 全局挂载至 `window` 并在组件卸载时清理，保证全局拖拽生命周期的确定性；
  3. 增加 `totalDragDist` 累加与 `hasDragged` 标记，当拖拽位移超过 4px 时判定为旋转漫游，阻止触发星子的点击事件，并在点击背景空白处时平滑关闭聚焦卡片。
- **验证方式**：
  1. 前端 `npm run build` 0 错误编译通过（500ms）；
  2. 浏览器打开 `/stories`，连续多次拖拽、漫游旋转顺畅无卡死；
  3. 单击任意星子仅展示单个聚焦卡片，彻底消除双重弹窗。

### ISSUE-29: 故事星宇未登录投递拦截与投递后星球数据丢失问题

- **问题现象**：
  1. 在未登录状态下允许打开投递寄语表单并直接投递；
  2. 投递完成后，3D 星球上的原有默认故事数据全部丢失（星子聚集在屏幕边缘或消失）。
- **根因**：
  1. 投递入口（顶部导航与底部控制栏）及 `submitStory` 方法未增加 `auth.isLoggedIn` 鉴权校验；
  2. 流星动画系统中由于对十六进制色值的正则替换存在非标准格式（`rgba(#ecd7af`），Canvas 在调用 `addColorStop` 时抛出 `DOMException: The value provided could not be parsed as a color` 异常，导致 `requestAnimationFrame` 的 3D 渲染动画循环中断崩溃。动画中断后，新生成的星子坐标停留在 `(screenX: 0, screenY: 0)` 默认值，视觉上表现为原有星子全部丢失；
  3. `submitStory` 中缺少对既有 `defaultStories` 数组的安全解构合并与去重处理。
- **处理动作**：
  1. 投递入口统一绑定 `handleOpenWrite`，在未登录时自动唤起全局登录弹窗并触发吐司提示；在 `submitStory` 中增加二次拦截保障；
  2. 重构流星粒子色值模型为标准 `RGB` 三元组（`[r, g, b]`），彻底杜绝 Canvas 渐变解析异常；
  3. 为 `updateAndRender()` 增加 `try...catch...finally` 异常隔离，确保 3D 动画渲染循环永不崩溃终止；
  4. 优化 `loadCustomStories()` 与 `submitStory()` 数据合并逻辑，确保新提交的故事与 12 个默认故事稳定共存且实时投影。
- **验证方式**：
  1. 前端 `npm run build` 0 错误编译通过（609ms）；
  2. 未登录状态下点击“投递寄语”，自动唤起登录弹窗并友好提示“请先登录后再投递你的微光心声”；
  3. 登录后投递新寄语，新故事与既有 12 个微光故事同时在 3D 星球上稳定发光旋转。

### ISSUE-30: 按需朗读暂停后从头播放与重复远端加载

- **问题现象**：AI 消息朗读过程中点击按钮会停止并清零进度；再次点击从头播放。音频只保存临时远端 URL，页面刷新后会重新请求 `/api/messages/tts` 和远端媒体。
- **根因**：`playOrSynthesizeMessage` 的停止分支执行 `pause()`、`currentTime = 0` 并销毁 `Audio`；消息状态未记录当前播放器归属，也没有跨刷新的浏览器持久音频缓存。
- **处理动作**：
  1. 增加当前手动播放器消息 ID、按消息 Blob URL 缓存和并发加载去重；
  2. 同消息播放中点击只暂停并保留进度，再次点击复用原 `Audio` 实例续播；播放结束后进度归零但保留缓存；
  3. 首次播放才请求 TTS 和远端音频，校验 HTTP 状态、`audio/*` 类型与非空 Blob 后写入 Cache Storage；刷新后按用户、消息、正文、音色和角色指令生成的稳定键恢复；
  4. 缓存最多保留 30 条，普通刷新只释放内存 Blob URL，新对话清理当前用户持久缓存；切换消息和实时语音仍独占停止旧播放器。
- **验证方式**：前端 `npm run build` 通过；真实 TTS 媒体 Range 请求返回 `206`、`audio/x-wav`、允许跨域且 Content-Range 正常。Chrome 暂停续播、刷新命中 Cache Storage 与 Network 零新增请求仍待用户登录态页面复测。

### ISSUE-31: Local Storage 导致账户与历史数据库断链

- **问题现象**：当前页面只能看到浏览器 `weiguang.local.chat-history.v1` 中的少量消息，旧 PostgreSQL 历史未显示；账户、昵称、角色设置和聊天记录依赖 Local Storage，刷新/清理浏览器或切换设备会丢失。
- **根因**：此前切换官方语音链路时把账户、设置和历史契约临时改成 Local Storage；当前 FastAPI 没有数据库用户会话与聊天历史 API，前端 `fetchChatMessages()` 完全绕过 PostgreSQL。
- **处理动作**：
  1. 新增 `005_app_data_persistence.sql` 与 `AppDataStore`，持久化用户、Session、设置、会话、消息和遗留故事；
  2. 新增 `/api/auth/*`、`/api/voice-settings`、`/api/chat-history`、`/api/stories` 与本机一次性迁移接口；
  3. 前端切换为 Cookie + 数据库 API，仅保留一次性 Local Storage 读取/删除适配器；迁移顺序固定为“事务写入 → API 回读 → 删除五个微光 Key”；
  4. 当前浏览器用户已自动迁入数据库：5 条消息、1 份角色设置、1 条遗留故事，数据库会话有效；旧 `weiguang-postgres-1` 的 38 条历史保持原样，未在身份未确认时自动合并。
- **验证方式**：后端 compileall、前端 `npm run build`、`scripts/test_app_data_persistence.py` 通过；HTTP smoke 验证迁移计数、Cookie 恢复、历史/设置/故事回读和未登录 `401`；当前数据库行数与有效 Session 已回读。Chrome Application 面板中的五个 Key 清除状态待用户刷新后最终复核。

### ISSUE-32: psycopg3 批量创建兑换码调用位置错误

- **问题现象**：首次运行兑换码 PostgreSQL 闭环时，批次记录创建后在批量插入卡密阶段抛出 `AttributeError: 'Connection' object has no attribute 'executemany'`，整批事务回滚。
- **根因**：当前项目使用 psycopg3；批量 `executemany` 属于 Cursor API，不是 Connection API。
- **处理动作**：在同一数据库事务内创建游标，并改为 `cursor.executemany(...)` 批量写入兑换码哈希；保留批次和卡密的原子提交/失败回滚。
- **涉及文件**：`backend/billing_store.py`。
- **验证方式**：纯逻辑测试、真实 PostgreSQL 批次创建/兑换/重复兑换、FastAPI 注册与 Pro 兑换闭环均通过；同一个码并发提交 100 次只有 1 次成功、99 次被拒绝，测试数据已清理。

### ISSUE-33: 独立购买页未使用路由变量导致构建失败

- **问题现象**：新增 `PurchaseView.vue` 后执行 `npm run build`，TypeScript 报错 `TS6133: 'router' is declared but its value is never read`。
- **根因**：页面只读取当前路由参数，没有执行编程式跳转，却同时创建了 `useRouter()` 返回值。
- **处理动作**：移除未使用的 `useRouter` 导入与变量，保留 `useRoute` 获取套餐参数。
- **验证方式**：`vue-tsc -b && vite build` 通过；构建产出独立 `PurchaseView` JS/CSS，Plus续期提示与Pro跨档拦截已在当前登录态Chrome验证。

### ISSUE-34: 客户端用户 Header 可伪造额度归属与 Provider 身份

- **问题现象**：旧 Provider 入口在无 Session 时接受 `X-Weiguang-User-ID`，脚本可切换到其他用户额度账本。
- **根因**：开发期身份兼容 Header 被生产计费入口复用，用户 ID 未完全来自服务端会话。
- **处理动作**：所有 LLM、TTS、多模态、音色和截图入口统一使用 HttpOnly Session；生产 Cookie 强制 Secure，写请求校验可信 Origin，Local Storage 迁移仅 development/test 可用。
- **验证方式**：无 Cookie 与伪造 Header 均在 Provider 前返回 401；恶意 Origin 返回 403；production 显式 `COOKIE_SECURE=false` 启动失败；端点 mock 通过。

### ISSUE-35: 幂等请求可重复调用 Provider 与并发额度超卖

- **问题现象**：早期同一 `request_id` 命中已有用量行后仍可能继续调用 Provider；并发请求存在先查剩余、后扣减的超卖风险。
- **根因**：幂等只约束流水唯一键，没有把“谁可以执行 Provider”纳入同一事务合同。
- **处理动作**：增加 PostgreSQL 行锁与 request advisory lock；首次预留返回 `proceed=true`，reserved/completed/expired 重放在 Provider 前返回 409，只有显式 released 可重试。TTL 未知结果进入 terminal `expired`，迟到确认仍入账。
- **验证方式**：同一 ID 100 并发仅 1 次 Provider；剩余 50 次时 100 个不同请求仅 50 个成功；hard/shadow、跨用户、迟到确认与数据库不可用失败关闭回归通过。

### ISSUE-36: 流式部分输出、多模态历史与语音时长漏记

- **问题现象**：图片/视频放在较早 messages 可绕过计数；文字或 PCM 已下发后取消会释放额度；实际语音超过预留时可能已播放却不入账。
- **根因**：媒体只统计最后一条消息，流式结算只认完整 done，TTS 结果后计量与预估之间存在差额。
- **处理动作**：统计发给 Provider 的全部 messages；任意 text delta/PCM 下发后即确认；流式 PCM 按预留字节上限裁剪并关闭上游，原始 Provider/交付/超额量写入 raw_usage；非流式仍如实记录实际量。
- **验证方式**：早期消息媒体、delta 后失败/取消、PCM 后失败/取消、超预留裁剪与供应商错误脱敏 mock 通过。非流式 TTS 仍是结果后计量边界，方案保持未完成。

### ISSUE-37: 同档续费把两个30天合并为一个额度周期

- **问题现象**：再次兑换同档套餐会直接延长 `period_end`，第二个30天无法获得独立新额度。
- **根因**：访问授权到期日与当前用量周期共用同一字段。
- **处理动作**：新增 `access_end`，当前周期留在 `user_subscriptions`，未来30天写入 `subscription_grants`；请求前行锁切换当前周期。
- **验证方式**：同档续费保持当前重置日并延长访问权；周期边界100并发只切换一次，新周期用量归零；跨档拒绝不消耗码。

### ISSUE-38: Pro 3音色与跨系统删除状态不一致

- **问题现象**：旧 `VoiceCloneStore.save()` 会停用先前音色，Pro 实际只能保留1个；远端创建/删除成功而本地失败时会遗留孤儿或永久占槽。
- **根因**：只有最终 `voice_clones.active`，没有跨百炼与 PostgreSQL 的持久操作状态和恢复租约。
- **处理动作**：Pro 保留全部 active 音色并提供列表/选择/删除；新增 `voice_clone_operations`，记录 create/delete、远端成功、本地待办、补偿待办与 claim lease；请求前和列表读取有界 reconcile，未清理孤儿持续占用槽位。
- **验证方式**：真实本地 PostgreSQL 验证3个 active 音色、所有权隔离、补偿孤儿保槽、并发 claim 仅一次远端删除、远端已删仅重试本地停用、测试数据清理回读为0；未调用真实百炼删除。

### ISSUE-39: 全局 hard 开关无法只灰度内部账号

- **问题现象**：直接设置 `BILLING_ENFORCEMENT_MODE=hard` 会同时影响全部用户，无法安全地在一个内部账号先做额度验收。
- **根因**：计费模式只有全局值，没有按稳定用户 ID 的最小覆盖层。
- **处理动作**：新增 `BILLING_HARD_USER_IDS` 逗号白名单；BillingStore 和 API 失败关闭均按用户计算有效模式，前端继续读取服务端 summary，不接收邮箱、密码或前端 mode 参数。
- **验证方式**：真实本地 PostgreSQL 验证同一全局 shadow 下，白名单用户到达上限被阻断、普通用户仍可 shadow；数据库不可用时白名单用户在 Provider 前返回503；当前内部账号个人中心回显“硬额度已开启”。

### 验收复测：链动小铺真实支付、兑换、退款与权益回滚（2026-08-31）

- 真实订单 `LD260831DVXNUR`：¥0.10，微信支付成功，链动小铺自动发出Plus卡密；
- 微光兑换后访问权从2026-10-28顺延到2026-11-27，当前周期与真实用量保持不变；
- 买家端当日售后提交成功，商家端回显资金冻结；商家主动退款后订单为“已退款”、售后为“买家胜诉”；
- 本次退款对应兑换码已 `revoked`、未来grant已删除，访问权恢复到2026-10-28；当前周期与AI回复/语音/图片/视频/截图用量未改变；
- 完整卡密、联系方式、收款码、投诉密码和支付渠道流水未写入进度文档；
- 另有1笔因桌面支付跳转被拦截产生的未付款订单，未发码、未发权益，等待平台自动关单。

未完成边界：买家收款账户实际到账仍需人工确认；未兑换退款、库存耗尽、错误卡密的真实外部订单测试和链动API自动对账尚未完成。

### ISSUE-40: 后台启动命令随自动化终端退出导致服务立即停止

- **问题现象**：普通 `nohup ... &` 在启动命令内显示 FastAPI/Vite 健康，但命令会话结束后 `8080/5173` 立即不可访问，用户只能再次要求人工启动。
- **根因**：自动化终端会在命令结束时清理其子进程；`nohup` 只能忽略挂断信号，不能脱离该进程生命周期管理边界。
- **处理动作**：新增 `scripts/start-weiguang.zsh`，使用 macOS 原生 `launchctl submit` 启动缺失的 FastAPI/Vite；PostgreSQL复用现有Docker Compose，服务健康时直接跳过。日志写入 `.run-logs/`。
- **验证方式**：真实停止 `8080/5173` 后脚本成功恢复；后续独立命令再次访问仍正常，后端 `status=ok`、前端首页可用；重复执行不新增进程，从 `/tmp` 调用也能正确定位项目。

### ISSUE-41: 语音对话消息首次手动朗读误报音频格式无效

- **问题现象**：语音对话生成的 AI 消息第一次点击朗读显示“语音音频格式无效”，第二次点击可以正常播放。
- **根因**：实时链路按句返回 24 kHz、16-bit、单声道 `.pcm` 音频及多个 `audio.url`；页面只保留最后一个 PCM URL，而手动播放器只接受 WAV。首次点击因此拒绝 PCM，随后回退 `/api/messages/tts` 重新合成整段 WAV；第二次虽可播放，却已不是实时听到的原音频。
- **官方依据**：阿里云百炼实时 TTS 支持 PCM 流式输出，并要求收到音频增量后立即播放；项目当前实时链路明确使用 24 kHz PCM。
- **处理动作**：`PCMStreamPlayer` 在播放时同步保留已交付的全部 PCM 分片，流结束后按原顺序封装为单个 WAV 并写入消息 Cache Storage；播放键直接复用这份字节完全相同的缓存，不再依赖最后一个分句 URL，也不再二次合成。
- **涉及文件**：`frontend/src/lib/audioResponse.ts`、`frontend/src/lib/pcmStreamPlayer.ts`、`frontend/src/views/ChatView.vue`、`frontend/tests/audioResponse.test.ts`。
- **验证方式**：4 条 Node 测试通过，其中 PCM 多分片合并测试回读 WAV 数据区与输入字节逐字节一致；`npm run build` 通过。真实自然语音后的播放键音频一致性仍需在可操作麦克风的 Chrome 页面做最后听感复核。

### ISSUE-42: 简单语音问题等待近 30 秒才开始回复

- **问题现象**：用户说“你觉得一加一等于多少”后，文字和语音需要接近 30 秒才开始返回。
- **根因**：当前 `qwen3.5-flash` 是混合思考模型且默认开启思考；项目未显式关闭，简单陪伴对话也会先执行不可见思考。真实分段测量中 LLM 首字耗时 16.627 秒，而同一句 TTS 首包仅 0.518 秒，瓶颈不在音频播放器或 TTS。
- **官方依据**：阿里云百炼文档明确 `qwen3.5-flash` 默认开启思考，OpenAI Python SDK 需通过 `extra_body={"enable_thinking": false}` 关闭；实时 TTS 正常首包约 500ms。
- **处理动作**：聊天的流式与非流式 LLM 调用统一显式关闭思考，保留原模型、流式文本、句子队列和 TTS 参数不变。
- **涉及文件**：`backend/providers/qwen_llm.py`、`scripts/test_qwen_llm_options.py`。
- **验证方式**：参数回归检查、额度端点 mock、后端编译和前端构建全部通过；真实供应商复测 LLM 首字 0.386 秒、首句 0.418 秒、TTS 首包 0.431 秒，端到端首声约 0.849 秒；经本地完整 `/api/chat-and-tts/stream`、会话鉴权、计费预留与 SSE 转发后，首字 429ms、首个 `audio.delta` 1041ms。

### ISSUE-43: 实时语音回复期间提前显示手动播放键

- **问题现象**：AI 仍在实时生成或播放语音时，当前消息已显示手动朗读按钮，容易让用户误以为可以重复播放或打断当前音频。
- **处理动作**：增加仅存在于前端内存的 `voiceReplying` 状态；从语音请求开始到全部音频播放结束或异常退出，隐藏所有朗读按钮，避免旧消息的播放操作打断当前实时回复。文字对话不受影响。
- **涉及文件**：`frontend/src/views/ChatView.vue`。
- **验证方式**：`npm run build` 通过，Vue 类型检查与生产构建无错误。

### ISSUE-44: 正在聆听时手动播放历史音频造成语音回灌

- **问题现象**：语音回复结束并重新进入“正在聆听”后，历史消息的朗读按钮恢复；播放音频会被 Chrome `SpeechRecognition` 当作新的用户输入。
- **历史依据**：ISSUE-19 已处理实时 AI 外放期间的识别器门控，但手动朗读入口和启动语音会话时没有复用同一保护边界。
- **处理动作**：整个语音会话非空闲期间隐藏朗读按钮；播放函数入口再次检查 `voiceActive/orbState` 并直接拒绝；开启语音会话前先停止任何正在播放或加载的手动音频。
- **涉及文件**：`frontend/src/views/ChatView.vue`。
- **验证方式**：`npm run build` 通过；模板可见性、播放入口和语音启动三个边界均已静态回读。

### ISSUE-45: 本地打断只停播放器但不中断上游请求与扣量

- **问题现象**：AI 语音播放中点击打断只停止 `PCMStreamPlayer`，浏览器仍继续读取 SSE，服务端继续生成后续 TTS；被打断的回合没有完整缓存，再次朗读还会发起新的计费 TTS。
- **根因**：`streamChatAndTTS` 已支持 `AbortSignal`，但聊天页和全屏语音页均未创建或传入 `AbortController`；全屏页还被 `if (busy) return` 直接阻止打断。
- **官方依据**：Web `AbortController.abort()` 可同时终止 fetch、响应体消费和流；Python `asyncio` 取消会向任务抛出 `CancelledError`，清理后应继续传播。现有后端结算 `finally` 已符合该契约。
- **处理动作**：每个语音回合创建独立控制器；光球打断、关闭语音、退出页面时 abort；主动中断不显示接口错误，保留已返回文字但不缓存残缺音频；全屏页恢复真实可用的“轻触打断”。
- **涉及文件**：`frontend/src/views/ChatView.vue`、`frontend/src/views/VoiceView.vue`、`scripts/test_quota_endpoints.py`。
- **验证方式**：前端生产构建和额度端点 mock 通过，取消后 Provider TTS 迭代器关闭；真实登录态 SSE 首音频 1.334 秒到达，收到19,200字节后中断，用量从266.49增至266.89秒（精确0.40秒），随后两次读取保持266.89秒，预留为0。Chrome自然麦克风光球交互待用户最终复核。

### ISSUE-46: 免费体验到期后每 30 天自动续发额度

- **问题现象**：免费用户周期到期后，`_ensure_current_cycle_locked` 会创建新的 30 天 free 周期；付费套餐到期后也会回到免费计划，和“一次性体验”的产品规则冲突。
- **根因**：订阅表没有持久化“已领取免费体验”，周期切换只能把无付费 grant 的账号统一重置为 free；shadow 模式还会绕过零额度限制。
- **处理动作**：新增 `free_trial_started_at` 并回填全部现有账号；新账号只在首次订阅创建时获得一次免费周期（2026-09-08起为7天）；到期无grant进入 `expired`，额度上限归零且shadow/hard均阻断；兑换付费后恢复，付费到期不返免费。套餐页和个人中心同步展示一次性与已结束状态。
- **涉及文件**：`internal/auth/migrations/008_one_time_free_trial.sql`、`backend/billing_store.py`、`scripts/test_quota_atomicity.py`、`frontend/src/types/index.ts`、`frontend/src/stores/auth.ts`、`frontend/src/views/PricingView.vue`、`frontend/src/components/AccountDialog.vue`。
- **验证方式**：真实本地 PostgreSQL 原子测试通过，覆盖单次周期、跨两期不续、shadow强制阻断、Plus恢复及付费后再次过期；数据库体验标记空值0；前端生产构建通过，浏览器回显“每个账号可免费体验一次”“首次7天”“开始体验一次”。

### ISSUE-47: 缺少生产用量、成本和异常告警入口

- **问题现象**：已有套餐用量流水，但只能按单个用户查看；无法回答全局24小时调用量、失败/取消率、Token/字符成本、悬挂预留和预算是否超限。
- **根因**：`usage_events.raw_usage` 已保留供应商原始用量，却没有全局聚合、价格配置、内部只读端点或可调度告警检查器。
- **处理动作**：复用 BillingStore 聚合1–168小时用量；按百炼北京公开价估算Qwen3.5-Flash和Qwen-Audio-TTS成本；增加预算、失败率、过期/悬挂预留、原始用量缺失告警；端点仅内部hard白名单可读，脚本用退出码供launchd/cron调度。
- **涉及文件**：`backend/config.py`、`backend/billing_store.py`、`backend/app.py`、`.env.example`、`scripts/check_monitoring.py`、`scripts/test_quota_atomicity.py`、`scripts/test_quota_endpoints.py`。
- **验证方式**：真实7天汇总88个请求、失败/取消率11.36%、成本估算0.238975元，19个历史请求缺少成本遥测并产生告警；管理员实际API 200、普通账号mock 403；脚本无告警返回0、有告警返回2；PostgreSQL回归、编译和健康检查通过。

### ISSUE-48: 运营管理与生产监控缺乏统一 Web 可视化界面

- **问题现象**：仅有命令行脚本 `scripts/check_monitoring.py`，缺乏可视化 Web 仪表盘；无法直观查阅 24h/7d 调用趋势、各模型成本拆分、用户用量排行、卡密交易兑换流水、用户资料/备注编辑、账号禁用（立即吊销会话）以及故障排查对话正文审查。
- **根因**：后端缺少针对运营管理的多维聚合 API（分桶时序、模型拆分、用户级 Token 统计、交易账本、对话回溯）；数据库缺少用户状态字段 (`status`, `disabled_at`, `admin_note`)；前端缺少深色管理后台 UI 及轻量原生 SVG 时序图表。
- **处理动作**：
  1. **数据库层**：应用 `internal/auth/migrations/009_user_management_and_admin.sql`，在 `app_users` 增加 `status`（'active' | 'disabled'）、`disabled_at`、`admin_note` 及性能索引。
  2. **后端鉴权与存储**：`app_data_store.py` Session 校验加入 `u.status = 'active'` 过滤（被禁用用户会话立即失效）；实现用户列表搜索/筛选/分页、详情、资料与备注更新、禁用（事务内删除会话）、启用、对话会话与消息正文读取接口；`billing_store.py` 增加 `series` 动态时间桶聚合、`models` 按模型拆分、`get_admin_costs_summary` 用户 Token 聚合、`get_admin_transactions` 交易账本（实付标明“渠道未同步”）。
  3. **后端 API 路由**：`backend/app.py` 引入 `require_admin_user_id` 依赖，提供 `/api/admin/*` 全套监控与管理接口，严格对非管理员返回 403。
  4. **前端管理控制台**：
     - `MonitoringTrend.vue`：零依赖原生 SVG 曲线/面积图，支持成本和调用量双线对比。
     - `MonitoringView.vue`（`/admin/monitoring`）：4大核心 KPI、实时告警面板、SVG 时序走势、6类用量进度条、模型消耗表、30s自适应倒计时与可见性监听。
     - `AdminCostsView.vue`（`/admin/costs`）：Token/TTS 总览、费率说明、用户级消耗排行与遥测完整性。
     - `AdminTransactionsView.vue`（`/admin/transactions`）：分页交易账本。
     - `AdminUsersView.vue` / `AdminUserDetailView.vue`（`/admin/users`）：用户管理、资料/备注编辑、禁用确认弹窗、会话与消息正文（含附件元数据，不自动加载私有媒体）安全审查。
     - `AccountDialog.vue`：为管理员展示“⚙️ 运营管理后台”导航入口。
- **涉及文件**：`internal/auth/migrations/009_user_management_and_admin.sql`、`backend/app_data_store.py`、`backend/billing_store.py`、`backend/app.py`、`frontend/src/types/index.ts`、`frontend/src/api/index.ts`、`frontend/src/components/MonitoringTrend.vue`、`frontend/src/layouts/AdminLayout.vue`、`frontend/src/views/MonitoringView.vue`、`frontend/src/views/AdminCostsView.vue`、`frontend/src/views/AdminTransactionsView.vue`、`frontend/src/views/AdminUsersView.vue`、`frontend/src/views/AdminUserDetailView.vue`、`frontend/src/router/index.ts`、`frontend/src/components/AccountDialog.vue`。
- **验证方式**：
  - 执行 `scripts/test_admin_endpoints.py` 全量通过（验证 24h/168h 监控、costs、transactions、users、user detail、patch profile、disable/enable、self-disable 拦截、session 撤销、非管理员 403）；
  - `npm run build` 前端构建与 `vue-tsc` 类型检查 100% 成功；
  - `scripts/check_monitoring.py --hours 24` 与 `--hours 168` 回读生产真实数据正常。

---

### ISSUE-49: 管理后台与客户端前端混编导致安全边界模糊与打包冗余

- **问题现象**：运营管理后台代码内嵌在客户端应用 `frontend/` 中，普通用户的前端 Bundle 中打包了内部运维路由、管理 API 调用与审查组件；且缺乏独立的管理员登录门禁。
- **根因**：原方案将 `/admin/*` 路由挂在客户端工程下，未按照企业级应用的最佳实践将管理端与客户端在物理工程级别隔离。
- **处理动作**：
  1. **新建独立工程 `frontend-admin/`**：
     - 配置独立的 `package.json`、`vite.config.ts`（端口 `:5174`，代理 `/api` 至 `127.0.0.1:8080`）、`tsconfig.json` 与 `index.html`；
     - 建立专用的管理员登录视图 `LoginView.vue`、`AdminLayout.vue`、`MonitoringView.vue`、`AdminCostsView.vue`、`AdminTransactionsView.vue`、`AdminUsersView.vue`、`AdminUserDetailView.vue` 与 `MonitoringTrend.vue`；
     - `stores/auth.ts` 与 `router/index.ts` 形成完整的独立鉴权门禁（未登录跳 `/login`，非管理员登录后提示并拦截）。
  2. **彻底清理客户端工程 `frontend/`**：
     - 移除全部 admin 视图、布局与图表组件；
     - 清理 `frontend/src/router/index.ts` 中的 `/admin` 路由；
     - 清理 `frontend/src/api/index.ts` 中的 admin 接口；
     - 个人中心 `AccountDialog.vue` 中“⚙️ 运营管理后台”改为外链形式打开 `http://localhost:5174`。
  3. **服务编排更新**：`scripts/start-weiguang.zsh` 统一调度 `com.weiguang.frontend.admin`（`:5174`）并进行健康检查。
- **涉及文件**：
  - `frontend-admin/` 全部工程文件（`package.json`, `vite.config.ts`, `src/*`）；
  - `frontend/src/router/index.ts`；
  - `frontend/src/api/index.ts`；
  - `frontend/src/components/AccountDialog.vue`；
  - `scripts/start-weiguang.zsh`。
- **验证方式**：
  - `cd frontend-admin && npm run build` 成功，0 错误；
  - `cd frontend && npm run build` 成功，0 错误；
  - `curl -s -I http://localhost:5174/` 返回 HTTP 200。

---

### ISSUE-50: 独立后台登录时后端报“请求来源不受信任”拦截 (403 untrusted_origin)

- **问题现象**：在 `http://localhost:5174/login` 提交登录请求时，前端提示红字报错“请求来源不受信任”。
- **根因**：FastAPI 后端针对写操作（POST/PUT/DELETE）启用了 `require_trusted_origin` 中间件，而开发环境可信来源白名单 `settings.trusted_origins` 原先仅配置了 `http://localhost:5173` 与 `http://127.0.0.1:5173`，未包含独立后台工程的 `5174` 端口。
- **处理动作**：在 `backend/config.py` 的 `_trusted_origins` 开发环境列表中加入 `http://localhost:5174` 与 `http://127.0.0.1:5174`。
- **涉及文件**：`backend/config.py`。
- **验证方式**：模拟带有 `Origin: http://localhost:5174` 的 `POST /api/auth/login` 请求，成功返回 HTTP 200 并下发 `weiguang_session` Cookie。

---

### ISSUE-51: 管理后台登录时 API 响应解构错误导致管理员误判拦截

- **问题现象**：输入正确的管理员账号密码后，前端显示红字报错“该账号非系统指定管理员，无权进入运营管理后台。”
- **根因**：后端 `POST /api/auth/login` 直接返回 Profile 对象，而 `frontend-admin/src/stores/auth.ts` 错误地解构了 `res.profile`（导致 `profile.value` 为 `undefined`），使 `isAdmin` 计算属性返回 `false` 并触发拦截。
- **处理动作**：修正 `frontend-admin/src/api/index.ts` 中 `login` 函数的返回类型为 `Promise<Profile>`，并在 `stores/auth.ts` 中直接将返回值赋予 `profile.value`。
- **涉及文件**：`frontend-admin/src/api/index.ts`、`frontend-admin/src/stores/auth.ts`。
- **验证方式**：`frontend-admin` 生产构建与类型检查 100% 成功，账号登录后正确解析 `is_admin: true` 并放行进入控制台。

---

### ISSUE-52: 聊天历史图片附件加载 403 Forbidden (`Request has expired`, `0002-00000069`)

- **问题现象**：在主聊天页面 (`localhost:5173/chat`) 刷新或加载历史记录时，历史消息中包含的图片附件请求失败，浏览器网络面板报 `403 Forbidden`，响应头返回 `X-Oss-Ec: 0002-00000069`，错误内容为 `Request has expired`。
- **根因**：
  1. 用户发送图片时，后端签发了有效期通常为 15 分钟的临时 GET URL，并将其直接持久化保存在数据库 `chat_messages.attachments` JSON 字段中。
  2. 随后当用户刷新页面或在数小时后回看历史消息时，`GET /api/chat-history` 与管理员消息审查接口直接将数据库里已失效的历史签名 URL 返回给了前端。
  3. 阿里云 OSS 对私有 Bucket 的签名时间戳进行严格校验，超期后判定为过期链接并直接返回 HTTP 403。
- **处理动作**：
  1. 在 `backend/app.py` 中编写 `_enrich_messages_attachments(messages)` 辅助函数；在 `GET /api/chat-history` 及 `GET /api/admin/conversations/{conversation_id}/messages` 返回前，自动检测带 `object_key` 的消息附件；
  2. 借助 `OSSProvider.presign_object_download(att["object_key"])` 动态生成当前有效的私有下载签名，并写入 `download_url`；
  3. 前端 `ChatView.vue` 图片渲染优先采用 `download_url`，同时保留 `@error` 优雅容错。
- **涉及文件**：`backend/app.py`、`frontend/src/views/ChatView.vue`。
- **验证方式**：编写 `scratch/test_attachment_and_distill.py` 单元测试，模拟带已过期旧签名的附件数据，验证接口返回的附件 `download_url` 成功刷新为未来有效时间戳的私有签名链接。

### ISSUE-53: OCR 人设字段未回填且将“系统消息”误作角色名称

- **问题现象**：OCR 自动提炼完成后，工坊中的 MBTI 与依恋类型选择框显示为空；部分角色名称被写成“系统消息”。音色克隆按钮也因表单纵向布局落到音色下拉框下方。
- **根因**：模型输出的是“ESFJ (执政官) 或 ISFJ (守卫者)”等描述值，前端选择框仅接受精确枚举值；导入端没有过滤 OCR 的系统标签，且头部控件复用了纵向 `.p-form-group`。
- **处理动作**：前端在加载角色时将 MBTI/依恋类型归一化为枚举值并补齐16型 MBTI；导入端过滤系统/时间/AI 等通用标签并跳过用户侧消息；角色名称字段明确标注用途，音色下拉框和克隆按钮使用独立横向控件组；客户端个人中心移除运营后台入口，独立后台不受影响。
- **涉及文件**：`backend/persona_distiller.py`、`backend/app.py`、`frontend/src/components/PersonaWorkshopDialog.vue`、`frontend/src/assets/styles/persona.css`、`frontend/src/components/AccountDialog.vue`、`scripts/test_ex_skill_persona.py`。
- **验证方式**：项目虚拟环境运行 `scripts/test_ex_skill_persona.py` 通过，覆盖“系统消息”过滤与有效角色名选择；`frontend npm run build` 通过。

### ISSUE-54: 原生音色下拉框与头部动作组视觉不一致

- **问题现象**：浏览器原生音色下拉框展开后出现系统白底与蓝色高亮，和深色工坊不一致；保存、删除按钮高于“克隆新音色”按钮。
- **根因**：原生 `select/option` 的展开层由 Chrome 绘制，无法用页面 CSS 可靠统一主题；动作组随头部整体居中，而左侧音色控件包含标签行。
- **处理动作**：使用无依赖的项目内按钮菜单替代原生音色选择，保留 `listbox` 语义、点击外部关闭和 Escape 关闭；动作组改为底部对齐，和音色控件行一致。
- **涉及文件**：`frontend/src/components/PersonaWorkshopDialog.vue`、`frontend/src/assets/styles/persona.css`。
- **验证方式**：`frontend npm run build` 通过；浏览器实际检查菜单为深色、无系统蓝色高亮，Escape 仅关闭菜单而不关闭工坊。

### ISSUE-55: 截图导入消息固定显示 `【对方】` 且无左右头像

- **问题现象**：确认截图导入后，左侧消息正文都会被前端拼接 `【对方】`；这些消息又按 AI 消息渲染，既不具备导入身份信息，也没有可区分左右双方的头像。
- **根因**：`ChatView` 将非 user 的导入记录直接映射为 `ai` 并把 OCR 的 `speaker_label` 写进正文；`chat_import_batches` 和 `chat_messages` 没有头像/导入显示元数据字段。
- **处理动作**：新增迁移 `011_chat_import_display_meta.sql`，在导入批次保存左右头像对象键、在聊天消息保存导入显示元数据；OCR 审核页新增左侧对方/右侧我两个可选头像上传入口。新导入不再拼接标签，主聊天按导入元数据显示头像；历史读取时对私有头像链接重新签发，并兼容隐藏旧记录的 `【对方】` 前缀。
- **涉及文件**：`internal/auth/migrations/011_chat_import_display_meta.sql`、`backend/chat_import_store.py`、`backend/app.py`、`backend/app_data_store.py`、`frontend/src/types/index.ts`、`frontend/src/api/index.ts`、`frontend/src/components/ChatImportDialog.vue`、`frontend/src/views/ChatView.vue`、`frontend/src/assets/styles/chat.css`。
- **验证方式**：本地数据库迁移后回读 `chat_import_batches.left/right_avatar_object_key` 与 `chat_messages.import_meta` 三列存在；后端编译与前端生产构建通过；浏览器刷新旧导入历史，`【对方】` 前缀已消失。未上传用户头像作为测试数据。

### ISSUE-56: 单一聊天记录无法按人物分组与 OCR 导入无分流选择

- **问题现象**：所有消息固定写入同一个默认会话，不能像微信一样显示联系人头像、会话名称、最后一条消息并切换；OCR 导入也无法选择合并到当前聊天或另开聊天。
- **根因**：历史数据层虽然有 `chat_conversations`，却由唯一索引和 `_ensure_conversation` 强制限制为每用户一个活跃会话；客户端未读取会话列表，导入确认事件没有目标会话信息。
- **处理动作**：新增 `012_multi_conversations.sql` 移除单会话唯一索引并为会话增加头像键；后端增加会话列表、创建、指定会话历史/写入，仍按登录用户校验归属；聊天页面增加微信式会话列表和切换，`新对话` 改为创建空会话而非删除历史；OCR 审核页增加“继续当前会话 / 新建聊天”，新会话采用对方名称和头像。
- **涉及文件**：`internal/auth/migrations/012_multi_conversations.sql`、`backend/app_data_store.py`、`backend/app.py`、`frontend/src/types/index.ts`、`frontend/src/api/index.ts`、`frontend/src/components/ChatImportDialog.vue`、`frontend/src/views/ChatView.vue`、`frontend/src/assets/styles/chat.css`。
- **验证方式**：迁移后确认 `avatar_object_key` 列和多会话索引存在、旧唯一索引不存在；后端编译和前端构建通过；浏览器确认已有默认会话显示头像/名称/最后消息/时间。新建及 OCR 分流写入待用户实际触发后验收，未生成测试会话或导入数据。
- **同步补充**：用户消息首次落库和 AI 回复/中断回合落库后都会重新聚合会话列表；前端构建通过。真实发送后列表预览与时间的浏览器回归待用户实际消息触发。

### ISSUE-57: 旧会话列表头像缺失且列表宽度不可调整

- **问题现象**：现有默认会话的聊天页里已经有导入头像，但列表只能退回显示“微”字；列表固定宽度，无法按屏幕和内容调整。
- **根因**：旧会话创建于会话级头像字段之前，头像只存在于导入消息 `import_meta` 中；列表宽度是常量。
- **处理动作**：会话列表读取时，当会话级头像为空，动态使用最近一条左侧导入消息的头像；增加原生 Pointer Events 拖拽分隔条，限制宽度 156–360px，仅保留当前页面状态。
- **交互补充**：分隔条改为常驻细线和居中“⋮”把手，鼠标悬停时高亮，避免透明热区不可见。
- **位置修正**：拖拽把手从聊天列表右边界移动到光球区域与聊天列表之间；浏览器实测拖动后光球区域宽度变为470px。

### ISSUE-58: OCR 人设与声音表现割裂，缺少可控语速和声音情绪

- **问题现象**：OCR 只能提炼文字人格，用户无法查看或覆盖角色的朗读语速、声音情绪和输出清晰度；“调教语气”容易被误解为声音控制。
- **根因**：人格蒸馏输出未包含 TTS 表达建议；实时聊天、全屏语音和消息朗读把角色系统提示直接传给 TTS，没有独立、角色级声音表现数据。
- **官方依据**：百炼 Qwen-Audio-TTS 支持以 `instruction` 用自然语言控制语速、情绪与风格；实时音频协议支持 16/24/48k 采样率。文本 OCR 无法判断原始人声音质，只能推断建议。
- **处理动作**：OCR 人格输出新增 `voice_style`；工坊“说话风格”新增速度、声音情绪、24/48k 采样率和自定义描述。角色 Store 统一生成受限长度的 TTS instruction，聊天、全屏语音和历史朗读共用；流式服务按采样率计算 PCM 时长、额度与播放器/WAV 缓存。
- **涉及文件**：`backend/prompts/persona_analyzer.md`、`backend/prompt_compiler.py`、`backend/app.py`、`frontend/src/types/index.ts`、`frontend/src/stores/personaStore.ts`、`frontend/src/components/PersonaWorkshopDialog.vue`、`frontend/src/api/index.ts`、`frontend/src/lib/pcmStreamPlayer.ts`、`frontend/src/views/ChatView.vue`、`frontend/src/views/VoiceView.vue`、`scripts/test_ex_skill_persona.py`。
- **验证方式**：浏览器确认四项控件可见；专项人格编译测试、后端编译和前端生产构建通过。OCR 自动产出和真实百炼 TTS 声音效果待下一次用户实际触发验收，未消耗用户额度。

### ISSUE-59: 声音控件参数层级、覆盖优先级和缓存不一致

- **现象与根因**：Provider把instruction放到顶层而非input；语速仅为描述；非流式组合接口固定24k；有自定义描述时忽略下拉选择；缓存键没有真实TTS参数。
- **官方依据**：https://help.aliyun.com/zh/model-studio/cosyvoice-tts-http-api ，适用于当前Qwen-Audio-TTS HTTP/SSE接口。
- **修复**：四个入口贯通rate和sample_rate，修正input.instruction；三档速度映射0.85/1/1.15；选择项优先的合成描述；按设置快照建立版本2缓存键；采样率如实命名；校验非法参数并按慢速扩大额度预留。
- **验证**：Provider双路径请求体检查、四入口参数透传/非法输入/48k计量mock、7项前端音频测试和构建通过。真实HTTP24k/1倍速得到2.160秒WAV，SSE48k/0.85倍速得到2.541秒WAV。验证不包含OCR重新蒸馏和情绪听感保证。
- **涉及文件**：`backend/app_data_store.py`、`frontend/src/views/ChatView.vue`、`frontend/src/assets/styles/chat.css`。
- **验证方式**：浏览器刷新后列表已显示真实会话头像；实际拖拽分隔条后列表宽度由 218px 变为 296px；前端构建通过。

### ISSUE-60: 移动端首次进入语音页只显示微弱光晕

- **问题现象**：移动端切换到“语音”标签后，粒子光球不显示，只剩一层很淡的背景光晕。
- **根因**：移动端初始隐藏语音面板，Canvas 挂载时尺寸为 `0×0`，绘制函数因没有渲染上下文而退出；面板随后显示时又没有尺寸观察器重新测量并恢复动画。
- **处理动作**：共享光球渲染器使用浏览器原生 `ResizeObserver` 监听 Canvas 尺寸变化；隐藏面板变为可见后重新计算画布尺寸并恢复绘制循环，同时修正动画帧状态，避免已执行的帧 ID 阻止重启。
- **涉及文件**：`frontend/src/composables/useOrb.ts`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：移动端静态回归测试 6/6 与前端生产构建通过；Chrome iPhone 12 Pro（390×844）从“聊天”切到“语音”后粒子光球完整出现，控制台 0 条消息。

### ISSUE-61: Chrome 移动模拟器性能采集报错与 favicon 404

- **问题现象**：DevTools 控制台出现多条 `Cannot read properties of undefined (reading 'startTime')`，刷新后另有 `/favicon.ico` 404。
- **根因**：CDP 回读确认 `startTime` 异常来自名为 `DevTools Performance Metrics` 的隔离执行上下文，是 Chrome 152 DevTools 移动模拟性能采集脚本，并非页面主执行上下文；favicon 404 则是页面未显式声明已有应用图标。
- **处理动作**：无需修改或屏蔽业务异常；在页面头部复用 `public/weiguang-app-icon.png` 声明 favicon，消除真实资源 404。
- **涉及文件**：`frontend/index.html`。
- **验证方式**：前端生产构建通过；清空旧记录并强制刷新后，favicon 链接为 `http://localhost:5173/weiguang-app-icon.png`，CDP 连续监听页面主上下文及隔离上下文 3 秒，异常数为 0。

### ISSUE-62: OCR 导入的对方消息无法转换语音

- **问题现象**：普通 AI 回复有朗读按钮，但 OCR 导入的对方文本没有，无法使用当前克隆音色转换和保存语音。
- **根因**：消息模板的朗读按钮条件显式包含 `!msg.imported`，在进入已有的通用 TTS 流程前就排除了全部导入消息。
- **处理动作**：移除导入来源限制；所有 `who === 'ai'` 的对方文本均复用现有按需 TTS、额度、缓存、播放和保存流程，导入的用户侧消息仍不提供朗读。
- **涉及文件**：`frontend/src/views/ChatView.vue`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端回归测试 7/7、生产构建通过；Chrome 实际回读 21 条导入的对方消息均出现朗读按钮，6 条导入的用户消息均未出现。未主动调用 TTS，避免消耗用户语音额度。

### ISSUE-63: Pro 按次数计费缺少单次 LLM 成本硬上限

- **问题现象**：Pro 提供 3,000 次回复，但所有 Qwen3.5-Flash 调用均未传 `max_completion_tokens`，供应商默认允许最大输出；聊天历史也完整发送，套餐不存在确定的最坏 Token 成本。
- **根因**：额度层只控制调用次数，没有在共享 Provider 入口限制单次输出、系统提示、历史上下文及视觉附件，也未记录请求上限、裁剪量和 `finish_reason`。
- **处理动作**：共享 Provider 增加强制场景预算（聊天512、语音/纠偏1024、OCR4096、人设8192）；服务端限制2,000字符、200条消息、系统提示24KB、历史48KB、总文本96KB和最近视觉上下文；成本流水与管理端新增上限、P95、`length`比例、裁剪量及套餐平均单次成本。
- **涉及文件**：`backend/providers/qwen_llm.py`、`backend/providers/screenshot_extractor.py`、`backend/persona_distiller.py`、`backend/correction_handler.py`、`backend/app.py`、`backend/billing_store.py`、`frontend-admin/src/types/index.ts`、`frontend-admin/src/views/AdminCostsView.vue`、相关回归脚本。
- **验证方式**：Provider、额度端点、语音、人设、OCR及真实本地PostgreSQL原子回归通过，两套前端生产构建通过；浏览器直连接口验证2,001字符与5图均返回422，FastAPI健康。测试中一度出现补丁残留字符导致热重载语法错误，已由 `py_compile` 定位清除并确认服务恢复；未调用真实百炼生成。

### ISSUE-64: 免费体验周期由30天调整为7天

- **问题现象**：免费体验周期过长，且个人中心把同一个免费到期日同时显示成“额度重置日”和“访问续费至”，容易让用户误以为免费额度会续发。
- **处理动作**：服务端权威套餐周期改为7天；新增迁移同步缩短已有纯免费账号并调整列默认值；套餐页改为读取服务端周期，个人中心免费状态只显示“免费体验到期日”。Plus/Pro仍为30天。
- **涉及文件**：`backend/plans.py`、`internal/auth/migrations/019_free_trial_seven_days.sql`、`frontend/src/views/PricingView.vue`、`frontend/src/components/AccountDialog.vue`、相关方案与测试。
- **验证方式**：真实本地PostgreSQL原子回归、4项前端信任文案测试和生产构建通过；迁移已应用，浏览器账单回读免费周期7天，当前测试账号到期时间为2026-09-15。首次迁移因保留字别名失败并完整回滚，修正后成功；FastAPI已重新启动并恢复健康。

### ISSUE-65: 中文输入法按回车选词时误发送消息

- **问题现象**：在聊天输入框使用中文输入法输入拼音时，按 Enter 确认候选词会直接提交尚未完成的拼音字符。
- **根因**：输入框的 `keydown` 处理只判断 Enter/Shift，没有识别浏览器 IME 组合输入状态。
- **处理动作**：发送前忽略 `KeyboardEvent.isComposing`，并兼容输入法事件的 `keyCode === 229`；普通 Enter 发送和 Shift+Enter 换行保持不变。
- **涉及文件**：`frontend/src/views/ChatView.vue`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端交互回归 8/8 和生产构建通过；Chrome 实际派发事件验证组合态 Enter 的 `defaultPrevented=false`（交给输入法选词），普通 Enter 的 `defaultPrevented=true`（页面发送逻辑接管），测试未写入消息、未产生 AI 调用。

### ISSUE-66: 克隆声音与音色设置入口语义混淆

- **问题现象**：音色下拉框旁缺少设置入口；初次调整又误删了顶部“克隆声音”，并让设置图标进入了克隆界面。
- **处理动作**：恢复顶部“克隆声音”文字按钮；现有声音弹窗增加 `clone/settings` 两种入口模式，顶部进入上传克隆界面，下拉框右侧纯图标进入已有音色设置界面。设置界面选择音色后立即持久化，保留 `aria-label` 与悬停提示。
- **涉及文件**：`frontend/src/components/AppNav.vue`、`frontend/src/views/ChatView.vue`、`frontend/src/components/VoiceSettingsDialog.vue`、`frontend/src/stores/voiceConfig.ts`、`frontend/src/assets/styles/chat.css`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端回归 8/8 和生产构建通过；Chrome 双入口验收：顶部按钮显示“克隆声音”并包含上传表单，设置图标显示“音色设置”且不包含上传表单，顶部按钮保持可见。

### ISSUE-67: 音色设置缺少声音表现配置且聊天标题固定

- **问题现象**：设置图标只显示已创建音色，原有语速、情绪、拟声、采样率和声音维度配置不可见；OCR新建会话后顶部仍固定显示“微光”。
- **处理动作**：设置模式复用完整 `VoiceProfileForm` 并通过当前角色API保存；导航标题改为当前会话标题，OCR创建并激活新会话后自动更新。
- **涉及文件**：`frontend/src/components/VoiceSettingsDialog.vue`、`frontend/src/components/VoiceProfileForm.vue`、`frontend/src/components/AppNav.vue`、`frontend/src/views/ChatView.vue`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端回归9/9和生产构建通过；Chrome实测设置页显示8类主要配置及保存按钮且无上传表单，克隆页有上传表单且无声音配置；当前会话与顶部均显示“导入聊天”。开发中出现一次Vue props默认值警告，已改用Vue 3.5响应式解构默认值并确认构建无警告。

### ISSUE-68: 自适应语音忽略下拉框所选音色

- **问题现象**：用户选择“默认音色”或“我的音色”听感相同，Network中只看到相同 `conversation_id`，未看到有效音色差异。
- **根因**：`conversation_id`仅标识聊天；前端在 `adaptive_voice=true` 时省略 `voice` 查询参数，后端又用角色音色或系统默认覆盖传入音色；空值“默认音色”还会在非自适应入口回退到最近克隆音色。
- **处理动作**：自适应语音也显式传递所选 `voice`；后端采用“明确选择 > 角色绑定 > 系统默认”的优先级；前端以 `__default__` 明确表达系统默认，后端只对旧客户端未指定音色时保留历史回退；全屏语音同步使用相同规则。
- **涉及文件**：`frontend/src/api/index.ts`、`frontend/src/views/ChatView.vue`、`frontend/src/views/VoiceView.vue`、`backend/app.py`、`scripts/test_adaptive_speech.py`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：语音自适应Mock、额度端点、前端回归9/9、生产构建和FastAPI健康检查通过；真实本地账号解析确认克隆音色/模型匹配、默认音色为系统音色且二者不同；Chrome拦截fetch验证自适应请求分别携带所选voice和`__default__`，未调用百炼、未消耗语音额度。

### ISSUE-69: 克隆声音缺少高质量录音指导

- **问题现象**：上传区只展示格式、大小和最低时长，用户不知道怎样录制更容易获得接近原声的克隆效果。
- **处理动作**：在克隆声音上传区前增加官方建议说明：优先10–20秒、单人连续清晰说话、正常语速、安静环境，避免背景音乐、回声、杂音和其他人声。
- **涉及文件**：`frontend/src/components/VoiceSettingsDialog.vue`、`frontend/src/assets/styles/voice-api.css`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端回归9/9和生产构建通过；Chrome新标签页实测“克隆声音”弹窗包含录音指导、10–20秒建议以及避免背景音乐/其他人声说明。

### ISSUE-70: 音色无法重命名且OCR新会话缺少对方网名

- **问题现象**：已克隆音色只能沿用创建时名称；OCR新建会话固定回退为“导入聊天”，无法让会话列表和顶部显示真实网名。
- **处理动作**：新增用户归属校验的音色重命名接口，直接更新现有展示名称，不调用百炼；音色设置列表增加重命名编辑态。OCR选择新建聊天时新增必填“对方网名”，识别到有效昵称则预填，确认后作为现有会话 `title` 写入；列表和顶部继续共用该字段。
- **涉及文件**：`backend/voice_store.py`、`backend/app.py`、`frontend/src/api/index.ts`、`frontend/src/stores/voiceConfig.ts`、`frontend/src/components/VoiceSettingsDialog.vue`、`frontend/src/components/ChatImportDialog.vue`、`frontend/src/views/ChatView.vue`、相关样式与测试。
- **验证方式**：后端Mock覆盖成功改名、空名称422、跨用户404；前端回归10/10、生产构建、OpenAPI PATCH路由和Chrome重命名编辑态通过。未确认测试导入，避免制造测试会话。

### ISSUE-71: 对方网名误放到全局页面顶部

- **问题现象**：当前会话网名替换了页面顶部的“微光”品牌，而不是显示在右侧聊天对话框顶部中间。
- **根因**：会话标题错误绑定到全局 `AppNav`，右侧聊天区已有的一级标题仍被视觉隐藏。
- **处理动作**：全局导航恢复默认“微光”；右侧聊天主区域顶部显示当前会话 `title`，并保持桌面和移动聊天视图居中。
- **涉及文件**：`frontend/src/views/ChatView.vue`、`frontend/src/assets/styles/chat.css`、`frontend/tests/mobileA11y.test.mjs`。
- **验证方式**：前端回归10/10和生产构建通过；Chrome实测全局品牌为“微光”，右侧标题为“导入聊天”，标题与右侧聊天面板的水平中心点均为1132px，标题可见且位于聊天区顶部。
