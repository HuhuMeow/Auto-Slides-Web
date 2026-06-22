# Backend 部署与架构说明

Backend 是一个 FastAPI 应用：接收论文 PDF，创建异步任务，依次调用提取、规划、TEX 生成、校验、修复和演讲稿 Agent，并将产物及结构化进度事件提供给前端。

## 部署

### 环境要求

- Python 3.11+；Node.js 20+（构建前端时使用）。
- TeX Live，至少包含 `pdflatex`；中文演示文稿需要 `xelatex`。
- DeepSeek 或 OpenRouter 等 OpenAI 兼容服务的 API Key。
- Marker/Surya 模型是可选项；未安装时使用 PyMuPDF 降级提取。

在仓库根目录执行：

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，至少设置一个 API Key，并修改默认账号密码
cd frontend && npm ci && npm run build && cd ..
python -m backend --host 0.0.0.0 --port 8000
```

构建完成后，FastAPI 会同时提供 `/api/*` 和 `frontend/dist/`，访问 `http://localhost:8000` 即可。开发时可分别运行 `uvicorn backend.main:app --reload` 与 `cd frontend && npm run dev`。

### 单机免登录模式

在仓库根目录启动：

```bash
python -m backend --nologin
```

先复制本地配置，再启动服务：

```bash
cp backend/settings.example.toml backend/settings.toml
```

访问 `http://127.0.0.1:8000` 时，前端会通过后端自动取得该单机账户的 Session Token 并直接进入主页。账户和密码只保存在已被 Git 忽略的 `backend/settings.toml`：

```toml
[single_user]
username = "localuser"
password = "localpass"
```

可以直接修改此文件，或用 `python -m backend --nologin --settings /path/to/settings.toml` 指定其他配置。后端不会把密码发送给前端，也不会填充登录表单。该账户使用固定 ID 并保存在 SQLite 中；以后不带 `--nologin` 启动多人模式时，仍可使用配置过的用户名和密码登录。

配置文件以明文保存密码，应限制为当前系统用户可读，例如执行 `chmod 600 backend/settings.toml`，并避免将生产密码提交到公开仓库。

`--nologin` 默认只监听 `127.0.0.1`。它会让所有能访问服务的人共享该账户，因此不要在不可信网络上使用 `--host 0.0.0.0`。

### 重置数据库

先停止正在运行的后端，然后在仓库根目录执行：

```bash
python -m backend --initdb
```

`--init-db` 是等价写法。该命令会永久删除所有用户、登录 Session、任务、Agent 事件、上传论文和生成结果，重新创建 SQLite 表与初始管理员/用户，然后立即退出。它不会删除 `.runtime/models/` 中已下载的 Marker/Surya 模型。

如果重置后希望同时创建 `settings.toml` 中的单机账户，执行：

```bash
python -m backend --initdb --nologin
```

这是不可撤销操作；需要保留数据时应先备份 `.runtime/data/`。

生产环境建议由 systemd/supervisor 管理上述 Uvicorn 命令，并在前面配置 Nginx/Caddy TLS 反向代理。当前任务队列基于进程内 `ThreadPoolExecutor`，因此应使用**单个 Uvicorn worker**；需要多实例部署时，应先将任务队列迁移到 Celery/RQ 等外部系统。持久化挂载 `.runtime/data/`，模型较大时也挂载 `.runtime/models/`。可通过 `AUTOSLIDES_DATA_DIR`、`AUTOSLIDES_MARKER_MODEL_DIR` 和 `AUTOSLIDES_MAX_WORKERS` 调整路径与并发数。

## 面向对象的运行模型

可以把一次转换理解为多个协作对象处理同一个 `Job`：

1. Router 是 Controller，负责鉴权、校验请求并调用应用服务。
2. `pipeline.py` 是 Orchestrator，控制 Agent 顺序、取消检查、状态和产物落库。
3. `PlanningAgent`、`TexGenerationAgent`、`VerificationAgent`、`RepairAgent`、`SpeechAgent` 各自封装一种职责；Editor Agent 采用函数式入口，但承担相同的领域角色。
4. `TexWorkflow`、`TexValidator`、`LightweightExtractor` 是可复用 Service，对 Agent 隐藏编译、PDF 解析等基础设施细节。
5. `LLMInterface` 是模型适配器；`llm_provider_context` 为一次任务注入 provider/model 配置。
6. `progress.py` 类似轻量 Event Bus。各对象发出用户可读事件，事件写入 `job_events`；`GET /api/jobs/{id}` 返回最近事件，前端轮询后显示在进度条下。

## 文件职责

### 应用核心

| 文件 | 职责 |
| --- | --- |
| `__main__.py` | 解析 `--nologin`、监听地址和配置文件等启动参数。 |
| `main.py` | 应用装配入口；初始化数据库、注册路由、CORS 和前端静态资源。 |
| `config.py` | 环境变量、运行目录、默认账号与并发配置。 |
| `settings.example.toml` | 单机账户配置模板；实际凭据写入被 Git 忽略的 `settings.toml`。 |
| `pipeline.py` | 完整转换流程与保存、编译、修复用例。 |
| `jobs.py` | Job 的创建、查询、排队、状态更新和 Artifact 关联。 |
| `database.py` | SQLite 连接、建表、迁移、数据重置、种子用户与统计数据。 |
| `progress.py` | 绑定当前 Job，持久化 Agent 事件并同步进度。 |
| `schemas.py` | Pydantic 请求/响应 DTO，包括 `JobEvent`。 |
| `artifacts.py` | Artifact 建模、公开 URL 和安全路径解析。 |
| `downloads.py` | 收集 TEX、图片等文件并生成下载压缩包。 |
| `mappers.py` | 将 Agent 原始字典规范化为稳定 API 模型。 |
| `security.py` | 密码哈希、Token Session、鉴权依赖。 |
| `themes.py` | 可用 Beamer 主题列表。 |
| `__init__.py` | 标记 `backend` Python 包。 |

### Agent、服务与模型层

| 目录/文件 | 职责 |
| --- | --- |
| `agents/planning.py` | 分析论文并生成逐页演示计划。 |
| `agents/tex_generation.py` | 将计划与论文内容转成完整 Beamer TEX。 |
| `agents/verification.py` | 比较论文、计划和 TEX，报告遗漏与风险。 |
| `agents/repair.py` | 按验证报告修复内容覆盖问题。 |
| `agents/speech.py` | 为每页幻灯片生成讲稿和时间估算。 |
| `agents/editor.py` | 根据自然语言生成可审阅 TEX diff，并在确认后应用。 |
| `services/layout_extractor.py` | 提取 PDF 文本、图片和版面信息。 |
| `services/paper_extractor.py` | 用 LLM 增强表格、公式、摘要等结构化内容。 |
| `services/presentation.py` | Planning Agent 的稳定服务入口。 |
| `services/tex_workflow.py` | 串联 TEX 生成、图片准备、编译和自动纠错。 |
| `services/tex_compiler.py` | 隔离目录内运行 LaTeX、解析错误并重试。 |
| `services/latex.py` | Unicode/LaTeX 转义、包注入与特殊字符检查。 |
| `llm/client.py` | 统一 LLM 调用、JSON 解析与重试。 |
| `llm/router.py` | Provider 环境配置、模型列表和任务级上下文。 |
| `llm/settings.py` | 不同任务类型的温度、Token 等参数。 |
| `llm/compat.py` | 第三方 OpenAI/LangChain 客户端兼容补丁。 |
| 各子目录 `__init__.py` | 标记 Python 包，不包含业务逻辑。 |

提示词文件按任务一一对应：`extract_tables_and_equations.py` 提取表格与公式，`summarize_text_for_presentation.py` 生成面向演示的摘要，`key_content_extraction.py` 提取核心论点，`slides_planning.py` 规划页面，`tex_generation.py` 生成 Beamer，`tex_error_fix.py` 修复编译错误；`prompts/__init__.py` 统一导出这些模板。

### HTTP 路由

`routers/auth.py` 管理登录、注册和登出；`jobs.py` 管理任务、TEX、编译、修复、Editor Agent 及报告；`sessions.py` 安全读取产物；`models.py` 返回可选模型；`themes.py` 返回主题。新增接口应保持 Router 只处理 HTTP 语义，将业务规则放入 Agent、Service 或应用核心。

## 运行数据与日志约定

SQLite、上传文件和生成结果默认位于 `.runtime/data/`，模型位于 `.runtime/models/`，均不应提交。Agent 日志必须通过 `emit_progress(agent, message, stage=..., progress=...)` 发送用户可理解的阶段信息；不要把 Prompt、API Key、完整论文内容或内部堆栈写入事件。服务端诊断细节仍使用 Python `logging`。每个任务最多保留最近 200 条事件，API 默认返回最近 40 条。
