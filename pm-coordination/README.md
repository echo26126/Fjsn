# 多 Agent 调度文档规范

## 目录说明

- `assignments/`：我发布给各 Agent 的任务分配单
- `reports/`：各 Agent 完成后提交的回执

## 时间戳命名规范

- 分配单：`ASSIGNMENT-YYYYMMDD-HHMMSS.md`
- 完成回执：`REPORT-<AGENT>-YYYYMMDD-HHMMSS.md`

## 流程约定

1. 我每次派单时，创建一份新的分配单。
2. 每个 Agent 完成后，按自己的 Agent 名称与完成时间戳创建回执。
3. 回执必须引用分配单编号，并写明交付物、验证结果、风险与阻塞。

## 统一字段

- Agent 名称
- 对应分配单
- 开始时间 / 完成时间
- 完成项
- 产出文件
- 验证记录
- 风险与阻塞
- 需 CTO 决策项
