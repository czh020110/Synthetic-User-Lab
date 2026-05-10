# TODO

## 本次可提交任务

- [ ] T-001（P0）：在 `backend/graph/run_graph.py` 中接入最小恢复分支：首次命中 `recovery_candidate` 时执行一次受控恢复动作并重新验证，同时保留恢复前后的步骤日志与最终报告收尾链路。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：本次提交内可验证完成

- [ ] T-002（P0）：为最小恢复分支补齐 `tests/test_validator.py`、`tests/test_demo_run_api.py` 与必要的 `tests/test_report_builder.py` 回归，确认恢复后 demo API 仍能生成包含 `conclusion` 的最终报告。
  - 来源 STEP：无
  - 依赖：T-001
  - 验收标准：本次提交内可验证完成
