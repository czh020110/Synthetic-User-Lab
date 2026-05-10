# 统一迁移提示词到 backend-prompt

## Commit

统一迁移提示词到 backend-prompt

## 变更目标

把项目内分散在 graph 与 report 实现中的提示词统一收敛到 `backend/prompt/` 目录，明确 graph 决策/验证提示词与报告分析提示词的职责边界，并补充报告提示词里 `conclusion` 三档取值的中文含义说明，避免提示词文案继续散落在运行逻辑中。

## 修改前

`backend/graph/graph_prompt.py` 同时承载决策与验证提示词；`backend/analysis/report_builder.py` 直接内嵌报告分析 system prompt。提示词内容分散在运行实现内部，职责边界不够清晰，后续调整 `conclusion` 语义时也需要同时修改报告实现文件。

## 修改后

graph 决策/验证提示词已迁移到 `backend/prompt/graph.py`，报告分析提示词已迁移到 `backend/prompt/report.py`，并通过 `backend/prompt/__init__.py` 统一导出。`backend/graph/run_graph.py` 与 `backend/analysis/report_builder.py` 改为从提示词包读取对应 prompt；报告提示词额外补充了 `keep` / `optimize` / `fix` 的中文含义说明，方便后续维护与调试。

## 修改文件

- `backend/prompt/graph.py`
  - 修改原因：需要把 graph 决策/验证提示词从运行实现中拆出来，形成独立提示词模块。
  - 修改内容：承接原 `graph_prompt.py` 中的 `decide`、`decide_input`、`validate`、`validate_input` 文案，保留动作决策与步骤验证的模板结构。
  - 修改影响：graph 运行逻辑不再内嵌提示词字符串，后续调整 prompt 更集中。

- `backend/prompt/report.py`
  - 修改原因：报告分析提示词需要独立管理，并补充结论级别语义说明。
  - 修改内容：抽出 `RECOMMENDATION_SYSTEM_PROMPT`，保留基于本次 run 证据生成详细报告的约束，并补充 `keep` / `optimize` / `fix` 的中文含义说明。
  - 修改影响：报告生成逻辑的 prompt 语义更清晰，后续维护 `conclusion` 规则更直接。

- `backend/prompt/__init__.py`
  - 修改原因：需要一个统一的 prompt 包入口，方便调用方稳定导入。
  - 修改内容：集中导出 graph 与 report 相关提示词常量。
  - 修改影响：调用方从单一包路径读取 prompt，减少分散导入。

- `backend/graph/run_graph.py`
  - 修改原因：graph 执行节点需要改用新的 prompt 包入口。
  - 修改内容：把决策/验证 prompt 导入切换到 `backend.prompt.graph`。
  - 修改影响：运行图主链路的业务逻辑保持不变，但 prompt 来源改为独立模块。

- `backend/analysis/report_builder.py`
  - 修改原因：报告生成器需要改用独立的报告提示词模块。
  - 修改内容：把 system prompt 导入切换到 `backend.prompt.report.RECOMMENDATION_SYSTEM_PROMPT`，删除原内嵌 prompt 函数。
  - 修改影响：报告 builder 只保留数据组装与模型调用职责，提示词文案迁出实现文件。

- `backend/graph/graph_prompt.py`
  - 修改原因：旧提示词文件已被新 prompt 包替代。
  - 修改内容：删除旧文件，不再保留兼容层。
  - 修改影响：旧导入路径失效，调用方必须迁移到 `backend/prompt/`。

- `.claude/introduction/数据流/核心数据流.md`
  - 修改原因：真实调用链中 prompt 的来源和职责边界发生变化。
  - 修改内容：更新本次更新原因、链路目标、决策节点、报告收尾节点和相关文件清单，补充 `backend/prompt/graph.py`、`backend/prompt/report.py`、`backend/prompt/__init__.py` 的职责说明。
  - 修改影响：核心数据流文档与当前代码结构保持一致，便于后续继续扩展报告和验证逻辑。

- `.claude/introduction/项目实现目标/项目目标.md`
  - 修改原因：实现发现需要记录提示词职责拆分这一结构性变化。
  - 修改内容：补充提示词统一迁移到 `backend/prompt/` 的实现发现，并记录报告 prompt 对 `conclusion` 含义的说明。
  - 修改影响：接手开发者可以直接看到当前 prompt 组织方式。

- `.claude/introduction/TODO/DONE.md`
  - 修改原因：需要记录本轮已验证完成的提示词收敛事项。
  - 修改内容：新增一条 DONE 记录，说明 graph/report 提示词统一迁移与 `conclusion` 含义补充已经完成并验证。
  - 修改影响：阶段进度与当前已落地的 prompt 结构保持一致。

## 验证结果

- 验证方式：`D:/Env/Anaconda/Anaconda3-2024.06-1/envs/synthetic-user-lab/python.exe -m pytest tests/test_report_builder.py tests/test_validator.py`
- 验证结果：通过
- 验证方式：`D:/Env/Anaconda/Anaconda3-2024.06-1/envs/synthetic-user-lab/python.exe -m pytest tests/test_demo_run_api.py`
- 验证结果：通过

## TODO / DONE 同步

- TODO：未调整；当前仍保留“最小恢复分支”作为下一次可提交任务，未强行轮转，因为本次提交主要是提示词目录迁移，不属于当前 TODO 列表中的恢复分支任务。
- DONE：已更新；新增“graph 与 report 提示词统一迁移到 `backend/prompt/`”的已完成记录。

## 后续事项

- 后续如果继续调整 prompt 文案，优先修改 `backend/prompt/`，不要把提示词再写回 graph / report 实现文件。
- 如果后续需要进一步同步数据流或项目目标，可以继续补充提示词包在 graph/report 之间的职责边界。