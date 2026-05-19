# TASK BOARD

## 维护规则

- 本文件是细粒度任务的唯一事实源，不再区分独立的 TODO / DONE 文件。
- 新任务应在准备开始实现前写入，而不是提交后再补。
- 如果当前已经存在 `未开始` / `进行中` / `阻塞` / `暂缓` 任务，不要覆盖它们；只有在确有新想法或新增需求时才直接追加新任务。
- 只有在当前没有未完成任务时，才写入下一批主任务。
- `T-xxx` 编号一旦分配后不重排、不复用；新增任务从当前最大编号继续递增。
- 任务状态只允许：`未开始` / `进行中` / `阻塞` / `暂缓` / `完成`。
- `最近完成` 只保留近期完成项；过久记录可按需裁剪，避免文档膨胀。

## 进行中

无

## 未开始

- [ ] T-016（P0）：在 `backend/graph/run_graph.py` 中把 `ready_for_next_action` 与 `abnormal_stuck` 结果接成真正的受控恢复动作，并区分恢复后继续主链路与终止收尾。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：一次 recovery step 会留下独立的动作前后页面快照、恢复动作执行结果与最终验证结论；`abnormal_stuck` 不再只直接收尾失败。

- [ ] T-017（P0）：为受控恢复动作补齐 `tests/test_demo_run_api.py` 与必要回归，确认 `/steps` 与 `/report` 在恢复分支中稳定透出 `before_page_state`、`after_page_state`、`wait_observation_traces[].screenshot_path`。
  - 来源 STEP：无
  - 依赖：T-016
  - 验收标准：本次提交内可验证完成。

## 阻塞

无

## 暂缓

无

## 最近完成

- [x] T-018（P0）：迁移 introduction 到根目录 .claude_introduction
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：`.claude/introduction` 完成迁移为根目录 `.claude_introduction`，且 `.claude` 内相关引用全部更新并可检索到新路径
  - 完成日期：2026-05-19
  - 验证方式：python .claude/skills/update-todo/scripts/todo_cli.py prune-recent --keep 12 --dry-run --json && python .claude/skills/query-project/scripts/query_introduction_rag.py --sync-config-status && python .claude/skills/query-project/scripts/query_introduction_rag.py --query "当前待办是什么" --top-k 2 --format markdown --no-rerank && git status --short

- [x] T-001：搭建最小 Demo Run 闭环主流程并提供基础收尾能力
  - 来源 STEP：S-001
  - 验收标准：可通过 FastAPI 启动固定 demo run，并查询 status、steps、report，且 LangGraph 能完成 observe → decide → execute → validate → log → finalize 的闭环。
  - 完成日期：2026-04-24
  - 验证方式：tests/test_demo_run_api.py、tests/test_validator.py、内置 demo 页面人工回归
  - 关联 Commit：run1最小闭环

- [x] T-002：补充报错日志、失败报告与失败原因保留链路
  - 来源 STEP：S-001
  - 验收标准：失败 run 状态查询、`/report` 异常分支人工检查、最小测试回归可稳定看到失败原因。
  - 完成日期：2026-04-24
  - 验证方式：失败 run 状态查询、`/report` 异常分支人工检查、最小测试回归
  - 关联 Commit：修改文档, 添加报错日志

- [x] T-003：增加项目根目录 .env 配置导入与 API 前缀规范化
  - 来源 STEP：S-001
  - 验收标准：配置读取人工检查、FastAPI 启动导入检查。
  - 完成日期：2026-04-24
  - 验证方式：配置读取人工检查、FastAPI 启动导入检查
  - 关联 Commit：添加.env文件导入环境变量设置函数

- [x] T-004：将 demo graph 的决策与验证节点接入 run 级 agent
  - 来源 STEP：S-001
  - 验收标准：graph prompt 与 `demo_run_graph` 调用链人工检查、相关测试回归。
  - 完成日期：2026-04-25
  - 验证方式：graph prompt 与 `demo_run_graph` 调用链人工检查、相关测试回归
  - 关联 Commit：添加demo graph 使用agent替代节点

- [x] T-005：补齐 graph prompt、task schema 与 run 级上下文隔离逻辑
  - 来源 STEP：S-001
  - 验收标准：`tests/test_demo_run_api.py`、schema 与 prompt 链路人工检查。
  - 完成日期：2026-04-25
  - 验证方式：`tests/test_demo_run_api.py`、schema 与 prompt 链路人工检查
  - 关联 Commit：修改graph prompt以及agent逻辑

- [x] T-006：完成项目文档、阶段目标与核心数据流的结构化重整
  - 来源 STEP：无
  - 验收标准：文档人工检查。
  - 完成日期：2026-04-27
  - 验证方式：文档人工检查
  - 关联 Commit：更新claude项目文档

- [x] T-007：补充细粒度 TODO 与开发文档约束说明
  - 来源 STEP：无
  - 验收标准：文档人工检查。
  - 完成日期：2026-04-27
  - 验证方式：文档人工检查
  - 关联 Commit：更新claude项目文档2

- [x] T-008：按 git commit 维度重构修改记录并移除目录索引依赖
  - 来源 STEP：无
  - 验收标准：文档人工检查、修改记录引用搜索。
  - 完成日期：2026-05-09
  - 验证方式：文档人工检查、修改记录引用搜索
  - 关联 Commit：重构修改记录文档并移除目录索引

- [x] T-009：收敛运行报告结论并细化问题报告
  - 来源 STEP：无
  - 验收标准：`RunReport.conclusion` 固定为 `keep / optimize / fix`，并稳定输出真实问题报告。
  - 完成日期：2026-05-10
  - 验证方式：`tests/test_report_builder.py`、`tests/test_validator.py`、`tests/test_demo_run_api.py`
  - 关联 Commit：收敛运行报告结论并细化问题报告

- [x] T-010：统一迁移提示词到 backend-prompt
  - 来源 STEP：无
  - 验收标准：graph 与 report 提示词统一迁移到 `backend/prompt/`，相关测试通过。
  - 完成日期：2026-05-10
  - 验证方式：`python -m pytest tests/test_report_builder.py tests/test_validator.py`、`python -m pytest tests/test_demo_run_api.py`
  - 关联 Commit：统一迁移提示词到 backend-prompt
