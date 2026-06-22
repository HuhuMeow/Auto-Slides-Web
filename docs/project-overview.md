# 项目结构概览

本仓库只保留 Web 交付路径，源码按职责分层：

```text
backend/
├── main.py          FastAPI 入口与生产 SPA 托管
├── routers/         HTTP 接口
├── agents/          Planning、Verification、Repair、TEX、Speech、Editor Agent
├── services/        PDF 提取、图片处理、TEX workflow 与编译器
├── llm/             Provider 路由、共享客户端、参数和兼容层
├── prompts/         当前 Agent 使用的 Prompt
├── pipeline.py      异步作业编排
└── jobs.py          作业状态与 artifact 持久化
frontend/src/        React 页面、组件、状态与 API adapter
static/              后端提供的主题预览与公共图片
examples/            可上传的示例论文和项目幻灯片源码
scripts/             模型下载等维护命令
docs/                架构和使用说明
.runtime/            SQLite、上传、输出、模型与历史运行结果
```

前端只通过 `frontend/src/api/client.ts` 访问后端。后端以 SQLite 保存用户、作业、状态和 Agent edit，以文件保存 raw JSON、plan、verification、TEX、PDF 与 speech artifact。

`.runtime/` 默认不进入版本控制。可通过 `AUTOSLIDES_RUNTIME_DIR` 整体迁移，也可分别覆盖 `AUTOSLIDES_DATA_DIR` 和 `AUTOSLIDES_MARKER_MODEL_DIR`。

生产构建后，FastAPI 同时提供 `/api/*` 和 `frontend/dist/`。完整 Agent 数据流见 [agent-architecture.md](agent-architecture.md)。
