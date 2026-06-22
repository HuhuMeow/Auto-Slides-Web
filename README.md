# Auto-Slides Web

[中文](#中文说明) · [English](#english)

## 中文说明

### 项目简介

本项目基于 [Westlake-AGI-Lab/Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) 进行二次开发，将原有流程整理为可部署的 Web 应用。原项目论文可在 [examples/autoslides.pdf](examples/autoslides.pdf) 查看。

系统接收学术论文 PDF，通过多个 Agent 完成内容提取、演示规划、覆盖度验证、自动修复、LaTeX Beamer 生成、PDF 编译和可选讲稿生成。浏览器端支持任务进度、计划与验证报告查看、TEX 编辑、PDF 预览，以及可审阅的自然语言修改。

### 用户：部署与使用

#### 推荐：Docker 一键部署

安装 [Docker Engine/Desktop 与 Compose plugin](https://docs.docker.com/compose/install/)，然后在仓库根目录配置 API：

```bash
cp .env.example .env
# 编辑 .env，填写 API Key 并修改默认账户密码
```

标准网络环境：

```bash
./scripts/docker-deploy.sh
```

中国大陆镜像流程：

```bash
./scripts/docker-deploy-cn.sh
```

需要完整的版面分析、OCR、表格和图片提取能力时，增加 `--with-models`：

```bash
./scripts/docker-deploy-cn.sh --with-models
```

脚本会构建前后端、安装 TeX 环境、启动服务并持久化数据库和模型。启动后访问 `http://localhost:8000`。更多选项、数据卷与更新方法见 [Docker 部署说明](docs/docker-deployment.md)。如果不使用 Docker，也可以按下面的本地流程部署。

#### 1. 环境要求

- Python 3.11+
- Node.js 20+
- TeX Live：英文至少需要 `pdflatex`，中文还需要 `xelatex` 和中文字体包
- DeepSeek 或 OpenRouter API Key
- 建议预留足够磁盘空间；完整 Marker/Surya 模型约占数 GB

#### 2. 安装依赖

在仓库根目录执行：

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

cd frontend
npm ci
cd ..
```

没有 `uv` 时，也可以使用标准 `venv` 和 `pip`：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. 配置 API 与账户

复制环境变量模板：

```bash
cp .env.example .env
```

编辑根目录 `.env`，至少配置一个模型服务：

```env
LLM_DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

也可以配置 `OPENROUTER_API_KEY` 及对应模型。API Key 只能放在后端 `.env`，不要写入 `frontend/.env`。

多人模式的初始账户在 `.env` 中配置：

```env
AUTOSLIDES_ADMIN_USERNAME=admin
AUTOSLIDES_ADMIN_PASSWORD=change-me
AUTOSLIDES_USER_USERNAME=user1
AUTOSLIDES_USER_PASSWORD=change-me
```

请在第一次启动前修改默认密码。数据库已经创建后，如需按新配置重新创建初始账户，可执行下文的数据库重置命令。

单机免登录账户使用独立配置：

```bash
cp backend/settings.example.toml backend/settings.toml
```

然后编辑 `backend/settings.toml`：

```toml
[single_user]
username = "localuser"
password = "replace-with-a-strong-password"
```

该文件已被 Git 忽略。账户密码不会发送到浏览器，也不会自动填入登录表单。

#### 4. 下载可选版面模型

```bash
python scripts/download_models.py
```

脚本会从 ModelScope 下载 `Lixiang/marker-pdf` 到 `.runtime/models/`。下载后可以获得更完整的版面感知 Markdown、OCR、表格识别和论文图片提取效果。

不下载模型也可以运行。Marker 初始化失败时，系统会自动回退到 PyMuPDF 纯文本提取；基础生成流程仍可使用，但复杂版面、表格和图片信息会减少。

#### 5. 构建并启动网页服务

```bash
cd frontend
npm run build
cd ..

python -m backend --host 0.0.0.0 --port 8000
```

浏览器访问 `http://localhost:8000`。FastAPI 会同时提供网页和 `/api/*` 接口。

生产环境应由 Nginx/Caddy 提供 HTTPS 反向代理，并持久化 `.runtime/data/`。当前任务队列位于后端进程内，因此只运行一个 Uvicorn 进程；任务并发由 `AUTOSLIDES_MAX_WORKERS` 控制，不要使用多个 Uvicorn worker。

单机免登录模式：

```bash
python -m backend --nologin
```

默认只监听 `127.0.0.1:8000`，浏览器会使用配置的单机账户自动建立真实 Session。不要在不可信网络上以 `--nologin --host 0.0.0.0` 运行。

#### 6. 使用流程

1. 登录或使用单机模式进入主页。
2. 上传论文 PDF，选择语言、模型、Beamer 主题和可选 Agent。
3. 启动任务，在进度条下查看当前 Agent 的实时操作。
4. 查看演示计划、验证报告、TEX、PDF 和可选讲稿。
5. 直接编辑 TEX，或让 Editor Agent 生成修改建议并在确认 diff 后应用。

#### 7. 重置为初始状态

先停止后端，再执行：

```bash
python -m backend --initdb
```

该命令会永久删除所有用户、任务、Session、上传文件和生成结果，然后重建初始数据库；不会删除 `.runtime/models/`。若要同时重建单机账户，使用 `python -m backend --initdb --nologin`。

### 开发者：本地开发

后端开发服务器：

```bash
source .venv/bin/activate
python -m backend --reload --host 127.0.0.1 --port 8000
```

另一个终端启动前端：

```bash
cd frontend
npm run dev
```

访问 `http://localhost:5173`。Vite 会将 `/api` 和 `/static` 代理到后端。仅做独立 UI 开发时，可以在 `frontend/.env` 设置 `VITE_USE_MOCK_API=true`。

主要目录：

```text
backend/           FastAPI、任务编排和持久化
  agents/          Planning、Verification、Repair、TEX、Speech、Editor Agent
  services/        PDF 提取、LaTeX 处理与编译
  llm/             Provider 路由、模型客户端和参数
  prompts/         Agent 提示词
frontend/          React、TypeScript、Vite 前端
scripts/           模型下载等维护脚本
docs/              使用与架构文档
examples/          原项目论文
.runtime/          本地数据库、任务产物和模型，不进入 Git
Dockerfile         前后端与 TeX/ML 运行环境镜像
docker-compose*.yml 标准及中国大陆镜像部署配置
```

提交前运行：

```bash
python -m compileall -q backend scripts
cd frontend
npm run lint
npm run build
```

修改 API 时，请同步更新 `backend/schemas.py` 与 `frontend/src/api/types.ts`。完整说明见 [Backend 文档](backend/README.md) 和 [Agent 架构](docs/agent-architecture.md)。

### 许可证与商业使用

**本项目使用的不是标准 MIT 许可证。未经许可，禁止将本项目用于任何商业目的。** 商业使用包括但不限于：将本项目或其修改版本集成到收费产品或服务、用于商业部署、提供付费托管服务，或者以其他方式直接或间接获取商业利益。

如需商业使用，必须事先同时获得以下双方的明确书面许可：

1. 原项目 [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) 的原作者或相关权利人；
2. 本二次开发项目的作者或维护者。

仅获得其中一方许可并不足以获得本项目的商业使用授权。其他许可条款请参阅 [LICENSE](LICENSE)。

---

## English

### Overview

This project is developed from [Westlake-AGI-Lab/Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) and reorganizes the original workflow as a deployable Web application. The original project paper is available at [examples/autoslides.pdf](examples/autoslides.pdf).

The application accepts an academic PDF and coordinates multiple agents for content extraction, presentation planning, coverage verification, automatic repair, LaTeX Beamer generation, PDF compilation, and optional speech generation. The browser provides task progress, plan and verification views, TEX editing, PDF preview, and reviewable natural-language edits.

### Users: Deployment and Usage

#### Recommended: one-command Docker deployment

Install [Docker Engine/Desktop and the Compose plugin](https://docs.docker.com/compose/install/), then configure the API from the repository root:

```bash
cp .env.example .env
# Edit .env and add an API key and safe default passwords.
```

Standard network:

```bash
./scripts/docker-deploy.sh
```

China mainland mirror flow:

```bash
./scripts/docker-deploy-cn.sh
```

Add `--with-models` for layout-aware extraction, OCR, tables, and figures:

```bash
./scripts/docker-deploy-cn.sh --with-models
```

The scripts build both application layers, install the TeX toolchain, start the service, and persist application data and models. Open `http://localhost:8000`. See [Docker deployment](docs/docker-deployment.md) for options, volumes, and upgrades. The manual non-Docker workflow remains available below.

#### 1. Requirements

- Python 3.11+
- Node.js 20+
- TeX Live with `pdflatex`; Chinese output also requires `xelatex` and CJK fonts
- A DeepSeek or OpenRouter API key
- Several GB of free disk space if the full Marker/Surya models are installed

#### 2. Install dependencies

Run from the repository root:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

cd frontend
npm ci
cd ..
```

Without `uv`, use the standard environment tooling:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure the API and accounts

```bash
cp .env.example .env
```

Configure at least one provider in the root `.env`:

```env
LLM_DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

OpenRouter is supported through the corresponding `OPENROUTER_*` variables. Keep API keys in the backend `.env`; never place them in `frontend/.env`.

Initial multi-user credentials are configured in `.env`:

```env
AUTOSLIDES_ADMIN_USERNAME=admin
AUTOSLIDES_ADMIN_PASSWORD=change-me
AUTOSLIDES_USER_USERNAME=user1
AUTOSLIDES_USER_PASSWORD=change-me
```

Change these values before the first launch. If the database already exists, use the reset command below to recreate the initial accounts from the updated configuration.

For local no-login mode, create a private settings file:

```bash
cp backend/settings.example.toml backend/settings.toml
```

Edit `backend/settings.toml`:

```toml
[single_user]
username = "localuser"
password = "replace-with-a-strong-password"
```

This file is ignored by Git. Its password stays on the backend and is never sent to or prefilled in the browser login form.

#### 4. Download the optional layout models

```bash
python scripts/download_models.py
```

The script downloads `Lixiang/marker-pdf` from ModelScope into `.runtime/models/`. These weights enable layout-aware Markdown, OCR, table recognition, and figure extraction.

The application also works without the download. If Marker cannot initialize, extraction falls back to text-only PyMuPDF. Core slide generation remains available, but complex layouts, tables, and figures are captured less accurately.

#### 5. Build and run the Web service

```bash
cd frontend
npm run build
cd ..

python -m backend --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. FastAPI serves both the built frontend and `/api/*`.

For production, place Nginx or Caddy in front of the service for HTTPS and persist `.runtime/data/`. The job queue lives inside the backend process, so run one Uvicorn process and control task concurrency with `AUTOSLIDES_MAX_WORKERS`; do not start multiple Uvicorn workers.

For local no-login mode:

```bash
python -m backend --nologin
```

It listens on `127.0.0.1:8000` by default and establishes a real session for the configured local account. Do not expose `--nologin --host 0.0.0.0` to an untrusted network.

#### 6. Workflow

1. Sign in, or enter through local no-login mode.
2. Upload a PDF and select the language, model, Beamer theme, and optional agents.
3. Start the job and follow the current Agent action below the progress bar.
4. Review the plan, verification report, TEX, PDF, and optional speech script.
5. Edit TEX directly or review and apply a diff proposed by the Editor Agent.

#### 7. Reset to a clean installation

Stop the backend, then run:

```bash
python -m backend --initdb
```

This permanently removes all users, jobs, sessions, uploads, and generated outputs, then rebuilds the initial database. It preserves `.runtime/models/`. Add `--nologin` to recreate the configured local account as well.

### Developers: Local Development

Run the backend development server:

```bash
source .venv/bin/activate
python -m backend --reload --host 127.0.0.1 --port 8000
```

Run the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/static` to the backend. Set `VITE_USE_MOCK_API=true` in `frontend/.env` only for isolated UI development.

Repository layout:

```text
backend/           FastAPI, job orchestration, and persistence
  agents/          Planning, Verification, Repair, TEX, Speech, and Editor agents
  services/        PDF extraction, LaTeX processing, and compilation
  llm/             Provider routing, model clients, and parameters
  prompts/         Agent prompts
frontend/          React, TypeScript, and Vite client
scripts/           Model download and maintenance utilities
docs/              Usage and architecture documentation
examples/          Original project paper
.runtime/          Local database, job artifacts, and models; ignored by Git
Dockerfile         Frontend, backend, TeX, and ML runtime image
docker-compose*.yml Standard and China-mainland deployment configuration
```

Validate changes before committing:

```bash
python -m compileall -q backend scripts
cd frontend
npm run lint
npm run build
```

When changing the API, keep `backend/schemas.py` and `frontend/src/api/types.ts` synchronized. See the [Backend guide](backend/README.md) and [Agent architecture](docs/agent-architecture.md) for details.

### License and Commercial Use

**This project is not distributed under the standard MIT License. Commercial use is prohibited unless separately authorized.** Commercial use includes, without limitation, integration into a paid product or service, commercial deployment, paid hosting, or any other direct or indirect commercial exploitation of this project or its derivatives.

Any commercial use requires prior, explicit, written permission from both:

1. the original authors or relevant rightsholders of [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides); and
2. the author or maintainer of this derivative project.

Permission from only one party is insufficient to authorize commercial use of this project. See [LICENSE](LICENSE) for the remaining terms.
