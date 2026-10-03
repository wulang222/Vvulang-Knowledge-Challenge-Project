# AI 知识闯关 MVP v1 契约

> 状态：`已审核通过`
>
> 冻结日期：2026-10-03
>
> 审核通过日期：2026-10-03
>
> 契约版本：`1.0.0`

本目录是第一版匿名核心闭环的唯一开发契约。审核通过后，第二阶段后端 TDD 和后续前端开发都必须以这里的范围、接口和验收场景为准。

## 文件索引

1. [`SCOPE.md`](./SCOPE.md)：产品范围、页面边界、状态流转和关键约束。
2. [`openapi.yaml`](./openapi.yaml)：前后端共同使用的 HTTP API 契约。
3. [`ACCEPTANCE.md`](./ACCEPTANCE.md)：第二阶段开始前必须保留的验收场景。
4. [`redocly.yaml`](./redocly.yaml)：OpenAPI 机器校验规则；健康检查接口无需虚构无意义的 4xx 响应。

## 已冻结的优先级

发生冲突时，按以下顺序执行：

1. 用户在当前任务中的明确指令；
2. 本目录内经人工确认的 MVP v1 契约；
3. `AI 知识闯关小程序方案设计文档.md` V1.3；
4. `AI 知识闯关小程序需求文档.md`；
5. HTML 原型中的非 MVP 扩展展示。

因此，本版不采纳需求文档中与 V1.3 冲突的登录、历史记录、15 题、知识点确认、关卡地图和动态追题能力。

## 审核时只需确认 5 件事

- [ ] 页面仅包含输入配置、生成等待、逐题答题/依据、本次报告与必要异常状态。
- [ ] 用户输入没有产品级字符数上限；空白、敏感信息和滥用由后端判断。
- [ ] 题量仅为 5/10，难度仅为基础/进阶，题型仅为单选/判断。
- [ ] 没有用户原文时检索官方资料；有原文时优先使用原文，官方补充单独标注。
- [ ] 每道题都有可定位证据，分数与统计由程序计算，不由模型决定。

## 变更规则

契约已经冻结为 `1.0.0`。任何改变接口字段、错误码、页面范围或验收条件的修改，都必须先更新本目录并记录版本，不在实现代码中暗改。

## 已核验的官方实现依据

- [Uni-app Vue 3 + Pinia](https://uniapp.dcloud.net.cn/tutorial/vue3-pinia.html)
- [Uni-app TypeScript](https://uniapp.dcloud.net.cn/tutorial/typescript-subject.html)
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI 测试依赖替换](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [阿里云百炼联网搜索](https://help.aliyun.com/zh/model-studio/web-search/)
