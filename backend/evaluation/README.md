# AI问数评测说明

## 目标

在 POC 阶段量化问数质量，持续跟踪可回答率、准确率、可解释性。

## 数据与用例

- 用例文件：`evaluation/question_set.json`
- 输出目录：`evaluation/output/`

## 运行方式

在 `backend` 目录执行：

```bash
python evaluation/evaluate_ai.py
```

## 指标定义

- 可回答率：返回无错误且非“无法回答/无数据”的比例
- SQL有效率：生成 SQL 以 `SELECT` 开头的比例
- 准确率：SQL有效 + 目标表命中 + 行数达标 + 问题被回答
- 可解释性通过率：SQL有效 + 有数据 + 答案命中关键业务词

## 达标建议

- 可回答率 ≥ 90%
- 准确率 ≥ 90%
- 可解释性通过率 ≥ 90%
