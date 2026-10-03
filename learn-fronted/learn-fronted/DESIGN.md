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
    content: "1rem"
    section: "1.25rem"
components:
    button-primary:
        backgroundColor: "{colors.primary}"
        rounded: "{rounded.DEFAULT}"
    card:
        backgroundColor: "{colors.surface}"
        textColor: "{colors.ink}"
        rounded: "{rounded.md}"
    paper-card:
        backgroundColor: "{colors.paper}"
    helper-text:
        textColor: "{colors.muted}"
    evidence-stamp:
        textColor: "{colors.correction-red}"
    note:
        backgroundColor: "{colors.note-yellow}"
    status-success:
        textColor: "{colors.mastery-green}"
    divider:
        backgroundColor: "{colors.line}"
    focus-ring:
        backgroundColor: "{colors.focus}"
---

# AI 知识闯关 Design System

## Overview

一本会动的爆笑校园练习册：米色稿纸、黑色墨线、蓝色钢笔、老师红笔批改和黄色便签共同构成界面材料。目标用户是希望用一个问题或一段资料快速自测的中文用户。产品表达集中在等待和判题时刻，题干、选项、证据与隐私说明保持克制。

记忆点是“有依据才放行”红笔印章。禁止复制具体漫画人物、封面、字体标识或分镜；禁止通用 AI 渐变、玻璃拟态和赌场式奖励。

本文件是视觉决策来源，`styles/theme.css` 是唯一运行时 token 映射；页面和组件只使用语义 CSS 变量。

## Colors

纸张与表面形成低对比层级；墨色承担文字和硬边框。蓝色只用于主动作与当前进度，红色只用于错误和批改，绿色只用于成功与可信通过。黄色不能成为唯一状态信号。

## Typography

标题使用有手写节奏的中文字体栈，正文使用系统中文无衬线，证据和批注使用楷体栈。正文保持约 16px 与至少 1.55 行高；题干约 20px。长证据不斜体、不截断。

## Layout

手机单手操作优先，内容以 390×844 原型为基准自然滚动。主要动作位于内容末端并预留安全区；不使用会遮挡正文或焦点的固定按钮。

## Elevation & Depth

层级只使用纸张色阶、2px 墨线和 2–4px 硬偏移阴影。禁止柔和大阴影、背景模糊和玻璃拟态。

## Shapes

卡片统一约 14px 圆角，按钮约 12px；标签允许胶囊。红笔印章是唯一明显旋转的功能元素。

## Components

共享组件覆盖按钮、页头和证据卡。交互控件具备默认、按下、禁用和忙碌状态；H5 增强悬停与焦点。加载不伪造百分比，错误始终说明恢复动作。动效控制在 160–220ms，减弱动画时取消位移和循环。

## Do's and Don'ts

- 先展示证据、错因和下一步行动，再强调分数。
- 把漫画表达集中在关键反馈时刻。
- 不用装饰包围长题干或来源证据。
- 不根据一次结果宣称用户已经长期掌握知识。
