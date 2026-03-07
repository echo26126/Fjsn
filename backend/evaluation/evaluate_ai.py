import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.llm_service import llm_service
from services.db_service import db_service


@dataclass
class EvalItem:
    case_id: str
    question: str
    expected_table: str
    expected_keywords: List[str]
    min_rows: int


def load_question_set(path: Path) -> List[EvalItem]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvalItem(
            case_id=item["id"],
            question=item["question"],
            expected_table=item["expected_table"],
            expected_keywords=list(item.get("expected_keywords", [])),
            min_rows=int(item.get("min_rows", 1)),
        )
        for item in data
    ]


def compute_metrics(case: EvalItem, resp: Dict[str, Any]) -> Dict[str, Any]:
    answer = str(resp.get("answer") or "")
    sql = str(resp.get("sql") or "")
    rows = resp.get("data") or []
    row_count = len(rows) if isinstance(rows, list) else 0
    err = str(resp.get("error") or "")

    sql_valid = sql.strip().lower().startswith("select")
    table_match = case.expected_table in sql
    row_match = row_count >= case.min_rows
    keyword_hit_count = sum(1 for kw in case.expected_keywords if kw in answer)
    keyword_hit = keyword_hit_count >= max(1, len(case.expected_keywords) // 2)
    has_error = bool(err)
    unanswered = ("无法回答" in answer) or ("未找到相关数据" in answer)
    answered = (not has_error) and (not unanswered) and row_count > 0

    accuracy_pass = sql_valid and table_match and row_match and answered
    explainability_pass = sql_valid and row_count > 0 and keyword_hit

    return {
        "case_id": case.case_id,
        "question": case.question,
        "expected_table": case.expected_table,
        "sql": sql,
        "answer": answer,
        "row_count": row_count,
        "error": err,
        "sql_valid": sql_valid,
        "table_match": table_match,
        "row_match": row_match,
        "keyword_hit": keyword_hit,
        "accuracy_pass": accuracy_pass,
        "explainability_pass": explainability_pass,
        "answered": answered,
    }


def ratio(items: List[Dict[str, Any]], key: str) -> float:
    if not items:
        return 0.0
    return round(sum(1 for it in items if it.get(key)) * 100 / len(items), 2)


def render_report(metrics: List[Dict[str, Any]], output_json: Path) -> str:
    total = len(metrics)
    answered_rate = ratio(metrics, "answered")
    sql_valid_rate = ratio(metrics, "sql_valid")
    accuracy_rate = ratio(metrics, "accuracy_pass")
    explainability_rate = ratio(metrics, "explainability_pass")

    failures = [m for m in metrics if not m["accuracy_pass"]]
    bad_lines = []
    for m in failures:
        bad_lines.append(
            f"- {m['case_id']} | {m['question']} | table_match={m['table_match']} | row_match={m['row_match']} | answered={m['answered']} | error={m['error'] or 'None'}"
        )
    if not bad_lines:
        bad_lines = ["- 无"]

    return "\n".join(
        [
            "# AI问数评测报告",
            "",
            f"- 评测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 用例总数: {total}",
            f"- 可回答率(Answered): {answered_rate}%",
            f"- SQL有效率(SQL Valid): {sql_valid_rate}%",
            f"- 准确率(Accuracy): {accuracy_rate}%",
            f"- 可解释性通过率(Explainability): {explainability_rate}%",
            f"- 结果明细: {output_json.name}",
            "",
            "## 未通过用例",
            *bad_lines,
            "",
            "## 结论",
            "- POC阶段建议准确率和可解释性都保持在90%以上。",
            "- 若未达标，优先补充规则化SQL规划词典与别名映射。",
        ]
    )


async def run_eval(question_set: List[EvalItem]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for case in question_set:
        schema_info = db_service.get_schema_info()
        sql = await llm_service.generate_sql(case.question, schema_info)
        if "CANNOT ANSWER" in (sql or "").upper():
            response = {"answer": "无法回答", "sql": sql, "data": [], "error": ""}
            metrics = compute_metrics(case, response)
            results.append(metrics)
            continue
        data = await db_service.execute_query(sql) if sql else []
        response = {
            "answer": await llm_service.analyze_data(case.question, data) if data else "未找到相关数据。",
            "sql": sql,
            "data": data,
            "error": "" if sql else "SQL为空",
        }
        metrics = compute_metrics(case, response)
        results.append(metrics)
    return results


def main():
    base_dir = Path(__file__).resolve().parent
    question_set_file = base_dir / "question_set.json"
    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = output_dir / f"eval-result-{ts}.json"
    output_md = output_dir / f"eval-report-{ts}.md"

    question_set = load_question_set(question_set_file)
    metrics = asyncio.run(run_eval(question_set))
    output_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_report(metrics, output_json)
    output_md.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nJSON: {output_json}")
    print(f"MD: {output_md}")


if __name__ == "__main__":
    main()
