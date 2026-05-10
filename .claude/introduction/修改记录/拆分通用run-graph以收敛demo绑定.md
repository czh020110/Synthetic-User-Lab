# 拆分通用run-graph以收敛demo绑定

## Commit

拆分通用run-graph以收敛demo绑定

## 变更目标

将最小 run 闭环中的 demo 专属上下文与共享运行编排解耦，让共享 schema、graph state、运行节点与异常兜底不再被 demo 命名和默认页面细节污染，同时保留现有 `/runs/demo/*` API 作为最小验证入口。

## 修改前

原有 `backend/graph/demo_run_graph.py` 同时承担 demo 默认 persona/task 装配、LangGraph 通用节点、主流程编排和异常失败收尾职责；共享层仍使用 `DemoPersona`、`DemoTask`、`DemoRunState` 命名，导致 demo 语义渗透到 schema、graph state、validator、store 与测试；路由层也直接了解 demo start_url 与默认上下文装配细节。

## 修改后

新增通用 `backend/graph/run_graph.py`，统一承载 `load_context -> init_session -> observe -> decide -> execute -> validate -> log -> finalize` 主链路与异常兜底；`backend/graph/demo_run_graph.py` 收敛为 demo 场景适配层，只负责默认 persona/task、demo start_url 和对通用 graph 的包装调用；共享模型泛化为 `Persona`、`Task`、`RunState`，路由层只通过 helper 创建占位记录并启动 demo workflow，现有验证逻辑与 demo API 查询面保持不变。

## 修改文件

- `backend/graph/run_graph.py`
  - 修改原因：需要把原 demo graph 中可复用的运行节点与异常兜底抽到共享层。
  - 修改内容：新增通用 graph 编排模块，沉淀 `create_run_agents()`、`init_session()`、`observe_current_page()`、`decide_next_action()`、`execute_current_action()`、`validate_current_progress()`、`log_current_step()`、`route_after_log()`、`finalize_report()`、`build_run_graph()` 与 `run_workflow()`；保留 agent 调用、规则护栏补强和异常补失败报告的原有行为。
  - 修改影响：后续非 demo run 可复用同一条主流程，只需替换 `load_context` 节点即可接入。

- `backend/graph/demo_run_graph.py`
  - 修改原因：需要把 demo 专属逻辑收拢到独立适配层，避免继续污染共享 graph。
  - 修改内容：保留并明确 `build_demo_persona()`、`build_demo_task()`、`create_demo_placeholder_record()`、`load_demo_context()`、`build_demo_run_graph()`、`run_demo_workflow()`，其中主流程执行改为委托通用 `run_graph`。
  - 修改影响：demo 场景仍保持原入口，但默认上下文只在 demo 层装配。

- `backend/schemas/run_schemas.py`
  - 修改原因：共享 schema 不应继续以 demo 类型名作为公共契约。
  - 修改内容：将共享模型从 `DemoPersona` / `DemoTask` 泛化为 `Persona` / `Task`，并保持现有运行请求、页面观察、动作、验证、步骤日志和报告结构可继续复用。
  - 修改影响：validator、graph、store 与测试都改为依赖通用语义模型。

- `backend/graph/run_state.py`
  - 修改原因：LangGraph 状态定义需要和通用 schema 对齐。
  - 修改内容：将共享状态从 `DemoRunState` 收敛为 `RunState`，并将 `persona`、`task` 等字段改为通用类型引用。
  - 修改影响：共享 graph 可以接受不同场景的上下文装配结果，不再限定 demo 命名。

- `backend/api/routes/demo_runs.py`
  - 修改原因：路由层不应继续持有 demo 业务装配细节。
  - 修改内容：启动接口改为调用 `create_demo_placeholder_record()` 创建占位记录，并继续通过 `run_demo_workflow()` 启动后台任务；保留现有 `/runs/demo/*` 查询接口。
  - 修改影响：demo API 仍可兼容现有调用方式，但路由层职责更聚焦于 HTTP 入口。

- `backend/analysis/validator.py`
  - 修改原因：共享验证层需要跟随通用 task 概念。
  - 修改内容：仅做类型与 import 跟随调整，保持现有规则护栏逻辑不变。
  - 修改影响：验证护栏继续按真实页面与历史步骤判定成功、失败、卡住与偏航。

- `backend/stores/in_memory_run_store.py`
  - 修改原因：内存存储需要跟随新的共享记录与报告类型。
  - 修改内容：更新存储层对 `RunRecord`、`RunReport`、`RunStatusResponse` 的通用引用。
  - 修改影响：run 状态、步骤日志与报告的存取接口不变。

- `tests/test_validator.py`
  - 修改原因：需要验证通用 graph 迁移后规则护栏与节点行为未回归。
  - 修改内容：测试改为引用 `backend.graph.run_graph` 与新的 `Persona` / `Task` 类型，并保留对验证护栏、`validate_current_progress()` 与 `route_after_log()` 的回归断言。
  - 修改影响：为共享 graph 抽离后的关键行为提供最小自动化保障。

- `.claude/introduction/数据流/核心数据流.md`
  - 修改原因：真实调用链已从 demo graph 单体实现改为“demo 适配层 + 通用 run graph”结构。
  - 修改内容：重写最小 run 闭环数据流，补充通用 `run_graph.py`、demo 上下文装配层、共享 `RunState` / `Task` / `Persona`、状态流转与异常分支说明。
  - 修改影响：后续接手开发时可直接按新分层理解真实链路。

- `.claude/introduction/修改记录/拆分通用run-graph以收敛demo绑定.md`
  - 修改原因：需要按本次 commit 维度沉淀修改记录。
  - 修改内容：记录本次拆分通用 graph、收口 demo 绑定、共享类型去 demo 化与测试跟随调整。
  - 修改影响：后续回顾该轮重构时可直接定位本次改动目的与影响。

## 验证结果

- 验证方式：`D:/Env/Anaconda/Anaconda3-2024.06-1/envs/synthetic-user-lab/python.exe -m pytest tests/test_validator.py tests/test_demo_run_api.py`
- 验证结果：通过，15 passed

## TODO / DONE 同步

- TODO：将当前已完成的拆分任务从 `TODO.md` 迁移，并写入下一次提交要推进的最小恢复分支任务。
- DONE：将本次完成的通用 graph 拆分、共享类型去 demo 化、demo API 收口与回归测试事项迁入 `DONE.md`。

## 后续事项

- 在通用 `run_graph.py` 上继续实现最小恢复分支，首次命中 `recovery_candidate` 时执行一次受控恢复动作并重新验证。
- 为恢复分支补齐 demo workflow 与 graph 层回归测试，确保恢复后仍能正确生成最终报告。
