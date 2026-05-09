# run1最小闭环

## Commit

run1最小闭环

## 变更目标

建立 Synthetic User Lab 的最小 Demo Run 闭环，让项目先具备可启动、可执行、可查询、可回归的最小纵向切片。

## 修改前

项目缺少可运行的后端主流程、Demo 页面、受控动作执行链路和最小状态查询接口，无法验证 persona 驱动 run 的基础可行性。

## 修改后

项目新增 FastAPI 入口、Demo Run API、LangGraph 最小闭环、Playwright 执行器、内存态 run 存储、基础 schema、Demo 页面与最小测试，用固定 persona 与固定 task 跑通了从启动 run 到查询报告的基础链路。

## 修改文件

- `backend/main.py`
  - 修改原因：补齐应用入口。
  - 修改内容：创建 FastAPI 应用，注册 API 路由并挂载内置 demo 静态页面目录。
  - 修改影响：提供最小运行入口，支持本地启动与接口验证。
- `backend/api/router.py`、`backend/api/routes/demo_runs.py`
  - 修改原因：暴露最小闭环的 HTTP 查询面。
  - 修改内容：新增 demo run 启动、状态查询、步骤查询、报告查询与健康检查接口。
  - 修改影响：调用方可以通过 API 启动和轮询一次 demo run。
- `backend/graph/demo_run_graph.py`、`backend/graph/run_state.py`
  - 修改原因：搭建最小 LangGraph 主流程。
  - 修改内容：实现 load context、init session、observe、decide、execute、validate、log、finalize 等状态节点与共享状态结构。
  - 修改影响：run 执行逻辑从接口层下沉到图编排层，形成最小闭环。
- `backend/execution/observer.py`、`backend/execution/playwright_adapter.py`
  - 修改原因：补齐页面观察和受控动作执行。
  - 修改内容：实现页面可见文本、可交互元素、表单字段、错误提示采集，以及 navigate/click/fill/wait 等动作执行。
  - 修改影响：图节点可以基于真实页面事实决策并执行动作。
- `backend/analysis/report_builder.py`、`backend/analysis/validator.py`
  - 修改原因：补齐最小验证与报告生成能力。
  - 修改内容：实现规则验证、成功失败判定、摩擦信号汇总与最终 run 报告生成。
  - 修改影响：run 在结束后可返回结构化结果与基础建议。
- `backend/schemas/run_schemas.py`、`backend/stores/in_memory_run_store.py`
  - 修改原因：统一运行时数据结构并保存执行结果。
  - 修改内容：定义 request、page state、action、execution result、validation result、step log、report、record 等 schema，并提供内存态 run 存储。
  - 修改影响：API、图节点与执行层共享一致的数据契约。
- `backend/fixtures/demo_site/index.html`
  - 修改原因：提供稳定可复现的内置测试页面。
  - 修改内容：实现开始体验、填写表单、校验必填和提交成功文案的最小 demo 页面。
  - 修改影响：本地验证不依赖外部网站，可重复回归。
- `tests/test_demo_run_api.py`、`tests/test_validator.py`
  - 修改原因：补齐最小自动化回归。
  - 修改内容：验证健康检查、启动 run 接口和 validator 的成功/失败分支。
  - 修改影响：为最小闭环提供基础测试保障。
- `.claude/CLAUDE.md`、`introduction/TODO/DONE.md`、`introduction/环境说明/常见命令.md`、`introduction/数据流/核心数据流.md`、`introduction/项目文档/*`
  - 修改原因：同步项目文档与阶段进度。
  - 修改内容：补充项目说明、环境、数据流与已完成事项记录。
  - 修改影响：文档与首个最小闭环实现对齐。

## 验证结果

- 验证方式：`tests/test_demo_run_api.py`、`tests/test_validator.py`、内置 demo 页面人工回归
- 验证结果：通过

## TODO / DONE 同步

- TODO：未记录
- DONE：同步记录最小 Demo Run 闭环完成情况

## 后续事项

- 后续可在最小闭环基础上继续扩展真实 persona、正式 task、持久化存储与更完整的恢复分支。
