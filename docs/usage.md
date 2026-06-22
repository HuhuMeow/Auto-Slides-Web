# Auto-Slides Web 使用说明

## 开发模式

后端在项目根目录启动：

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

前端在另一个终端启动：

```bash
cd frontend
npm ci
npm run dev
```

浏览器访问 `http://localhost:5173`。`frontend/src/api/client.ts` 默认选择真实 HTTP API；仅在 `frontend/.env` 中设置 `VITE_USE_MOCK_API=true` 时使用 mock 数据。

## 单进程部署

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

后端检测到 `frontend/dist/` 后，会同时托管 SPA 与 `/api/*` 接口。浏览器访问 `http://localhost:8000`。

## LLM 配置

密钥只写在根目录 `.env`：

```env
LLM_DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
DEEPSEEK_MODELS=deepseek-chat,deepseek-reasoner

OPENROUTER_API_KEY=your-key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=openai/gpt-4o
OPENROUTER_MODELS=openai/gpt-4o,openai/gpt-4.1
```

`frontend/.env` 只配置 `VITE_API_BASE_URL` 和 `VITE_USE_MOCK_API`，不得存放服务端密钥。同源部署时让 `VITE_API_BASE_URL` 为空；只有前后端跨域部署时才填写完整后端地址。

## 网页操作流程

1. 登录或注册用户。
2. 新建任务并上传 PDF。
3. 选择语言、模型、主题及可选 Agent。
4. 启动任务并查看阶段进度。
5. 在工作区检查 plan、验证报告、TEX、PDF 和讲稿。
6. 修改 TEX 后保存并重新编译。
7. 向 Editor Agent 提交自然语言要求；检查 Current/Proposed diff 后再接受。
8. 验证未通过时可执行 One-click repair；后端会真实修复 plan、重新验证并重新生成幻灯片。

## 数据目录

`.runtime/` 集中保存 SQLite、上传、作业产物、模型和历史运行数据。可用 `AUTOSLIDES_RUNTIME_DIR` 整体改变位置，也可分别设置 `AUTOSLIDES_DATA_DIR` 与 `AUTOSLIDES_MARKER_MODEL_DIR`。`AUTOSLIDES_MAX_WORKERS` 控制并发作业数。生产环境必须覆盖默认账号密码，并定期清理过期上传与输出。
