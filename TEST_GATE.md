
# 自动化测试门禁 (Automated Test Gate)

为了保障版本质量与上线稳定性，本项目建立了自动化测试门禁机制。所有代码提交及版本发布前必须通过此门禁。

## 门禁规则 (Gate Rules)

1.  **后端冒烟测试 (Backend Smoke Tests)**:
    *   覆盖关键 API 接口（Dashboard, Production, Sales 等）。
    *   确保所有 GET 请求返回 200 OK。
    *   确保返回的数据结构符合预期。
    *   运行命令: `python -m pytest tests/test_smoke.py` (在 `backend` 目录下)

2.  **前端关键路径回归 (Frontend Key Path Regression)**:
    *   覆盖所有一级导航菜单页面（Dashboard, Production Query, Inventory, Sales, etc.）。
    *   确保页面能够正常加载且 URL 正确跳转。
    *   使用 Playwright 进行端到端测试。
    *   运行命令: `npm run test:e2e` (在 `frontend` 目录下)

## 如何运行门禁 (How to Run)

在项目根目录下运行以下脚本：

```bash
python scripts/gate.py
```

该脚本将依次执行后端和前端测试。如果任何一项测试失败，脚本将以非零状态码退出，并输出错误信息。

## 前置条件 (Prerequisites)

1.  **后端环境**:
    *   安装 Python 3.10+
    *   安装依赖: `pip install -r backend/requirements.txt`

2.  **前端环境**:
    *   安装 Node.js 18+
    *   安装依赖: `cd frontend && npm install`
    *   安装 Playwright 浏览器: `npx playwright install`

## 测试清单 (Test Inventory)

### 后端 API 测试
- `/api/health`: 健康检查
- `/api/cockpit/kpi`: 驾驶舱 KPI 数据
- `/api/cockpit/production`: 驾驶舱生产数据
- `/api/cockpit/sales`: 驾驶舱销售数据

### 前端页面测试
- `Dashboard`: 态势感知页面
- `Production`: 生产查询页面
- `Inventory`: 库存监控页面
- `Sales`: 销售管理页面
- `SalesForecast`: 销售预测页面
- `Balance`: 产销平衡页面
- `DataManagement`: 数据管理页面
