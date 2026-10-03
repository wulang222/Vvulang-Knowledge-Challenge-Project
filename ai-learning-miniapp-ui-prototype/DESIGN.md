---
version: alpha
name: "AI 知识闯关"
description: "把问题、主题或用户资料变成有来源可信闯关练习的原创校园漫画式学习产品。"
colors:
  primary: "#4D78B8"
  paper: "#FFF8E7"
  surface: "#FFFDF5"
  ink: "#24201B"
  muted: "#756E63"
  pencil-blue: "#4D78B8"
  correction-red: "#E4493F"
  note-yellow: "#FFD85A"
  mastery-green: "#58A66A"
  line: "#D9CEB6"
  focus: "#1D5FD1"
typography:
  display:
    fontFamily: "Smiley Sans, LXGW WenKai, Noto Sans SC, sans-serif"
  body:
    fontFamily: "Noto Sans SC, PingFang SC, Microsoft YaHei, sans-serif"
  note:
    fontFamily: "LXGW WenKai, KaiTi, STKaiti, serif"
rounded:
  DEFAULT: "0.875rem"
  sm: "0.5rem"
  md: "0.875rem"
  lg: "1.25rem"
  pill: "999px"
spacing:
  unit: "0.25rem"
  phone-gap: "1.5rem"
  board-max: "76rem"
components:
  button: {}
  card: {}
  phone-artboard: {}
  evidence-stamp: {}
  dialog: {}
  toast: {}
---

# AI 知识闯关 Design System

## Overview

### Creative North Star

一本会动的爆笑校园练习册：米色稿纸、黑色墨线、蓝色钢笔、老师红笔批改和黄色便签共同构成界面材料。幽默来自原创学生角色的反应和简短批注，不来自牺牲信息清晰度。

### Product context and register

- **Audience and primary job:** 有一个问题想快速弄懂，或有资料想自测的中文用户；在 10 分钟内建立概念并检查是否真正掌握。
- **Target market and evidence:** 中国大陆微信小程序用户，依据项目需求文档的微信生态、中文学习和分享场景。
- **Locale and language policy:** 首版 `zh-CN`，产品文案使用简短、直接、可行动的中文。
- **Usage scene:** 手机单手操作，碎片化但需要专注；原型评审在桌面端以三列手机画板展示。
- **Register:** 产品界面为主，品牌表达集中在欢迎页、等待页和结果反馈。
- **Memorable signature:** “有依据才放行”红笔印章；答案解析必须能展开用户原文或官方来源证据。
- **Restraint:** 题干、选项、证据和隐私说明保持安静、规则和高可读性。
- **Anti-references:** 不使用通用紫蓝 AI 渐变、玻璃拟态、赌场式奖励、现有漫画角色或竞品视觉复刻。
- **Token ownership/runtime mapping:** 本文件是视觉决策来源；`prototypes/assets/prototype.css` 是原型运行时映射。

## Colors

纸张与表面形成低对比层级；墨线黑承担文字和硬边框。铅笔蓝只用于主动作与当前进度，批改红只用于错误、重点和批注，掌握绿只用于成功与可信通过。黄色是表达性色，不承担唯一语义。焦点环使用独立深蓝，保证键盘可见性。

## Typography

展示标题使用有手写节奏的中文字体栈，正文使用系统中文无衬线，资料摘录与老师批注使用楷体栈。正文基线 15–16px、行高不低于 1.55；题干 19–22px。长证据文本不斜体、不全大写、不截断关键内容；官方来源标题、发布方和链接使用清晰的资料卡层级。

## Layout

桌面原型板最大宽度 76rem，每行三列；中宽两列，手机宽单列。手机画板以 390×844 为设计基准，内容区遵循顶部状态栏和底部安全区。核心操作固定在视觉末端，不遮挡焦点和正文。

## Elevation & Depth

层级通过纸张色阶、2px 墨线和 3–4px 硬偏移阴影表达。禁止柔和大面积阴影、背景模糊和玻璃拟态。弹窗遮罩使用半透明墨色，弹窗本体仍保持纸张材质。

## Shapes

卡片使用轻微不规则感但保持 14px 统一圆角；按钮为 12–14px 圆角，不默认使用胶囊形。知识点标签、状态标签和短筛选项允许胶囊。红笔印章是唯一明显旋转的组件。

## Components

### Foundational visual states

所有可交互元素提供默认、悬停、键盘焦点、按下、禁用和忙碌状态。错误同时使用图标、标题和修正动作；成功同时使用勾选图标与文本。加载保留最终内容高度，长任务使用真实阶段，不伪造精确百分比。

### Buttons and actions

主按钮为蓝底白字和硬阴影；次按钮为纸色墨线；危险动作为红色描边，和安全主操作分开。忙碌时按钮宽度不变。图标按钮必须有 `aria-label`。

### Navigation and data display

跨原型文件使用顶部导航。小程序内部以底部导航和页面返回为主。关卡地图表达真实知识点顺序；报告优先使用列表和进度条，不用难以解释的雷达图。

### Forms and overlays

输入控件有真实标签、帮助文本和行内错误。文本域禁止手动缩放并提供足够高度。隐私、删除和公开范围使用应用自有对话框；严重操作默认聚焦取消。

### Iconography

使用简洁线性符号和文字标签。图标采用 2px 墨线，装饰性涂鸦不能代替功能图标。

### Motion

反馈动效 160–220ms，使用轻微压下、红笔勾画和印章落下。`prefers-reduced-motion` 下全部取消位移和循环动画。

### Content and data visualization

文案像一位直率但不羞辱人的同桌：说明发生了什么、为什么、下一步怎么做。报告只描述“本次表现”，不因一次正确宣称长期掌握。

## Do's and Don'ts

- **Do:** 把证据、错因和下一步行动放在分数之前。
- **Do:** 让漫画表达集中在关键反馈时刻。
- **Don't:** 用夸张装饰包围长题干或来源证据。
- **Don't:** 复制《阿衰》角色、封面、字体标识或具体漫画分镜。
