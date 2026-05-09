# 添加demo-graph-使用agent替代节点

## Commit

添加demo graph 使用agent替代节点

## 变更目标

把 demo graph 的关键决策环节从固定逻辑推进到 agent 驱动，为后续 persona 化执行和结构化推理打基础。

## 修改前

图节点中的决策主要依赖固定逻辑，persona 与 task 的固定上下文没有沉淀到 run 级 agent 初始化流程中。

## 修改后

demo graph 在 run 初始化阶段创建 agent，并将 persona 与 task 固定上下文注入 agent system prompt，使图执行开始具备按 run 级上下文决策的能力。

## 修改文件

- `backend/graph/demo_run_graph.py`
  - 修改原因：图节点需要接入 agent 决策。
  - 修改内容：在 `load_demo_context` 中创建当前 run 的 agent，并在决策节点中调用 agent 输出结构化动作。
  - 修改影响：最小闭环从纯规则推进到 agent 参与的执行模式。
- `backend/graph/graph_prompt.py`
  - 修改原因：agent 需要稳定提示词模板。
  - 修改内容：新增与整理 graph prompt 模板，用于向决策节点注入 persona、task 与页面事实。
  - 修改影响：prompt 与图节点职责更清晰，后续扩展更稳定。
- `backend/core/config.py`
  - 修改原因：agent 图运行复用统一配置。
  - 修改内容：同步必要运行配置接入。
  - 修改影响：图执行配置链路更集中。
- `introduction/TODO/DONE.md`
  - 修改原因：同步已完成事项。
  - 修改内容：记录 demo graph 已接入 run 级 agent。
  - 修改影响：阶段进度可追踪。

## 验证结果

- 验证方式：graph prompt 与 `demo_run_graph` 调用链人工检查、相关测试回归
- 验证结果：通过

## TODO / DONE 同步

- TODO：未记录
- DONE：记录决策与验证节点接入 run 级 agent 的阶段成果

## 后续事项

- 后续需要继续补齐验证节点的 agent 化与历史上下文隔离能力。
