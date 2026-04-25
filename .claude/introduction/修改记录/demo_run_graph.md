# demo_run_graph

## 按 run_id 区分 agent checkpointer 并显式传入历史步骤(最新修改)

- 修改的文件名和路径(单个文档只写一次):
  - `backend/graph/demo_run_graph.py`

- 修改前存在的问题:
  - agent 调用使用固定 `thread_id="demo_1"`，不同 run 之间可能共享同一段 agent 消息状态。
  - `decide_agent` 只接收 `previous_steps_count`，无法知道之前具体执行过哪些动作、执行结果和验证结论。

- 添加前未完成的功能:
  - 缺少按当前 run 隔离的 agent checkpointer 配置。
  - 决策 agent 缺少完整历史步骤上下文。

- 如何修复的(关键修改点说明):
  - 删除全局固定 `config`。
  - `decide_agent` 调用时使用 `thread_id=f"{state['run_id']}:decide"`。
  - `validate_agent` 调用时使用 `thread_id=f"{state['run_id']}:validate"`。
  - `decide_input_prompt` 新增传入 `previous_steps`，内容来自历史 `StepLog` 的 JSON 结构。

- 修改后的预期功能或修复后的预测结果:
  - 不同 run 的 decide / validate agent 消息状态互不污染。
  - `decide_agent` 能基于历史步骤详情避免重复无效动作，并理解之前执行过什么。

## 将 validate_progress 节点接入 validate agent(最新修改)

- 修改的文件名和路径(单个文档只写一次):
  - `backend/graph/demo_run_graph.py`

- 修改前存在的问题:
  - `validate_current_progress` 仍使用固定规则函数 `validate_progress()` 判断进展。
  - 当前图只有 `decide_action` 使用 agent，无法验证“决策 + 验证”两个语义节点都由 agent 参与的图执行模式。

- 添加前未完成的功能:
  - 缺少与 `decide_agent` 接入方式一致的 validate agent。
  - 验证节点无法根据 task、最新页面状态、执行结果和历史步骤生成结构化 agent 判断。

- 如何修复的(关键修改点说明):
  - 引入 `ValidationResult` 作为 `validate_agent` 的结构化输出模型。
  - 引入 `validate` 和 `validate_input` prompt，并创建 `validate_input_prompt`。
  - 新增 `validate_agent = create_agent(..., response_format=ValidationResult)`。
  - 在 `validate_current_progress` 中保留真实页面观察 `observe_page()`，将验证判断替换为 `validate_agent.ainvoke()`。

- 修改后的预期功能或修复后的预测结果:
  - `validate_progress` 节点仍保留 LangGraph 节点名，但内部验证判断改由 validate agent 完成。
  - 图执行过程中，动作决策和进展验证都可以通过 agent 的结构化输出参与闭环。

## 修复 run 异常失败时 error_message 为空、report 长期 409 且日志不清晰的问题(最新修改)

- 修改的文件名和路径(单个文档只写一次):
  - `backend/graph/demo_run_graph.py`

- 修改前存在的问题:
  - run 在初始化阶段异常时，`error_message` 可能为空字符串，排查困难。
  - 异常失败时可能没有最终报告，`/report` 长期返回 409。
  - 关键阶段缺少明确日志，不利于定位 `init_session` 与浏览器会话问题。

- 添加前未完成的功能:
  - 异常失败链路的可观测性和可查询性不完整。

- 如何修复的(关键修改点说明):
  - 在 `run_demo_workflow` 异常分支中将失败信息改为 `异常类型 + repr`。
  - 异常失败时若无报告，基于已有 steps 生成最小失败报告并写入存储。
  - 在 `init_session` 增加初始化开始与起始页面加载成功日志。

- 修改后的预期功能或修复后的预测结果:
  - 状态接口能返回可读失败原因。
  - 异常失败时 `/report` 也能返回失败报告，不再长期 409。
  - 日志可直接定位 run 在会话初始化或图执行阶段的失败点。
