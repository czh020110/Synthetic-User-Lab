# 修改graph-prompt以及agent逻辑

## Commit

修改graph prompt以及agent逻辑

## 变更目标

统一 graph prompt 职责，并让 run 级 agent 的决策与验证输入边界更清晰。

## 修改前

固定上下文、动态上下文和步骤历史的职责边界不清晰，决策和验证节点的输入结构也不够稳定。

## 修改后

prompt 模板区分了 system prompt 与动态输入，决策节点补充了历史步骤详情，验证节点也拥有独立的结构化提示词和输入模板，run 级 agent 的上下文隔离更完整。

## 修改文件

- `backend/graph/graph_prompt.py`
  - 修改原因：prompt 职责边界不清晰。
  - 修改内容：梳理 decide / validate system prompt 与动态输入模板，补齐 persona/task 占位符和历史步骤占位符。
  - 修改影响：agent 决策与验证都可以依赖统一的 prompt 结构。
- `backend/graph/demo_run_graph.py`
  - 修改原因：需要把新的 prompt 结构接到图执行里。
  - 修改内容：按 run 级别创建 decide / validate agent，传入历史步骤和页面状态，并按 run_id 隔离 agent 状态。
  - 修改影响：不同 run 的 agent 上下文不再互相污染。
- `backend/api/routes/demo_runs.py`
  - 修改原因：启动 run 时的占位 task 需要与新 schema 对齐。
  - 修改内容：将 pending task 的成功条件迁移到 `success_criteria`。
  - 修改影响：启动请求和 task schema 保持一致。
- `backend/analysis/validator.py`
  - 修改原因：规则验证逻辑需要适配新的 task 成功结构。
  - 修改内容：改为使用 `success_criteria` 列表判断成功。
  - 修改影响：规则验证与 task schema 保持一致。
- `backend/schemas/run_schemas.py`
  - 修改原因：数据结构需要适配 agent 与 task 语义。
  - 修改内容：调整 `DemoTask`、`RunRequest` 等 schema 的职责边界与字段说明。
  - 修改影响：页面、图节点与验证器共用统一契约。
- `introduction/TODO/DONE.md`
  - 修改原因：同步阶段完成记录。
  - 修改内容：记录 graph prompt 与 agent 逻辑已补齐。
  - 修改影响：阶段进度可追踪。

## 验证结果

- 验证方式：`tests/test_demo_run_api.py`、schema 与 prompt 链路人工检查
- 验证结果：通过

## TODO / DONE 同步

- TODO：未记录
- DONE：记录 graph prompt、task schema 与 run 级上下文隔离逻辑完成

## 后续事项

- 后续可继续扩展历史步骤摘要压缩和更细粒度的验证提示词。
