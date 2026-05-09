项目:Synthetic User Lab

# 项目环境说明

项目环境: @introduction/环境说明/本地开发环境.md
项目常见命令: @introduction/环境说明/常见命令.md

## 运行验证注意事项

- 默认使用 `synthetic-user-lab` Conda 环境，避免系统 Python 缺少 Playwright 等依赖。

# 项目文档说明

## 分块文档说明

1. 项目定位、边界与设计原则
   @introduction/项目文档/01-项目定位边界与设计原则.md
   - 用于理解项目为什么存在、解决什么问题、第一阶段边界与核心设计原则。

2. 功能模块与 API 接口
   @introduction/项目文档/02-功能模块与API接口.md
   - 用于实现 persona、task、observer、planner、validator、report 等功能模块和基础 API。

3. RAG 记忆与上下文系统
   @introduction/项目文档/03-RAG记忆与上下文系统.md
   - 用于实现产品知识库、UI 经验库、失败恢复库、评测规则库和检索策略。

4. 系统架构、技术栈与存储职责
   @introduction/项目文档/04-系统架构技术栈与存储职责.md
   - 用于搭建项目目录、技术栈选型、服务分层以及 PostgreSQL / Redis 职责划分。

5. LangGraph 执行流程与数据模型
   @introduction/项目文档/05-LangGraph流程与数据模型.md
   - 用于实现 run 流程、异常恢复分支以及 Project / Persona / Task / Run / StepLog 等数据对象。

6. 安全边界与 MVP 路线图
   @introduction/项目文档/06-安全边界与MVP路线图.md
   - 用于判断 MVP 先做什么、哪些操作必须限制，以及后续阶段如何演进。

# 项目核心数据流

项目核心数据流说明: @introduction/数据流/核心数据流.md

# 技术接口规范

LangChain 与 LangGraph 接口规范: @introduction/LangChain与LangGraph接口规范.md

# TODO

项目整体计划步骤: @introduction/TODO/STEP.md

当前项目已完成具体模块功能点: @introduction/TODO/DONE.md

项目细粒度功能点计划: @introduction/TODO/TODO.md

# 修改记录

修改记录目录: @introduction/修改记录/

- `introduction/修改记录/` 按一次 git commit 维度维护。
- 文件名使用对应 commit description，空格替换为 `-`。
- 不再维护修改记录汇总索引；需要回顾历史时，按 commit description 读取对应修改记录文件。
