# RAG 企业级知识库问答系统

基于 **LangChain** 构建的企业级 RAG（检索增强生成）知识库问答系统，面向电商商品问答场景。用户通过浏览器操作，系统检索知识库内容并结合大语言模型生成回答，回答中附带知识库引用来源。

## 功能特性

- **知识库管理**（仅管理员）：文档上传、解析、分块、向量化入库、状态管理
- **RAG 问答**：检索知识库 + LLM 生成，展示引用片段、流式输出、多轮对话
- **多用户多会话**：独立会话、历史持久化，不同时间登录可找回对话
- **用户系统**：注册 / 登录 / 修改密码，角色权限（admin / user）
- **企业级优化**：问答结果缓存、接口限流、检索相关度过滤、上传文件校验、提示词注入加固

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python + FastAPI + LangChain |
| 大模型 | DeepSeek API（OpenAI 兼容接口） |
| Embedding | BGE（bge-m3，本地 sentence-transformers） |
| 向量库 | Chroma（本地持久化） |
| 关系库 | SQLite（SQLAlchemy，可平滑换 PostgreSQL） |
| 前端 | React 18 + Ant Design 5 + Vite |

## 目录结构

```
rag-qa-system/
├── backend/                 # 后端（FastAPI + LangChain）
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置（读取 .env）
│   │   ├── database.py      # SQLAlchemy 引擎
│   │   ├── models.py        # 数据模型
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── deps.py          # 认证 / 权限依赖
│   │   ├── core/            # security（密码哈希+JWT）/ limiter（限流）
│   │   ├── routers/         # auth / conversations / kb / chat
│   │   └── services/        # rag / llm / embedding / document_loader / cache
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # 前端（React + Ant Design）
│   └── src/pages/           # Login / Chat / KBManage
├── docs/产品文档.md
└── README.md
```

## 本地运行

### 0. 准备 DeepSeek API Key

1. 打开 [platform.deepseek.com](https://platform.deepseek.com)，注册并充值少量余额；
2. 在「API Keys」页面创建 Key，复制 `sk-...`。

### 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows 激活：
.venv\Scripts\activate
# （macOS / Linux：source .venv/bin/activate）

pip install -r requirements.txt
# 国内网络慢时改用清华镜像：
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制环境变量并填入你的 Key
cp .env.example .env
# 编辑 .env，把 DEEPSEEK_API_KEY 改成你的 Key

python run.py
# 后端运行在 http://127.0.0.1:8000
```

> 首次问答 / 上传文档时，会下载 BGE 向量模型（bge-m3，约 2GB），请耐心等待。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://127.0.0.1:5173
```

打开浏览器访问 <http://127.0.0.1:5173>。

## 企业级优化

- **结果缓存**：相同问题命中缓存后毫秒级返回。优先用 Redis（`REDIS_URL`），未启动 Redis 时自动降级为进程内存缓存。
- **接口限流**：全局 200 次/分、问答 10 次/分、登录注册 20 次/分（slowapi）。
- **检索相关度过滤**：按 L2 距离阈值（默认 0.75）过滤无关片段，降低答非所问。
- **上传校验 + 提示词注入加固**：校验文件真实格式防伪装扩展名；用户输入中的越权指令一律视为普通文本。

## 默认账号

| 角色 | 用户名 | 密码 | 权限 |
| --- | --- | --- | --- |
| 管理员 | admin | 123456 | 知识库管理 + 问答 |
| 普通用户 | 自行注册 | — | 仅问答 |

## 文档

完整产品与方案文档见 [docs/产品文档.md](docs/产品文档.md)。
