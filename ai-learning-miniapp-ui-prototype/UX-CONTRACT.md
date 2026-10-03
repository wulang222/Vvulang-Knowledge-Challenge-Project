# UX Contract

## Product context

- Audience: 有一个问题/主题想快速弄懂，或有资料希望短时自测的中文学习者，以及创建学习包的老师/培训者。
- Primary jobs: 问题/主题/资料转题、可信作答、来源复核、错题再练、分享经授权的结果。
- Target market: 中国大陆微信小程序用户。
- Active locales: `zh-CN`。
- Language/content register: 简短、直接、鼓励但不夸大掌握。
- Timezone/calendar policy: 客户端展示本地时间；复习日程使用公历自然日。
- Accessibility target: WCAG 2.2 AA。

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| 产品范围与学习规则 | `../docs/AI 知识闯关小程序需求文档.md` | PRD | 2026-10-02 |
| MVP 状态与失败协议 | `../docs/AI 知识闯关小程序方案设计文档.md` | Technical design / ADR | 2026-10-02 |
| 隐私与资料处理 | 上述两份文档的隐私、安全章节 | Product requirement | 2026-10-02 |
| 视觉方向 | 当前任务确认 `A + 1` | Explicit task decision | 2026-10-02 |

## Visual contract

- Project `DESIGN.md`: `DESIGN.md`
- Token ownership model: `DESIGN.md` 决策，CSS 变量映射。
- Runtime token source: `prototypes/assets/prototype.css`
- Supported themes: 米色纸张亮色主题；系统高对比模式保持可操作。

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | 原生 `<select>` | `UX-CONTRACT.md` | native | 键盘与窄屏 |
| Form | 原生 HTML 控件 + `.field/.choice` | `prototype.css` | 文本、单选、开关 | 键盘与窄屏 |
| Scrollbar | 全局 `prototype.css` | `DESIGN.md` | 稳定 gutter | computed style |
| Toast | `.toast` + `prototype.js` | `UX-CONTRACT.md` | success/info/error | live region |
| Dialog | 原生 `<dialog>` + `prototype.js` | `UX-CONTRACT.md` | 隐私、删除、发布 | Escape、焦点恢复 |
| Loading/progress | `.stage-list/.loader` | `prototype.css` | 生成、上传 | 阶段真实性 |
| Lists | `.list-stack/.history-card` | `prototype.css` | 历史、错题、资料 | 空/加载/错误 |

## Component behavior

| Component | Default | Hover | Focus | Active | Disabled | Busy | Error |
|---|---|---|---|---|---|---|---|
| Button | 明确层级 | 上移 1px | 3px 焦点环 | 硬阴影归零 | 降低对比 | 尺寸不变 | 行内说明 |
| Input | 2px 墨线 | 蓝色边线 | 3px 焦点环 | n/a | 灰底 | 保留高度 | 红线+文本 |
| Choice | 白纸卡片 | 蓝色边线 | 3px 焦点环 | 压下 | 灰底 | n/a | 红线+图标 |
| List | 完整摘要 | 轻微上移 | 卡片焦点 | 压下 | n/a | 固定占位 | 原位恢复动作 |

## Flow ledger

| Operation | Trigger | Pending | Success destination | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|---|
| 生成题目 | “先看看会考什么” | 输入分类、安全检查、来源整理/检索、规划、生成、质检 | 关卡地图/第一题 | 已通过质量检查 | 重试、修改输入或指定来源 | 第一题标题 | 技术方案 §5、§8 |
| 提交答案 | “确定答案” | 按钮锁定 | 本题解析 | 对错+原因+证据 | 保留选择后重试 | 解析标题 | 需求 §6.3 |
| 生成报告 | 完成末题 | 分析阶段 | 通关报告 | 分数与行动计划 | 返回确定性基础报告 | 报告标题 | 技术方案 §6.9 |
| 删除资料 | 资料详情删除 | 对话框确认 | 学习中心 | 已进入删除流程 | 保留资料并说明 | 原触发按钮 | 需求 §9 |
| 发布学习包 | 发布按钮 | 发布确认 | 分享详情 | 已发布 | 保留草稿 | 页面标题 | 需求 §6.2 |

## Navigation and responsive behavior

- 每个 HTML 原型板提供跨文件导航，当前文件标记 `aria-current="page"`。
- 手机画板内部使用返回按钮或底部导航；固定操作不遮挡内容。
- 桌面三列、中屏两列、窄屏单列；顺序保持业务流程顺序。
- 页面标题包含当前原型分组名称。

## Overlays and feedback

- 对话框使用原生 `<dialog>`，Escape 关闭并恢复触发按钮焦点。
- 危险删除展示对象与后果，取消按钮排在危险动作之前。
- Toast 位于画板底部，3 秒消失，使用 `aria-live="polite"`。
- 关键错误始终保留行内文本，Toast 不承载唯一信息。

## Async and resilience

- 生成和发布均采用悲观提交；按钮忙碌时阻止重复点击。
- 生成任务展示真实阶段与已经完成的步骤；联网检索不伪造精确百分比。
- 超时、断网、敏感信息、来源不可用均保留用户输入和配置。
- 匿名草稿保存在本地 24 小时；恢复前显示保存时间和继续/清除动作。

## Validation

- 原型使用 HTML 约束和应用自有行内错误，不调用浏览器验证气泡。
- 输入框不设置最少或最多字数门槛；只有空输入在前端阻止提交。一句话问题可以进入后端判断。
- 后端负责识别问题/原文/混合输入、敏感信息与来源策略；错误保留输入并聚焦可修正位置。
- 无用户原文时自动检索官方来源；有原文时优先使用原文，官方补充必须单独标记。
- 未选择答案时“确定答案”禁用；提交后选项锁定。
- 分享前默认隐藏文件名、原文和未授权成绩。

## Verification

- Static: HTML 解析、CSS/JS 语法、反模式搜索、DESIGN.md lint。
- Browser: Chromium 桌面、窄屏、键盘、减弱动画、成功与错误状态。
- Accessibility: 语义控件、可见焦点、非颜色单一反馈、44px 触控目标。
