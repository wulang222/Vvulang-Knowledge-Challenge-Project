# AI 知识闯关小程序 UI 原型

本目录集中保存本次 UI 原型任务的全部交付文件。原始需求与方案文档仍保留在项目 `docs/` 目录，不在此处重复或移动。

## 查看顺序

1. `prototypes/01-core-learning-flow.html` — 核心学习与闯关流程
2. `prototypes/02-study-review-center.html` — 学习、错题与复盘中心
3. `prototypes/03-sharing-creator.html` — 分享、挑战与创作者流程
4. `prototypes/04-system-states.html` — 加载、空白、异常与恢复状态

每个 HTML 文件在桌面端采用一行三列布局，在窄屏下自动切换为单列。

## 配套文件

- `DESIGN.md` — 视觉方向、色彩、排版与组件规范
- `UX-CONTRACT.md` — 跨页面交互与状态约定
- `premium-ui.json` — UI 审计配置
- `premium-audit.json` — 最近一次 UI 审计结果
- `.htmlvalidate.json` — HTML 校验配置
- `references/style-concept-board.png` — 前期风格概念板
- `prototypes/assets/` — 四套 HTML 共用的 CSS 与 JavaScript

## 本地预览

在项目根目录运行：

```bash
python3 -m http.server 4173
```

然后打开：

`http://127.0.0.1:4173/ai-learning-miniapp-ui-prototype/prototypes/01-core-learning-flow.html`
