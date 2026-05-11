# TODO

## 本次可提交任务

- [ ] T-001（P0）：在 backend/graph/run_graph.py 中把 ready_for_next_action 与 abnormal_stuck 结果接成一次真正的受控恢复动作，并区分恢复后继续主链路与终止收尾。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：本次提交内可验证完成

- [ ] T-002（P0）：为恢复动作接入后的 steps / report / API 输出补齐 tests/test_validator.py、tests/test_report_builder.py 与必要的 tests/test_demo_run_api.py 回归，确认 wait trace、elapsed_ms、timeout_ms 与 terminal_decision 稳定透出。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：本次提交内可验证完成
