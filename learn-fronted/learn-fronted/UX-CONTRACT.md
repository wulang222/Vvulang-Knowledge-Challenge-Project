# MVP UX Contract

## Product context

- 用户：输入问题、主题或任意长度文本并完成一次可信自测的中文学习者。
- 范围：输入配置、生成等待、逐题答题与证据、本次报告、必要错误恢复。
- 明确排除：登录、历史、关卡地图、动态补题、分享、排行榜和支付。
- 契约来源：`../../learn-backend/contracts/mvp-v1`、`../../docs/AI 知识闯关小程序方案设计文档.md`。
- 视觉来源：`../../ai-learning-miniapp-ui-prototype/DESIGN.md` 与核心流程/系统状态原型。

## Canonical UI Map

| Capability  | Canonical owner                                   | Source of truth | Allowed variants                  | Verification            |
| ----------- | ------------------------------------------------- | --------------- | --------------------------------- | ----------------------- |
| Button      | `components/AppButton.vue`                        | `DESIGN.md`     | primary, secondary, danger, ghost | busy/disabled/touch     |
| Header      | `components/AppHeader.vue`                        | `DESIGN.md`     | back, subtitle                    | safe area/back          |
| Evidence    | `components/SourceEvidence.vue`                   | API contract    | official, reference               | source mapping          |
| Form        | Uni-app native input components + page validation | this file       | textarea, radio-like buttons      | blank/focus/preserve    |
| Scrollbar   | `styles/theme.css` global H5 baseline             | `DESIGN.md`     | vertical                          | computed style          |
| Async state | `stores/quiz.ts`                                  | backend OpenAPI | generation, submission            | retry/abort/idempotency |

## Flow ledger

| Operation | Trigger          | Pending                    | Success    | Failure recovery     |
| --------- | ---------------- | -------------------------- | ---------- | -------------------- |
| 生成题目  | 生成有依据的题目 | 不确定等待，不伪造阶段完成 | 第一题     | 保留输入，重试或修改 |
| 确定答案  | 确定答案         | 本地立即锁定               | 解析与证据 | 不适用               |
| 提交闯关  | 查看本次报告     | 稳定忙碌按钮               | 报告页     | 保留全部作答并重试   |
| 会话过期  | 用原设置重新生成 | 新建临时会话               | 第一题     | 返回修改输入         |

## State and recovery

- 输入不设字符数限制；仅空白由前端阻止，安全和内容判断由后端负责。
- 草稿、配置和未提交作答在本地保留 24 小时；不保存 API Key 或完整抓取网页。
- 生成和提交为悲观操作，阻止重复点击；离页可中止当前请求。
- 422、超时、来源不足、断网和会话过期均保留可恢复数据及 `request_id`。
- 每题选择后才允许确定；确定后选项锁定并展示答案、解释和来源证据。

## Accessibility and responsive behavior

- 触控目标不小于 44px，状态不只依赖颜色，中文文本可换行。
- H5 提供可见焦点和全局可见滚动条；动效遵守 `prefers-reduced-motion`。
- 页面使用自定义导航栏并适配顶部/底部安全区。
- 页面标题由 `pages.json` 路由与可见 AppHeader 共同表达。
