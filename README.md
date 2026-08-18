# AI 个人智能知识库助手 (AI-Powered Personal Knowledge Base)

端到端 AI 全栈应用：上传 **PDF / 图片 / 音频 / 文本**，后台自动解析并向量化，
基于 **RAG（检索增强生成）** 实现跨文档智能问答（带流式输出）与内容摘要。

> 依据《项目开发文档：AI智能知识库助手》实现。

## 功能特性

- 📄 多格式上传：PDF、图片、音频、文本，单文件最大 100MB，支持拖拽多选
- ⚙️ 异步处理：Celery + Redis 后台解析、切片、向量化（文件状态实时可查）
- 🧠 多模态统一检索：图片 → 多模态 LLM 描述，音频 → Whisper 转文字，统一进入向量库
- 💬 智能问答：SSE 流式输出 + 引用来源标注 + 跨文档检索
- 📝 跨文档摘要生成
- 🔐 JWT 用户认证，文件按用户隔离
- 🐳 Docker Compose 一键启动

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Next.js 14 (App Router) · Tailwind CSS · shadcn/ui 风格组件 · Zustand · Axios |
| 后端 | FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| 数据库 | PostgreSQL (元数据) · ChromaDB (向量) |
| AI/ML | LangChain (切片) · OpenAI SDK / 智谱 SDK (双供应商) · Whisper · pdfplumber / PyPDF2 |
| 异步 | Celery + Redis |
| 部署 | Docker Compose |

## 快速开始 (Docker)

前置条件：Docker + Docker Compose（Windows 请安装 **Docker Desktop**）。

```bash
# 1. 准备环境变量（填入你的 LLM API Key）
cp .env.example .env

# 2. 一键启动全部服务（首次构建需几分钟）
docker compose up -d --build

# 3. 访问
#    前端界面:  http://localhost:3000
#    API 文档:  http://localhost:8000/docs
#    健康检查:  http://localhost:8000/health
```

首次启动会自动完成：PostgreSQL 建表、服务健康检查、前后端启动。

**使用流程**：注册账号 → 登录 → 上传文档 → 等待状态变为「已就绪」→ 提问 / 一键摘要。
左侧点击文档可**限定本次问答范围**，不选则跨全部文档检索。

## LLM 供应商切换

编辑根目录 `.env`：

```bash
# OpenAI（默认）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# 或 智谱 GLM（国内网络）
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=xxxx
```

- 两种供应商共用同一套抽象接口，切换后**需重建后端容器**：`docker compose up -d --build backend celery_worker`
- 不同供应商的 embedding 维度不同，向量库按供应商隔离（collection 自动加后缀）
- **音频转写**统一走 OpenAI Whisper API（智谱无等价服务），即使供应商选 zhipu，只要配置 `OPENAI_API_KEY` 即可转写音频

## 本地开发（不使用 Docker）

需要本机 Python 3.11+ 与 Node 18+。

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # 填好 API Key，默认 SQLite，无需 Postgres

# 本地调试模式: USE_CELERY=false，上传后由 BackgroundTasks 内联处理
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

### 数据库迁移 (可选)

应用启动时自动 `create_all` 建表；需要正式迁移时：

```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 注册 `{username, email, password}` |
| POST | `/api/auth/login` | 登录 → 返回 JWT |
| GET | `/api/users/me` | 当前用户信息 |
| POST | `/api/files/upload` | 上传文件 (multipart)，202 返回，后台异步处理 |
| GET | `/api/files` | 文件列表 |
| GET | `/api/files/{id}/status` | 处理状态 |
| DELETE | `/api/files/{id}` | 删除文件（同时删除向量） |
| POST | `/api/chat/query` | 非流式问答 |
| GET | `/api/chat/stream?question=..&file_ids=..` | **SSE 流式问答** |
| POST | `/api/summarize` | 生成摘要（支持多文件） |

流式事件格式：

```
data: {"type":"start","chunk":""}
data: {"type":"content","chunk":"这"}
data: {"type":"content","chunk":"份"}
data: {"type":"end","sources":["a.pdf"]}
data: [DONE]
```

## 项目结构

```
├── docker-compose.yml         # 一键编排 (Postgres/Redis/后端/Celery/前端)
├── .env.example               # 根环境变量 (LLM 密钥等)
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口 (CORS + 路由注册)
│   │   ├── config.py          # 配置管理 (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy 引擎/会话
│   │   ├── models/            # users / files / conversations
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── api/               # auth / users / files / chat / summarize
│   │   ├── services/          # auth / file / rag / embedding / chunking
│   │   ├── parsers/           # pdf / image / audio 解析器
│   │   ├── llm/               # 供应商抽象 (OpenAI / 智谱)
│   │   ├── tasks/             # Celery 文件处理任务
│   │   └── utils/             # JWT / 文件工具
│   ├── celery_worker.py       # Celery 启动模块
│   ├── alembic/               # 数据库迁移框架
│   └── Dockerfile
└── frontend/                  # Next.js 14 应用
    ├── app/                   # 页面 (仪表盘/登录/注册)
    ├── components/            # 上传/文件列表/聊天窗口/UI 组件
    ├── store/                 # Zustand (auth/file/chat)
    ├── lib/                   # axios 客户端 / SSE 解析
    └── Dockerfile
```

## 文件处理流程（异步）

```
上传 → files 表插入 (pending)
    → Celery: process_file
        ① 解析: PDF→pdfplumber | 图片→多模态描述 | 音频→Whisper | 文本→原文
        ② 切片: RecursiveCharacterTextSplitter (chunk=500, overlap=50)
        ③ 向量化: OpenAI text-embedding-3-small / 智谱 embedding-2
        ④ 写入 ChromaDB (file_chunks_{provider})
    → 状态更新 completed/failed，自动重试 2 次
```

## RAG 问答流程

```
问题 → 向量化 → ChromaDB 检索 top_k=5 (按 user 隔离 + 可选 file_ids 过滤)
    → 组装 Prompt (系统提示禁止幻觉 + 文档片段上下文)
    → LLM 流式生成 → SSE 推送 → 返回引用来源
```

## 常见问题

- **上传后一直「处理中」**：查看 celery 容器日志 `docker compose logs -f celery_worker`；
  确认 `.env` 中 LLM API Key 有效。
- **问答报「未找到 API Key」**：确认 `.env` 配置的供应商与 `LLM_PROVIDER` 一致，并重建后端。
- **音频上传失败**：需要配置 `OPENAI_API_KEY`（Whisper API）。
- **端口占用**：修改 `docker-compose.yml` 中 5432 / 6379 / 8000 / 3000 的映射端口。
- **向量库目录权限**：Windows 上 Docker 挂载 `backend/chroma_db` 偶发文件锁问题，
  可删除该目录后重启：`docker compose restart backend celery_worker`。

## 验收对照（文档 §11）

- [x] 注册/登录并获取 JWT
- [x] 上传 PDF 异步解析并向量化（含状态轮询）
- [x] 针对文档提问，回答附引用来源
- [x] SSE 流式逐字输出
- [x] 音频转文字并支持问答
- [x] Docker Compose 一键启动全部服务
