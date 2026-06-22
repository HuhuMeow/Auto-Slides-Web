# Docker 部署 / Docker Deployment

## 中文

Docker 镜像包含 React 前端、FastAPI 后端、Python 依赖、Poppler 和中英文 LaTeX 环境。API Key、数据库、上传文件、生成结果和可选 Marker/Surya 模型不会写入镜像：密钥来自 `.env`，运行数据与模型分别保存在 Docker named volume 中。

### 前置条件

- Docker Engine 或 Docker Desktop
- Docker Compose plugin（使用 `docker compose` 命令）
- 推荐 x86_64 Linux 主机、至少 16 GB 内存和充足磁盘空间

### 标准网络流程

```bash
cp .env.example .env
# 编辑 .env，填写 API Key 并修改默认账户密码

./scripts/docker-deploy.sh
```

需要完整的版面、OCR、表格和图片提取能力时：

```bash
./scripts/docker-deploy.sh --with-models
```

### 中国大陆镜像流程

```bash
cp .env.example .env
# 编辑 .env，填写 API Key 并修改默认账户密码

./scripts/docker-deploy-cn.sh
```

下载模型并启动：

```bash
./scripts/docker-deploy-cn.sh --with-models
```

大陆流程默认使用：

- DaoCloud 公共容器镜像代理：Node/Python 基础镜像
- 清华 TUNA：Debian 软件包
- 阿里云：PyPI 软件包
- npmmirror：npm 软件包
- ModelScope：Marker/Surya 模型

公共镜像可能限流或临时不可用。可以通过 `CN_NODE_IMAGE`、`CN_PYTHON_IMAGE`、`CN_DEBIAN_MIRROR`、`CN_DEBIAN_SECURITY_MIRROR`、`CN_PIP_INDEX_URL` 和 `CN_NPM_REGISTRY` 覆盖默认值。相关说明见 [DaoCloud 镜像代理](https://github.com/DaoCloud/public-image-mirror)、[清华 Debian 镜像](https://mirrors.tuna.tsinghua.edu.cn/help/debian/) 和 [阿里云 PyPI 镜像](https://developer.aliyun.com/mirror/pypi/)。

### 脚本选项

```text
--with-models  下载约数 GB 的可选版面模型并持久化
--nologin      使用 backend/settings.toml 中的账户自动登录
--skip-build   复用本地 autoslides-web:local 镜像
--china        让标准脚本使用大陆镜像配置
```

单机模式示例：

```bash
./scripts/docker-deploy.sh --nologin --with-models
```

脚本会在缺失时复制 `backend/settings.example.toml`。使用 `--nologin` 前应修改生成的 `backend/settings.toml`。

### 运维命令

```bash
# 查看状态和日志
docker compose ps
docker compose logs -f app

# 重启或停止
docker compose restart app
docker compose down

# 更新代码后重建
./scripts/docker-deploy.sh
```

数据库使用 `autoslides-data` volume，模型使用 `autoslides-models` volume。`docker compose down` 不会删除它们；`docker compose down -v` 会永久删除任务数据和已下载模型。

重置应用数据但保留模型：

```bash
docker compose stop app
docker compose run --rm app python -m backend --initdb
docker compose up -d
```

默认访问 `http://localhost:8000`。可以在 `.env` 中设置 `AUTOSLIDES_PORT=8080` 修改宿主机端口。

## English

The Docker image bundles the React frontend, FastAPI backend, Python dependencies, Poppler, and the English/Chinese LaTeX toolchain. Secrets and mutable data stay outside the image: `.env` supplies API credentials, while Docker named volumes store application data and optional Marker/Surya weights.

### Standard network

```bash
cp .env.example .env
# Edit .env and configure an API key and safe default passwords.

./scripts/docker-deploy.sh
```

Enable layout-aware extraction, OCR, tables, and figures:

```bash
./scripts/docker-deploy.sh --with-models
```

### China mainland mirrors

```bash
cp .env.example .env
# Edit .env first.

./scripts/docker-deploy-cn.sh --with-models
```

This flow uses the DaoCloud container proxy, TUNA Debian mirrors, Aliyun PyPI, and npmmirror. Mirror endpoints can be overridden with the `CN_*` environment variables listed above.

Use `--nologin` for the configured local account and `--skip-build` to reuse the current image. Open `http://localhost:8000` after startup. `docker compose down` preserves named volumes; `docker compose down -v` permanently removes both application data and downloaded models.
