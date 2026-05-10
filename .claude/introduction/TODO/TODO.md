# TODO

## 本次可提交任务

- [ ] T-001（P0）：在 backend/graph/run_graph.py 中把 wait_after_action 从等待观察推进为一次受控恢复动作并重新验证，覆盖 actionable 与 timeout 分支。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：本次提交内可验证完成

- [ ] T-002（P0）：为等待观察与恢复链路补齐 tests/test_validator.py、tests/test_demo_run_api.py 与必要的 tests/test_report_builder.py 回归，确认 wait_observation_* 与最终 conclusion 在报告中稳定透出。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：本次提交内可验证完成
