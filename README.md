# Synthetic User Lab

> 面向 Web 与 AI 产品的合成用户测试平台：用 LLM 驱动的 agent 扮演不同用户画像（persona），在真实可交互的测试站点上完成任务，自动观察、执行、验证并产出 UX 摩擦报告，支持同任务多 persona 对比。

## 简介

Synthetic User Lab 把"用户"抽象成可配置的 persona（技能 / 耐心 / 风险偏好三维度），用 LangGraph 编排一个会看页面、会操作浏览器、会判断进度的 agent 来模拟它跑完一条业务流，并在过程中沉淀步骤证据、关键截图与摩擦信号，最终输出一份可解释的 `keep / optimize / fix` 报告。

一次任务可以用多个 persona 批量执行，平台会聚合出跨 persona 对比报告，回答"哪类用户在哪一步会卡住"。
![alt text](assets/image-6.png)

### 核心特性

- **Persona 驱动执行**：persona 的 skill / patience / risk 三个维度作为行为约束注入决策 prompt，让不同角色产生差异化行为。
- **受控动作集合**：浏览器交互限定在 15 种受控动作内（navigate / click / fill / wait / press / scroll / upload / select / hover / check / uncheck / dblclick / drag / ask_for_help / abandon），不允许任意代码或脚本执行。
- **安全护栏**：动作执行前阻断高风险点击（支付/删除/发布等关键词）与敏感字段填写（密码/支付信息），护栏关键词库可在界面编辑，按 task 开关放行。
- **可读报告**：代码从步骤日志提取结构化事实 + 关键截图，模型只做语义补充；失败时仍能产出失败报告，可导出 Markdown。
- **多 persona 批量对比**：一次请求对同一 task 按多个 persona 发起 run，纯代码聚合出对比报告（成功率 / 结论分布 / 平均步数 / 摩擦信号数）。
- **基础 RAG 上下文**：决策与验证节点可接收录入的产品知识与失败案例检索上下文（关键词匹配，无外部向量依赖）。
- **开箱即用**：启动即自动 seed 3 个 persona + 3 个指向内置测试站点的 task；配好模型密钥后 `npm run dev` 即可跑通完整闭环。
- **系统级配置界面化**：模型预设与破坏性动作护栏关键词库均可在界面增删改，运行时按 persona 预设 > 默认预设 > `.env` 兜底解析模型。
- **三种持久化后端**：内存 / SQLite / PostgreSQL，按 `SYNTHETIC_USER_LAB_DATABASE_URL` 自动路由。

### 技术栈

| 层       | 技术                                                                                        |
| -------- | ------------------------------------------------------------------------------------------- |
| 后端     | Python 3.10+ · FastAPI · LangGraph · LangChain · Pydantic · Playwright                      |
| 模型路由 | OpenAI 兼容接口 / 阿里百炼 DashScope                                                        |
| 持久化   | InMemory / SQLite / PostgreSQL（psycopg 连接池 + JSONB）                                    |
| 前端     | React 19 · Vite 8 · TypeScript · Ant Design 6 · TanStack Query 5 · React Router 7 · i18next |
| 测试     | pytest · pytest-asyncio · FastAPI TestClient                                                |

---

## 快速开始

### 环境要求

- **uv**（Python 包管理器）
- **Python 3.10+**
- **Node.js 20+** 与 npm
- 一个可用的模型 API Key（OpenAI 兼容，或阿里百炼 DashScope）

### 安装

```bash
# 1. 复制环境变量模板，填入你自己的模型 API Key
cp .env.example .env

# 2. 安装根级一键启动工具
npm install

# 3. 安装后端依赖 + 浏览器驱动
uv sync --extra dev
uv run python -m playwright install

# 4. 安装前端依赖
cd frontend && npm install && cd ..
```

### 配置 `.env`

最少只需配置模型 Provider 与对应密钥：

```bash
MODEL_PROVIDER=openai            # 或 dashscope

# OpenAI 兼容（MODEL_PROVIDER=openai 时）
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL_NAME=gpt-4o
OPENAI_FAST_MODEL_NAME=gpt-4o-mini

# 阿里百炼（MODEL_PROVIDER=dashscope 时）
# DASHSCOPE_API_KEY=sk-your-key
# DASHSCOPE_MODEL_NAME=qwen-plus
# DASHSCOPE_FAST_MODEL_NAME=qwen-turbo
```

> **端口一致性提醒**：`SYNTHETIC_USER_LAB_BASE_URL` 的端口必须与后端监听端口（默认 8765）一致，否则内置测试站点 task 的 `start_url` 会指向错误端口，导致 Playwright 打不开页面。模板已默认对齐为 8765。

`SYNTHETIC_USER_LAB_DATABASE_URL` 控制持久化后端：

| 值                                    | 后端       | 说明                           |
| ------------------------------------- | ---------- | ------------------------------ |
| `:memory:`                            | InMemory   | 重启丢失，适合临时调试         |
| `data/synthetic_user_lab.db`（默认）  | SQLite     | 本地文件持久化                 |
| `postgresql://user:pass@host:5432/db` | PostgreSQL | 生产级，psycopg 连接池 + JSONB |

### 启动

```bash
npm run dev      # 一键同时启动后端(:8765) + 前端(:5173)，推荐
```

单独启动：

```bash
npm run dev:api  # 仅后端：uv run uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
npm run dev:web  # 仅前端：cd frontend && npm run dev
```

打开 `http://localhost:5173`。首次启动时会自动 seed 3 个 persona + 3 个 task，并在 `.env` 配置了有效 key 时 seed 一个默认模型预设。

---

## 使用流程

1. **配置 `.env` 模型参数** -> `npm run dev`
2. **Dashboard** 直接看到自动 seed 的可用 MVP persona / task
3. **Start Run** 选择一个 persona + 一个 task，发起 formal run
   - 选单个 persona 走单 run；选多个 persona 自动走 batch 并跳转对比报告
     ![alt text](assets/image-1.png)
4. **Run Detail** 实时轮询执行状态、步骤时间线与每步截图
   ![alt text](assets/image-2.png)
   ![alt text](assets/image-3.png)
5. **Report** 查看摘要 / 结论（keep·optimize·fix）/ 关键发现 / 摩擦信号 / 截图 / 建议
   ![alt text](assets/image-5.png)
6. **Compare** 多 persona 对比表与统计（成功率 / 结论分布 / 平均步数 / 摩擦信号数）

> 调试时可把 `SYNTHETIC_USER_LAB_HEADLESS=false` 看到真实浏览器窗口；也可在 Start Run 用 `max_steps_override` 临时覆盖本次 run 的步数上限（不回写 task 模板）。

---

## 内置测试站点 ShopLab

项目自带一个自托管的真实感电商测试站点（`backend/fixtures/test_site/`，通过 `/site` 挂载），包含 4 个页面构成完整多步业务流：

`index.html` 首页 -> `product.html` 商品详情 -> `checkout.html` 结算 -> `success.html` 成功

并故意埋入 4 个可控 UX 摩擦点，用于在多 persona 实验中制造可观察差异：

1. 商品页优惠券错误提示模糊
2. 结算页默认勾选"加急配送"隐藏额外运费
3. 结算页表单校验错误提示模糊
4. 结算页验证码提示埋在底部需滚动

MVP 样例的 3 个 task 全部指向该站点（浏览下单 / 优惠券 / 结算表单），并设置 `destructive_action_allowed=True` 以放行购买/支付/结算必经按钮。

---

## 系统配置

前端导航「系统配置」（`/system`）集中管理两类运行时配置：

- **模型预设**：多预设 CRUD + 设默认；每个 persona 可在表单中绑定特定预设；运行时按优先级 `persona 预设 > 默认预设 > .env` 解析，用于 decide / validate / wait agent 与报告分析。API Key 在列表中脱敏显示。
- **破坏性动作关键词库**：编辑 click / fill / navigate 的安全阻断关键词（正则模式），空库时回退默认词库。

---

## API 一览

所有接口前缀 `/api/v1`，根级健康检查 `GET /api/v1/health`。

| 方法    | 路径                                 | 说明                                                    |
| ------- | ------------------------------------ | ------------------------------------------------------- |
| CRUD    | `/personas/` `/tasks/` `/knowledge/` | 三类实体管理                                            |
| POST    | `/runs/start`                        | 单 persona 发起 formal run（支持 `max_steps_override`） |
| POST    | `/runs/batch`                        | 同 task 多 persona 批量发起，返回 `run_ids`             |
| POST    | `/runs/compare`                      | 跨 persona 对比报告聚合（纯代码，不调 LLM）             |
| GET     | `/runs`                              | 历史 run 列表                                           |
| GET     | `/runs/{id}`                         | run 状态                                                |
| GET     | `/runs/{id}/steps`                   | 步骤日志                                                |
| GET     | `/runs/{id}/report`                  | 结构化报告                                              |
| GET     | `/runs/{id}/report/markdown`         | Markdown 报告                                           |
| GET/PUT | `/settings/frontend`                 | 前端运行时设置（主题/语言/默认值）                      |
| CRUD    | `/system/model-presets`              | 模型预设（含 `/{id}/default` 切默认）                   |
| GET/PUT | `/system/guard-config`               | 护栏关键词库                                            |
| GET     | `/screenshots/{run_id}/{filename}`   | 截图文件（含路径遍历防护）                              |
| 静态    | `/site/`                             | ShopLab 测试站点                                        |

错误约定：实体不存在 `404`；报告未就绪 `409`；对比条件不满足 `404/409/400`；请求体校验失败 `422`。

---

## 测试与验收

```bash
# 后端全量测试
uv run pytest

# PostgreSQL store 测试（需先准备测试库）
SYNTHETIC_USER_LAB_POSTGRES_TEST_DSN='postgresql://<user>@localhost:5432/synthetic_user_lab_pg_test' \
  uv run pytest tests/test_postgres_run_store.py tests/test_postgres_entity_store.py -q

# 一键端到端验收（TestClient 驱动，不依赖 LLM/浏览器，可幂等复跑）
uv run python scripts/acceptance_check.py
uv run python scripts/acceptance_check.py --keep-reports

# PostgreSQL 模式验收
SYNTHETIC_USER_LAB_DATABASE_URL='postgresql://<user>@localhost:5432/synthetic_user_lab' \
  uv run python scripts/acceptance_check.py

# 幂等初始化 / 补 seed MVP 样例
uv run python scripts/seed_mvp_samples.py

# 前端
cd frontend && npx tsc --noEmit     # 类型检查
cd frontend && npm run lint         # oxlint
cd frontend && npm run build        # 构建，产物在 frontend/dist/
```
