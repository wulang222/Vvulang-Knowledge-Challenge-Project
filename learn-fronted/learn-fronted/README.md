# AI 知识闯关小程序前端

第一版 MVP 前端，基于现有 HBuilderX Vue 3 工程开发。

## 本地运行

1. 在 HBuilderX 中打开本目录。
2. 复制 `.env.config` 为 `.env.local`，按需修改后端地址。
3. 运行到浏览器或微信开发者工具。

后端默认地址为 `http://127.0.0.1:8000`。发布到微信小程序前，需要将 API 部署为 HTTPS，并在微信公众平台配置 request 合法域名。

## 质量检查

```bash
npm install
npm run check
npm run test:coverage
```

`check` 会执行 TypeScript 类型检查与格式校验；覆盖率测试包含 API 契约、错误映射、本地草稿和答题状态测试。

## MVP 页面

- 学习资料与出题配置
- AI 生成等待与取消
- 逐题作答、解析和来源依据
- 闯关报告
- 错误恢复

设计基线见 `DESIGN.md`，跨页面交互契约见 `UX-CONTRACT.md`。
