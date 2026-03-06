import pandas as pd
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        # In a real scenario, this would initialize DB connection pool
        self.mock_data = {
            "fact_production": pd.DataFrame({
                "base_name": ["龙岩基地", "三明基地", "南平基地", "泉州基地", "漳州基地"],
                "period": ["2026-02"] * 5,
                "actual_qty": [12.5, 10.8, 9.2, 8.6, 7.3],
                "plan_qty": [13.0, 11.0, 10.0, 9.0, 8.0]
            }),
            "fact_inventory": pd.DataFrame({
                "base_name": ["龙岩基地", "三明基地", "南平基地", "泉州基地", "漳州基地"],
                "inventory_qty": [5.8, 4.2, 3.1, 3.8, 2.6],
                "capacity": [7.5, 6.5, 5.0, 6.0, 5.5]
            })
        }
        
    def get_schema_info(self) -> str:
        """
        Return schema information for LLM context.
        """
        schema = """
        Table: fact_production
        Columns: base_name (TEXT), period (TEXT), actual_qty (FLOAT), plan_qty (FLOAT)
        Description: Production data by base and period.
        
        Table: fact_inventory
        Columns: base_name (TEXT), inventory_qty (FLOAT), capacity (FLOAT)
        Description: Inventory data by base.
        """
        return schema

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query.
        For now, this is a mock implementation that tries to interpret simple SQL or returns mock data.
        """
        logger.info(f"Executing SQL: {sql}")
        
        # Simple mock logic: check if table name is in SQL
        sql_lower = sql.lower()
        
        if "fact_production" in sql_lower:
            df = self.mock_data["fact_production"]
            # Basic filtering simulation could be added here, but for now return all or top N
            if "limit" in sql_lower:
                return df.head().to_dict(orient="records")
            return df.to_dict(orient="records")
            
        elif "fact_inventory" in sql_lower:
            df = self.mock_data["fact_inventory"]
            return df.to_dict(orient="records")
            
        return []

db_service = DBService()
