# RAG 企业级知识库问答系统 —— 项目上下文

## 项目概述

基于 **LangChain** 的 RAG（检索增强生成）知识库问答系统，用户毕设，面向电商商品问答。Web 应用，浏览器访问，回答附带知识库引用片段。支持多用户多会话、知识库管理、权限控制。

## 已确认技术决策（勿擅自变更）

- **框架**：LangChain（硬性要求）+ Python/FastAPI 后端 + React 18 / Ant Design 5 / Vite 前端
- **大模型**：DeepSeek API（`deepseek-chat`，OpenAI 兼容接口，经 `langchain_openai.ChatOpenAI` 接入）
- **Embedding**：BGE（`bge-m3`，本地 sentence-transformers）
- **向量库**：Chroma（本地持久化）
- **关系库**：SQLite（SQLAlchemy，可平滑换 PostgreSQL）
- **交付**：GitHub 公开仓库 `https://github.com/dachenx/project1` + 本机运行

## 关键账号

- 管理员：`admin` / `123456`（首次启动自动 seed，仅管理员可进知识库管理）
- 普通用户：自行注册，仅问答

## 项目结构

```
backend/    # FastAPI + LangChain（app/routers、app/services、app/core、app/models）
frontend/   # React + Ant Design（src/pages：Login/Chat/KBManage）
docs/产品文档.md
README.md
```

## 环境注意（国内，重要）

- **pip** 用清华镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
- **HuggingFace 模型下载**：已配 `HF_ENDPOINT=https://hf-mirror.com` 镜像，且 **必须禁用 Xet**（`HF_HUB_DISABLE_XET=1`，已在 config.py 写死）——否则会绕过镜像直连 AWS CDN 导致超时
- **模型缓存目录**：`D:\develop\huggingface`（HF_HOME，已用 setx 设全局 + config.py 兜底）
- **Python 3.14**：torch 2.13 已装好，无兼容问题

## 运行方式

```bash
# 后端（先复制 backend/.env.example 为 .env 并填入 DEEPSEEK_API_KEY）
cd backend
.venv\Scripts\activate          # Windows 激活虚拟环境
python run.py                   # 或 uvicorn app.main:app --port 8000

# 前端（另开终端）
cd frontend
npm run dev                     # http://127.0.0.1:5173
```

首次上传文档/问答会下载 BGE 模型（约 2GB）到 D 盘，走镜像。

## 当前进度

**已完成**：后端全部接口（认证/会话/知识库/RAG 流式问答）、前端全部页面、已 git 提交并推送到 GitHub、后端接口已实测通过（auth / 会话 / kb / 权限 / 中文 UTF-8）、**RAG 端到端实测通过**（上传文档 → BGE 向量化入库 → 检索 → DeepSeek 流式回答 → 引用 [1]，Xet 禁用后模型经镜像正常下载约 4.3GB 缓存到 D 盘）、**浏览器端到端联调通过**（走 Vite 代理完整流程，示例知识库补全为 12 个商品）、**企业级优化（轻量版）**：问答结果缓存（Redis 优先、连不上自动降级内存，命中后毫秒级返回）、接口限流（slowapi：全局 200/分、问答 10/分、登录注册 20/分）、检索/生成耗时日志、上传文件内容校验（防伪装扩展名）、提示词注入加固。

**待完成**：
1. 混合检索（BM25 + 向量，RRF 融合）——暂缓，当前语义检索已够用。
2. 重排序 Rerank——需另下载 rerank 模型，暂缓。
3. 本机安装 Redis 以启用 Redis 缓存（当前未装，自动降级为内存缓存）。

## 临时文件 / 演示资产

- `backend/_e2e_test.py`：E2E 测试脚本（测完可删）
- `backend/_sample_products.txt`：示例商品文档，已补全为 **12 个热门商品**（手机/平板/笔记本），入库后 6 个分块，作为演示数据
- `实习经历.txt`：将本项目整理成的实习经历描述（简历用）

## 协作约定

用户无法提供具体技术层面要求，重要技术决策需先列方案征询用户；命名、目录、代码风格等细枝末节按业界最佳实践处理。
