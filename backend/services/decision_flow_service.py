from datetime import datetime
import re
from uuid import uuid4

from sqlalchemy.orm import Session

from models.alert_event import AlertEvent
from models.alert_followup import AlertFollowup
from models.execution_light import ExecutionLight
from models.recommendation import Recommendation
from services.december_report_service import BASE_NAMES, december_report_service
from services.december_sales_service import december_sales_service
from services.llm_service import llm_service
from services.lp_optimizer import build_params, solve_three_scenarios


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"

INVENTORY_CAPACITY = {
    "安砂建福": 15.7,
    "永安建福": 5.5,
    "顺昌炼石": 5.5,
    "福州炼石": 5.9,
    "宁德建福": 5.15,
    "金银湖水泥": 15.7,
}


class DecisionFlowService:
    def list_alerts(self, db: Session, limit: int = 100):
        return db.query(AlertEvent).order_by(AlertEvent.updated_at.desc()).limit(limit).all()

    def create_alert(self, db: Session, payload: dict):
        row = AlertEvent(
            alert_id=payload.get("alert_id") or _new_id("ALERT"),
            alert_level=payload.get("alert_level") or "P2",
            alert_type=payload.get("alert_type") or "履约风险",
            alert_status=payload.get("alert_status") or "新建",
            source_type=payload.get("source_type") or "auto",
            alert_title=payload.get("alert_title") or "",
            alert_content=payload.get("alert_content") or "",
            severity_tag=payload.get("severity_tag") or "警告",
            context_json=payload.get("context_json") or "",
            affected_org_name=payload.get("affected_org_name") or "",
            sku_name=payload.get("sku_name") or "",
            gap_qty_ton=payload.get("gap_qty_ton") or 0,
            fulfillment_rate_pred=payload.get("fulfillment_rate_pred") or 0,
            recommendation_ref_id=payload.get("recommendation_ref_id") or "",
            owner_user=payload.get("owner_user") or "",
            assignee_user=payload.get("assignee_user") or "",
            process_status=payload.get("process_status") or "待跟进",
            process_result=payload.get("process_result") or "",
            action_deadline=payload.get("action_deadline") or "",
            note=payload.get("note") or "",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update_alert(self, db: Session, alert_id: str, payload: dict):
        row = db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id).first()
        if not row:
            return None
        for key in [
            "alert_level",
            "alert_type",
            "alert_status",
            "source_type",
            "alert_title",
            "alert_content",
            "severity_tag",
            "context_json",
            "affected_org_name",
            "sku_name",
            "gap_qty_ton",
            "fulfillment_rate_pred",
            "recommendation_ref_id",
            "owner_user",
            "assignee_user",
            "process_status",
            "process_result",
            "action_deadline",
            "note",
        ]:
            if key in payload and payload[key] is not None:
                setattr(row, key, payload[key])
        db.commit()
        db.refresh(row)
        return row

    def list_followups(self, db: Session, alert_id: str):
        return db.query(AlertFollowup).filter(AlertFollowup.alert_id == alert_id).order_by(AlertFollowup.created_at.desc()).all()

    def create_followup(self, db: Session, alert_id: str, payload: dict):
        row = AlertFollowup(
            alert_id=alert_id,
            action_type=payload.get("action_type") or "跟进",
            content=payload.get("content") or "",
            operator=payload.get("operator") or "",
            result_status=payload.get("result_status") or "",
        )
        db.add(row)
        alert_row = db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id).first()
        if alert_row:
            if payload.get("result_status"):
                alert_row.process_status = payload.get("result_status")
            if payload.get("content"):
                alert_row.process_result = payload.get("content")
        db.commit()
        db.refresh(row)
        return row

    def list_recommendations(self, db: Session, alert_id: str = "", limit: int = 100):
        q = db.query(Recommendation)
        if alert_id:
            q = q.filter(Recommendation.alert_id == alert_id)
        return q.order_by(Recommendation.updated_at.desc()).limit(limit).all()

    def create_recommendation(self, db: Session, payload: dict):
        row = Recommendation(
            recommendation_id=payload.get("recommendation_id") or _new_id("REC"),
            alert_id=payload.get("alert_id") or "",
            recommendation_role=payload.get("recommendation_role") or "PRIMARY",
            recommendation_summary=payload.get("recommendation_summary") or "",
            action_type=payload.get("action_type") or "",
            from_org_name=payload.get("from_org_name") or "",
            to_org_name=payload.get("to_org_name") or "",
            action_qty_ton=payload.get("action_qty_ton") or 0,
            est_net_gain=payload.get("est_net_gain") or 0,
            decision_status=payload.get("decision_status") or "待确认",
            decision_reason=payload.get("decision_reason") or "",
            decision_user=payload.get("decision_user") or "",
            decision_time=payload.get("decision_time") or "",
        )
        db.add(row)
        if row.alert_id:
            alert_row = db.query(AlertEvent).filter(AlertEvent.alert_id == row.alert_id).first()
            if alert_row and row.recommendation_role == "PRIMARY":
                alert_row.recommendation_ref_id = row.recommendation_id
        db.commit()
        db.refresh(row)
        return row

    def create_model_recommendation(self, db: Session, alert_id: str, operator: str):
        alert_row = db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id).first()
        if not alert_row:
            return None

        est_net_gain = 0
        try:
            scenario_result = solve_three_scenarios(build_params())
            balanced = scenario_result.get("scenarios", {}).get("balanced", {})
            est_net_gain = float(balanced.get("profit", 0) or 0)
        except Exception:
            est_net_gain = 0

        if alert_row.alert_type == "库存异常":
            action_type = "补库调拨"
            summary = f"运筹建议优先对{alert_row.affected_org_name or '目标组织'}执行跨组织补库，保障安全库存。"
            qty = max(alert_row.gap_qty_ton or 0, 80)
        elif alert_row.alert_type == "生产异常":
            action_type = "排产调整"
            summary = f"运筹建议对{alert_row.affected_org_name or '目标基地'}调整排产班次并预留应急产能。"
            qty = max(alert_row.gap_qty_ton or 0, 60)
        elif alert_row.alert_type == "单价异常" or alert_row.alert_type == "价格异常":
            action_type = "价格修正"
            summary = "模型建议按区域执行分层调价并同步重点客户沟通，控制毛利波动。"
            qty = 0
        elif alert_row.alert_type == "订单异常" or alert_row.alert_type == "履约风险":
            action_type = "履约保障"
            summary = "运筹建议按客户优先级进行订单重排，并锁定高优先级履约资源。"
            qty = max(alert_row.gap_qty_ton or 0, 50)
        else:
            action_type = "综合处置"
            summary = "模型建议先完成异常复核，再按供需与履约优先级执行综合调度。"
            qty = max(alert_row.gap_qty_ton or 0, 30)

        return self.create_recommendation(
            db,
            {
                "alert_id": alert_id,
                "recommendation_role": "PRIMARY",
                "recommendation_summary": summary,
                "action_type": action_type,
                "action_qty_ton": qty,
                "est_net_gain": est_net_gain,
                "decision_status": "待确认",
                "decision_user": operator,
            },
        )

    def _normalize_sku_name(self, material_name: str, spec: str) -> str:
        text = f"{material_name or ''} {spec or ''}".replace(" ", "").replace("（", "(").replace("）", ")")
        grade_hit = re.search(r"P\.[OC][0-9]{2}\.?[0-9]?", text, flags=re.IGNORECASE)
        grade = grade_hit.group(0).upper() if grade_hit else ""
        package = "散" if "散" in text else ("袋" if "袋" in text else "")
        if grade:
            return f"{grade}({package})" if package else grade
        model = str(spec or "").replace(" ", "").strip()
        material = str(material_name or "").replace(" ", "").strip()
        for token in ["建福", "炼石", "顺昌", "永安", "安砂", "福州", "宁德", "金银湖水泥", "水泥"]:
            material = material.replace(token, "")
        sku = model or material or "P.O42.5"
        return sku[:24]

    def regenerate_simulated_alerts(self, db: Session, operator: str = "system"):
        db.query(AlertEvent).filter(
            AlertEvent.source_type == "auto",
            AlertEvent.alert_title.like("自动监控触发：%"),
        ).delete(synchronize_session=False)
        db.commit()

        inventory_source = december_report_service._parse_inventory_sheet()
        rows = []
        for idx, base_name in enumerate(BASE_NAMES):
            base = str(base_name or "").strip()
            base_daily = inventory_source.get(base, {"days": [], "cement_inventory": []})
            days = list(base_daily.get("days", []))
            cement_series_ton = list(base_daily.get("cement_inventory", []))
            end_qty_wan = round((float(cement_series_ton[-1]) if cement_series_ton else 0.0) / 10000, 2)
            day_text = days[-1] if days else "12月31日"
            day_num = "".join([c for c in day_text if c.isdigit()])
            event_day = int(day_num) if day_num else 31
            capacity_wan = float(INVENTORY_CAPACITY.get(base, 0.0))
            safety_wan = round(capacity_wan * 0.25, 2)
            ratio = round((end_qty_wan / capacity_wan * 100), 1) if capacity_wan > 0 else 0.0
            low_risk = ratio <= 35
            high_risk = ratio >= 85

            sales_payload = december_sales_service.get_sales_payload(base=base, month="2025-12")
            sales_items = list(sales_payload.get("items", []))
            top_item = sorted(sales_items, key=lambda x: float(x.get("qty", 0) or 0), reverse=True)[0] if sales_items else {}
            sku_name = self._normalize_sku_name(top_item.get("material_name", ""), top_item.get("spec", ""))
            region = str(top_item.get("region", "") or "")
            qty_ton = max(int(abs(end_qty_wan - safety_wan) * 10000), 30)

            risk_tag = "库存偏低" if low_risk else ("库存偏高" if high_risk else "库存波动")
            suggestion = "建议优先补库并保障重点订单履约" if low_risk else ("建议加快去化并优化发运节奏" if high_risk else "建议滚动跟踪库存并优化调度")
            region_text = f"，重点区域：{region}" if region else ""
            row = self.create_alert(
                db,
                {
                    "alert_level": "P1" if low_risk else ("P2" if high_risk else "P3"),
                    "alert_type": "库存异常",
                    "source_type": "auto",
                    "alert_title": f"自动监控触发：{base}{sku_name}{risk_tag}",
                    "alert_content": f"2025年12月监测显示，{base}{sku_name}库存{end_qty_wan:.2f}万吨，安全线{safety_wan:.2f}万吨（库存占比{ratio:.1f}%）{region_text}，{suggestion}。",
                    "affected_org_name": base,
                    "sku_name": sku_name,
                    "gap_qty_ton": qty_ton,
                    "owner_user": f"{base}负责人",
                    "process_status": "待跟进",
                    "severity_tag": "严重" if low_risk else ("警告" if high_risk else "提示"),
                    "note": f"event_time:2025-12-{event_day:02d} {'09:30' if idx % 2 == 0 else '14:20'}",
                    "context_json": f'{{"month":"2025-12","base":"{base}","operator":"{operator}"}}',
                },
            )
            rows.append(row)
        return rows

    def _build_ai_analysis_simulated(self, db: Session, alert_id: str):
        alert_row = db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id).first()
        if not alert_row:
            return None
        base = alert_row.affected_org_name if alert_row.affected_org_name in BASE_NAMES else BASE_NAMES[0]
        inventory_source = december_report_service._parse_inventory_sheet()
        base_daily = inventory_source.get(base, {"days": [], "cement_inventory": []})
        days = list(base_daily.get("days", []))
        cement_series_ton = list(base_daily.get("cement_inventory", []))
        end_qty_wan = round((float(cement_series_ton[-1]) if cement_series_ton else 0.0) / 10000, 2)
        day_text = days[-1] if days else "12月31日"
        safety_wan = round(float(INVENTORY_CAPACITY.get(base, 0.0)) * 0.25, 2)
        ratio = round((end_qty_wan / float(INVENTORY_CAPACITY.get(base, 0.0)) * 100), 1) if float(INVENTORY_CAPACITY.get(base, 0.0)) > 0 else 0.0

        sales_payload = december_sales_service.get_sales_payload(base=base, month="2025-12")
        sales_items = list(sales_payload.get("items", []))
        top_sku_item = sorted(sales_items, key=lambda x: float(x.get("qty", 0) or 0), reverse=True)[0] if sales_items else {}
        sku_name = f"{top_sku_item.get('material_name', '')} {top_sku_item.get('spec', '')}".strip() or (alert_row.sku_name or "P.O42.5")

        low_risk = ratio <= 35
        high_risk = ratio >= 85
        action_type = "补库调拨" if low_risk else ("压库去化" if high_risk else "履约保障")
        qty_ton = (
            max(int(round((safety_wan - end_qty_wan) * 10000)), 50)
            if low_risk
            else (max(int(round((end_qty_wan - safety_wan) * 10000)), 50) if high_risk else max(int(alert_row.gap_qty_ton or 0), 30))
        )
        est_net_gain = round((max(0.0, 40 - ratio) * 1.2) if low_risk else (max(0.0, ratio - 55) * 0.7), 1)
        summary = (
            f"建议优先对{base}{sku_name}执行跨组织补库，并锁定高优先级订单履约资源。"
            if low_risk
            else (
                f"建议对{base}{sku_name}执行压库去化与区域协同发运，缓解库存占压。"
                if high_risk
                else f"建议对{base}{sku_name}执行稳态调度，按履约优先级滚动优化发运。"
            )
        )
        risk_text = (
            f"库存占比{ratio:.1f}%，低于安全阈值，存在履约缺口风险。"
            if low_risk
            else (f"库存占比{ratio:.1f}%，高于合理区间，存在压库与资金占压风险。" if high_risk else f"库存占比{ratio:.1f}%，处于波动区间，需要持续监控。")
        )
        root_cause = f"数据口径2025-12：{base} {sku_name}在{day_text}库存{end_qty_wan:.2f}万吨，安全线{safety_wan:.2f}万吨，偏差{abs(end_qty_wan - safety_wan):.2f}万吨。"
        plan = f"{summary} 推荐动作：{action_type}，建议处置规模约{qty_ton}吨。"
        impact = f"预计净利改善约{est_net_gain:.1f}万，同时优化履约稳定性与库存周转。"
        return {
            "risk": risk_text,
            "root_cause": root_cause,
            "plan": plan,
            "impact": impact,
            "suggestion": {
                "summary": summary,
                "action_type": action_type,
                "action_qty_ton": qty_ton,
                "est_net_gain": est_net_gain,
            },
            "meta": {
                "month": "2025-12",
                "base": base,
                "sku_name": sku_name,
            },
        }

    async def build_ai_analysis(self, db: Session, alert_id: str):
        simulated = self._build_ai_analysis_simulated(db, alert_id)
        if not simulated:
            return None
        config = llm_service.get_config(masked=False)
        channel = str(config.get("analysis_channel", "auto") or "auto").strip()
        should_use_agent = channel == "agent" or (channel == "auto" and bool(config.get("has_api_key")))
        if not should_use_agent:
            return simulated
        try:
            prompt = (
                "请基于输入数据输出JSON，不要输出其他文字。字段必须包含："
                "risk,root_cause,plan,impact,suggestion(meta保持不变)。"
                "其中 suggestion 必须包含 summary,action_type,action_qty_ton,est_net_gain。"
            )
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(simulated)},
            ]
            raw = await llm_service.chat_completion(messages, temperature=0.2)
            text = str(raw or "").strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            import json
            parsed = json.loads(text)
            for key in ["risk", "root_cause", "plan", "impact", "suggestion"]:
                if key not in parsed:
                    return simulated
            parsed["meta"] = simulated.get("meta", {})
            return parsed
        except Exception:
            return simulated

    def update_recommendation_decision(self, db: Session, recommendation_id: str, payload: dict):
        row = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id).first()
        if not row:
            return None
        if "decision_status" in payload and payload["decision_status"]:
            row.decision_status = payload["decision_status"]
        if "decision_reason" in payload and payload["decision_reason"] is not None:
            row.decision_reason = payload["decision_reason"]
        if "decision_user" in payload and payload["decision_user"] is not None:
            row.decision_user = payload["decision_user"]
        row.decision_time = payload.get("decision_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.commit()
        db.refresh(row)
        return row

    def list_executions(self, db: Session, recommendation_id: str = "", limit: int = 100):
        q = db.query(ExecutionLight)
        if recommendation_id:
            q = q.filter(ExecutionLight.recommendation_id == recommendation_id)
        return q.order_by(ExecutionLight.updated_at.desc()).limit(limit).all()

    def create_execution(self, db: Session, payload: dict):
        row = ExecutionLight(
            execution_id=payload.get("execution_id") or _new_id("EXE"),
            recommendation_id=payload.get("recommendation_id") or "",
            status=payload.get("status") or "待确认",
            owner=payload.get("owner") or "",
            plan_qty_ton=payload.get("plan_qty_ton") or 0,
            actual_qty_ton=payload.get("actual_qty_ton") or 0,
            due_date=payload.get("due_date") or "",
            note=payload.get("note") or "",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update_execution(self, db: Session, execution_id: str, payload: dict):
        row = db.query(ExecutionLight).filter(ExecutionLight.execution_id == execution_id).first()
        if not row:
            return None
        for key in ["status", "owner", "plan_qty_ton", "actual_qty_ton", "due_date", "note"]:
            if key in payload and payload[key] is not None:
                setattr(row, key, payload[key])
        db.commit()
        db.refresh(row)
        return row


decision_flow_service = DecisionFlowService()
