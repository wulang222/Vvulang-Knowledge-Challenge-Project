# AI 知识闯关后端

第一版后端采用 FastAPI、Pydantic v2 和进程内临时会话。接口契约见 [`contracts/mvp-v1`](./contracts/mvp-v1/README.md)。

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

`/ready` 只检查必要配置是否存在，不调用模型或产生费用。
