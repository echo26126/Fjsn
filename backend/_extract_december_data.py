from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
files = sorted(ROOT.glob("*.xlsx"), key=lambda p: p.stat().st_size, reverse=True)
if not files:
    raise SystemExit("no_xlsx_found")

target = files[0]
print(f"file={target.name}")

base_names = [
    "安砂建福",
    "永安建福",
    "顺昌炼石",
    "福州炼石",
    "宁德建福",
    "金银湖水泥",
]

xls = pd.ExcelFile(target)
target_sheet = "月报"
if target_sheet not in xls.sheet_names:
    raise SystemExit("target_sheet_not_found")

df = pd.read_excel(target, sheet_name=target_sheet, header=None, dtype=str)
df = df.fillna("")
print("sheet=" + target_sheet)
preview = df.head(30).iloc[:, :20]
for idx, row in preview.iterrows():
    row_values = row.astype(str).tolist()
    print("p=" + str(idx) + "|" + "|".join(row_values))

base_rows = []
for idx, row in df.iterrows():
    row_values = row.astype(str).tolist()
    name = row_values[0]
    kind = row_values[1] if len(row_values) > 1 else ""
    if name == "公司合计" and kind == "水泥生产/出厂":
        base_rows.append(("公司合计", row_values))
    if name and name in base_names and kind == "水泥生产/出厂":
        base_rows.append((name, row_values))

for name, row_values in base_rows:
    plan = row_values[4] if len(row_values) > 4 else ""
    month_prod = row_values[7] if len(row_values) > 7 else ""
    month_sales = row_values[10] if len(row_values) > 10 else ""
    end_inventory = row_values[12] if len(row_values) > 12 else ""
    capacity_ratio = row_values[13] if len(row_values) > 13 else ""
    print("base=" + name + "|" + str(plan) + "|" + str(month_prod) + "|" + str(month_sales) + "|" + str(end_inventory) + "|" + str(capacity_ratio))
