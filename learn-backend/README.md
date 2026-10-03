# AI 知识闯关后端

第一版后端采用 FastAPI、Pydantic v2、阿里云百炼 OpenAI 兼容接口和进程内临时会话。接口契约见 [`contracts/mvp-v1`](./contracts/mvp-v1/README.md)。

## 本地开发

要求 Python 3.12–3.14。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src tests
.venv/bin/uvicorn ai_quiz.app:app --reload
```

默认地址：`http://127.0.0.1:8000`。

- 健康检查：`GET /api/v1/health`
- 就绪检查：`GET /api/v1/ready`
- 创建闯关：`POST /api/v1/quiz-runs`
- 获取闯关：`GET /api/v1/quiz-runs/{run_id}`
- 提交作答：`POST /api/v1/quiz-runs/{run_id}/submit`

`/ready` 只检查必要配置是否存在，不调用模型或产生费用。

## 百炼配置

复制 `.env.example` 后填写服务端环境变量：

```dotenv
DASHSCOPE_API_KEY=your-server-only-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_GENERATION_MODEL=your-responses-capable-model
DASHSCOPE_SEARCH_MODEL=
```

`DASHSCOPE_SEARCH_MODEL` 为空时复用生成模型。所选模型必须支持 Responses API 和联网搜索工具。API Key 只保存在后端，不能写入 Uni-app 代码或提交到仓库。

## MVP 行为

- 输入不设置产品级字数上下限；后端仅拒绝空白、敏感信息、注入和明显滥用。
- 问题输入必须找到可靠网页来源；用户原文优先作为证据，官方网页可独立补充。
- 每题必须通过结构化字段、答案唯一性、重复题和证据引用门禁，失败最多修复两次。
- 分数和知识点统计由程序确定性计算；报告模型失败时返回不改变客观数据的基础报告。

默认测试使用可替换假模型和假搜索，不产生模型费用。真实联网调用应在人工配置有效百炼凭证后单独冒烟验证。
