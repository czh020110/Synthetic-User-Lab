# TODO

## 本次可提交任务

- [ ] T-001（P0）：在 `backend/graph/run_graph.py` 中把 `ready_for_next_action` 与 `abnormal_stuck` 结果接成真正的受控恢复动作，并区分恢复后继续主链路与终止收尾。
  - 来源 STEP：无
  - 依赖：无
  - 验收标准：一次 recovery step 会留下独立的动作前后页面快照、恢复动作执行结果与最终验证结论；`abnormal_stuck` 不再只直接收尾失败。

- [ ] T-002（P0）：为受控恢复动作补齐 `tests/test_demo_run_api.py` 与必要回归，确认 `/steps` 与 `/report` 在恢复分支中稳定透出 `before_page_state`、`after_page_state`、`wait_observation_traces[].screenshot_path`。
  - 来源 STEP：无
  - 依赖：T-001
  - 验收标准：本次提交内可验证完成。

## 注意

- TODO.md 只记录下一次开发要完成的细粒度任务。
- 每次提交后不要手动编辑 TODO/DONE；调用 `scripts/rotate_todo.py`，传入下一次提交可完成的新 TODO 列表。
- 脚本会把旧 `TODO.md` 中的未完成项按已验收完成迁移到 `DONE.md`，并用新列表重写 `TODO.md`。
