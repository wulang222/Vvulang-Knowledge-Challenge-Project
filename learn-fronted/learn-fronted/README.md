# AI 知识闯关小程序前端

第一版 MVP 前端，基于现有 HBuilderX Vue 3 工程开发。

## 本地运行

1. 在 HBuilderX 中打开本目录。
2. 复制 `.env.example` 为 `.env.local`，按需修改后端地址。
3. 在 HBuilderX 中选择“运行 → 运行到小程序模拟器 → 微信开发者工具”。

## 微信开发者工具

本目录是 uni-app 源码，源码中不会直接存在 `app.json`。开发模式的原生微信小程序代码由 HBuilderX 生成到：

```text
unpackage/dist/dev/mp-weixin
```

完成一次微信编译后，必须把上面的编译产物目录导入微信开发者工具，不能导入当前 uni-app 源码目录，否则开发者工具会提示找不到 `app.json`。

如果清理过 `unpackage`，需要先在 HBuilderX 重新运行到微信开发者工具。正式发行产物位于 `unpackage/dist/build/mp-weixin`，应直接导入该发行目录。

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
