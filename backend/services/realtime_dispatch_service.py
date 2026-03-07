from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.december_report_service import december_report_service
from services.lp_optimizer import (
    DEFAULT_CAPACITY,
    DEFAULT_PROD_COST,
    DEFAULT_TRANSPORT_COST,
    BAG_TRANSPORT_PREMIUM,
)


class RealtimeDispatchService:
    def __init__(self) -> None:
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.recommendations: Dict[str, Dict[str, Any]] = {}
        self.base_alias = {
            "福建安砂建福水泥有限公司": "安砂建福",
            "福建永安建福水泥有限公司": "永安建福",
            "福建顺昌炼石水泥有限公司": "顺昌炼石",
            "福州炼石水泥有限公司": "福州炼石",
            "福建省永安金银湖水泥有限公司": "金银湖水泥",
            "福建安砂建福水泥有限公司德化分公司": "德化分公司",
            "金银湖": "金银湖水泥",
            "安砂建福德化分公司": "德化分公司",
        }
        self.base_to_lp = {
            "安砂建福": "安砂建福",
            "永安建福": "永安建福",
            "顺昌炼石": "顺昌炼石",
            "福州炼石": "福州炼石",
            "金银湖水泥": "金银湖",
            "德化分公司": "德化分公司",
            "宁德建福": "福州炼石",
        }

    def _norm_base(self, base: str) -> str:
        return self.base_alias.get(base, base)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _inventory_map(self) -> Dict[str, float]:
        parsed = december_report_service._parse_daily_data()
        inv = parsed.get("inventory", {})
        out: Dict[str, float] = {}
        for k, v in inv.items():
            base = self._norm_base(k)
            cement = v.get("cement_inventory", [])
            last = float(cement[-1]) if cement else 0.0
            out[base] = last
        return out

    def _capacity_map(self) -> Dict[str, float]:
        parsed = december_report_service._parse_daily_data().get("production", {}).get(31, {})
        cap: Dict[str, float] = {}
        for base, row in parsed.items():
            name = self._norm_base(base)
            lp_key = self.base_to_lp.get(name)
            if lp_key and lp_key in DEFAULT_CAPACITY:
                cap[name] = (DEFAULT_CAPACITY[lp_key]["散装"] + DEFAULT_CAPACITY[lp_key]["袋装"]) * 10000
            else:
                cap[name] = float(row.get("plan_qty", 0.0))
        return cap

    def _prod_cost(self, base: str, product: str) -> float:
        lp_key = self.base_to_lp.get(base, base)
        if lp_key in DEFAULT_PROD_COST:
            key = "袋装" if product == "袋装" else "散装"
            return float(DEFAULT_PROD_COST[lp_key][key])
        return 300.0

    def _transport_cost(self, base: str, region: str) -> float:
        lp_key = self.base_to_lp.get(base, base)
        return float(DEFAULT_TRANSPORT_COST.get(lp_key, {}).get(region, 60.0))

    def _base_state(self) -> List[Dict[str, Any]]:
        inv = self._inventory_map()
        cap = self._capacity_map()
        rows = []
        for base in sorted(set(list(inv.keys()) + list(cap.keys()))):
            rows.append(
                {
                    "base": base,
                    "inventory_ton": round(float(inv.get(base, 0.0)), 2),
                    "capacity_ton": round(float(cap.get(base, 0.0)), 2),
                }
            )
        return rows

    def ingest_orders(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        accepted = 0
        invalid = 0
        ids: List[str] = []
        for row in rows:
            region = str(row.get("region", "")).strip()
            product = str(row.get("product", "散装")).strip() or "散装"
            qty = float(row.get("qty_ton", 0) or 0)
            if not region or qty <= 0:
                invalid += 1
                continue
            order_id = str(row.get("order_id", "")).strip() or f"ODR-{uuid4().hex[:8].upper()}"
            payload = {
                "order_id": order_id,
                "region": region,
                "product": "袋装" if product == "袋装" else "散装",
                "qty_ton": round(qty, 3),
                "priority": int(row.get("priority", 2) or 2),
                "due_time": str(row.get("due_time", "")),
                "source": str(row.get("source", "manual")),
                "status": "NEW",
                "created_at": self._now(),
            }
            self.orders[order_id] = payload
            ids.append(order_id)
            accepted += 1
        return {
            "batch_id": f"BATCH-{uuid4().hex[:10].upper()}",
            "accepted": accepted,
            "invalid": invalid,
            "order_ids": ids,
        }

    def get_snapshot(self) -> Dict[str, Any]:
        orders = sorted(self.orders.values(), key=lambda x: (x["status"], x["order_id"]))
        recs = sorted(self.recommendations.values(), key=lambda x: x["created_at"], reverse=True)
        return {
            "base_state": self._base_state(),
            "order_pool": orders,
            "recommendation_pool": recs,
            "metrics": {
                "pending_orders": len([o for o in orders if o["status"] == "NEW"]),
                "recommended_orders": len([o for o in orders if o["status"] == "RECOMMENDED"]),
                "confirmed_orders": len([o for o in orders if o["status"] == "CONFIRMED"]),
            },
        }

    def recommend(self, order_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        candidates = [o for o in self.orders.values() if o["status"] == "NEW"]
        if order_ids:
            allow = set(order_ids)
            candidates = [o for o in candidates if o["order_id"] in allow]
        candidates = sorted(candidates, key=lambda x: (x["priority"], x["order_id"]))

        base_state = self._base_state()
        available = {b["base"]: float(b["inventory_ton"] + b["capacity_ton"]) for b in base_state}
        items: List[Dict[str, Any]] = []
        unassigned: List[Dict[str, Any]] = []
        total_cost = 0.0
        touched_orders: List[str] = []

        for order in candidates:
            remain = float(order["qty_ton"])
            region = order["region"]
            product = order["product"]
            base_costs = []
            for base in available.keys():
                unit = self._prod_cost(base, product) + self._transport_cost(base, region)
                if product == "袋装":
                    unit += BAG_TRANSPORT_PREMIUM
                base_costs.append((base, unit))
            base_costs.sort(key=lambda x: x[1])
            for base, unit_cost in base_costs:
                if remain <= 0:
                    break
                can = max(0.0, available.get(base, 0.0))
                if can <= 0:
                    continue
                assign = min(can, remain)
                available[base] = can - assign
                remain -= assign
                cost = assign * unit_cost
                total_cost += cost
                items.append(
                    {
                        "order_id": order["order_id"],
                        "base": base,
                        "region": region,
                        "product": product,
                        "assigned_ton": round(assign, 3),
                        "unit_cost": round(unit_cost, 2),
                        "estimated_cost": round(cost, 2),
                    }
                )
            assigned = round(order["qty_ton"] - remain, 3)
            if assigned > 0:
                touched_orders.append(order["order_id"])
            if remain > 0:
                unassigned.append(
                    {
                        "order_id": order["order_id"],
                        "unassigned_ton": round(remain, 3),
                        "reason": "可用库存+产能不足",
                    }
                )

        rec_id = f"REC-{uuid4().hex[:10].upper()}"
        recommendation = {
            "recommendation_id": rec_id,
            "status": "RECOMMENDED",
            "created_at": self._now(),
            "order_count": len(candidates),
            "assigned_order_count": len(set([i["order_id"] for i in items])),
            "total_assigned_ton": round(sum(i["assigned_ton"] for i in items), 3),
            "total_estimated_cost": round(total_cost, 2),
            "items": items,
            "unassigned": unassigned,
        }
        self.recommendations[rec_id] = recommendation
        for oid in touched_orders:
            if oid in self.orders:
                self.orders[oid]["status"] = "RECOMMENDED"
                self.orders[oid]["last_recommendation_id"] = rec_id
        return recommendation

    def update_recommendation(self, recommendation_id: str, status: str, operator: str, reason: str = "") -> Dict[str, Any]:
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            raise ValueError("recommendation_not_found")
        rec["status"] = status
        rec["updated_at"] = self._now()
        rec["operator"] = operator
        if reason:
            rec["reason"] = reason
        affected = set([i["order_id"] for i in rec.get("items", [])])
        for oid in affected:
            if oid in self.orders:
                self.orders[oid]["status"] = "CONFIRMED" if status == "CONFIRMED" else "REJECTED"
        return rec


realtime_dispatch_service = RealtimeDispatchService()
