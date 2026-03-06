# 联调集成报告 (2026-03-04)

## 1. 联调验收清单

### 环境与基础设施
- [x] **后端服务启动**: FastAPI 服务运行于 8000 端口
- [x] **前端服务启动**: Vite 服务运行于 3000 端口
- [x] **接口代理配置**: 前端 `vite.config.ts` 正确代理 `/api` 至后端
- [x] **健康检查**: `/api/health` 响应正常

### 模块功能对接
#### 驾驶舱 (Dashboard)
- [x] **KPI 指标**: 对接 `/api/cockpit/kpi`，替换硬编码数据
- [x] **生产地图**: 对接 `/api/cockpit/production`，实现动态点位渲染
- [x] **销售地图**: 对接 `/api/cockpit/sales`，实现区域数据渲染
- [x] **数据映射**: 完成后端 `production`/`capacity` 到前端 `actual`/`plan` 的字段映射

#### 销售查询 (Sales Query)
- [x] **列表查询**: 对接 `/api/query/sales`，实现多维度查询
- [x] **图表联动**: 销售趋势图对接后端 `price_trend` 数据
- [x] **元数据映射**: 前端补全区域坐标与颜色配置

#### 生产查询 (Production Query)
- [x] **列表查询**: 对接 `/api/query/production`，支持按基地/品类筛选
- [x] **图表联动**: 计划vs实际、产能利用率图表基于 API 数据聚合生成

#### 库存查询 (Inventory Query)
- [x] **列表查询**: 对接 `/api/query/inventory`
- [x] **趋势图**: 对接后端 `trend` 数据
- [x] **水位图**: 基于 API 返回的 `capacity` 与 `current` 动态计算

---

## 2. 联调通过矩阵

| 模块 | 页面/组件 | 接口地址 | 方法 | 状态 | 说明 |
|---|---|---|---|---|---|
| **Dashboard** | KpiStrip | `/api/cockpit/kpi` | GET | ✅ Pass | 字段直接对应，展示无误 |
| **Dashboard** | MapChart (生产) | `/api/cockpit/production` | GET | ✅ Pass | 后端补充了 inventory 字段，前端完成了坐标映射 |
| **Dashboard** | MapChart (销售) | `/api/cockpit/sales` | GET | ✅ Pass | 前端维护了区域坐标字典 |
| **Sales** | Table/Charts | `/api/query/sales` | GET | ✅ Pass | 列表与趋势图数据一致 |
| **Production** | Table/Charts | `/api/query/production` | GET | ✅ Pass | 前端完成了数据聚合计算 |
| **Inventory** | WaterLevel/Table | `/api/query/inventory` | GET | ✅ Pass | 核心库存数据准确 |

---

## 3. 缺陷闭环列表

| ID | 缺陷描述 | 影响范围 | 优先级 | 状态 | 解决方案/规避措施 |
|---|---|---|---|---|---|
| **DEF-001** | 驾驶舱生产接口缺少库存数据 | 生产地图弹窗 | High | ✅ Fixed | 后端 `dashboard.py` 已增加 `inventory` 模拟字段 |
| **DEF-002** | 销售接口未返回地理坐标 | 销售地图渲染 | Medium | ⚠️ Accepted | 前端 `Dashboard.vue` 中维护 `REGION_COORDS` 静态字典进行映射 |
| **DEF-003** | 前后端基地名称定义不一致 | 全局数据展示 | High | ✅ Fixed | 前端移除硬编码名称，统一使用后端返回的规范名称（如“龙岩基地”） |
| **DEF-004** | 库存接口缺少出入库流量数据 | 库存页面图表 | Low | ⚠️ Accepted | 前端暂时使用模拟随机数据展示入库/出库对比，待后续接口升级 |
| **DEF-005** | 销售查询接口缺少地市与客户维度 | 销售明细表 | Low | ⚠️ Accepted | 前端根据区域名称进行简单Mock映射（如“福州区域”->“福州市”） |

---

## 4. 下一步计划

1. **接口规范化**: 推动后端在 `/sales` 接口中直接返回区域中心坐标，减少前端硬编码。
2. **数据真实性**: 替换后端 Mock 数据，对接真实数据库或数据仓库。
3. **鉴权对接**: 目前接口未开启鉴权，需在下一轮联调中加入 Token 验证。
