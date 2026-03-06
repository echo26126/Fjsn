# 数据平台设计报告：模型设计与 ETL 映射

**生成时间**: 2026-03-04
**负责 Agent**: Data Platform Agent
**关联任务**: 生产环境创建-数据平台任务书

## 1. 概述

本报告详细定义了能化水泥生产数据平台的 Doris 数仓模型、MySQL 业务模型、统一数据字典以及 Excel 入湖入仓的 ETL 映射规则。旨在为上层产销看板、查询报表与优化模型提供标准、可信的数据支撑。

## 2. 数据字典 (Data Dictionary)

### 2.1 维度定义

| 维度名称 | 代码 | 描述 | 示例值 |
|---|---|---|---|
| **组织机构** | `dim_org` | 公司、基地、车间、产线层级 | 福建水泥(公司) -> 安砂建福(基地) -> 熟料车间 -> 回转窑1(产线) |
| **物料/产品** | `dim_material` | 生产与销售的物料，区分品种、标号、包装 | 熟料、P.O42.5散装水泥、M32.5袋装水泥 |
| **时间** | `dim_time` | 日历维度，包含年、月、日、节假日标识 | 2025-12-01, 2025年12月 |
| **客户/区域** | `dim_customer` | 销售区域或客户 | 福州大区、厦门大区 |

### 2.2 核心指标

| 指标名称 | 代码 | 单位 | 计算逻辑/来源 |
|---|---|---|---|
| **日产量** | `qty_prod_daily` | 吨 | 生产日报表“日生产/进厂”列 |
| **日销量** | `qty_sales_daily` | 吨 | 生产日报表“日消耗/出厂”列 (水泥为出厂，熟料需区分自用/外售) |
| **期末库存** | `qty_inv_end` | 吨 | 生产日报表“期末库存”列 |
| **库容比** | `ratio_inv_capacity` | % | 期末库存 / 库容上限 * 100% |
| **设备运转率** | `rate_device_run` | % | 实际运行时间 / 24小时 * 100% (或日历时间) |
| **台时产量** | `qty_device_hourly` | 吨/小时 | 日产量 / 实际运行时间 |
| **熟料消耗** | `qty_clinker_consume` | 吨 | 水泥生产消耗的熟料量 |

## 3. Doris 数仓模型设计 (DDL)

采用 Star Schema 设计，分为维度表 (DIM) 和 事实表 (FACT/DWD/DWS)。

### 3.1 维度表 (DIM)

```sql
-- 组织机构维度
CREATE TABLE `dim_org` (
    `org_id` VARCHAR(50) NOT NULL COMMENT '机构ID',
    `org_name` VARCHAR(100) NOT NULL COMMENT '机构名称',
    `org_type` VARCHAR(20) NOT NULL COMMENT '类型: COMPANY, BASE, WORKSHOP, LINE',
    `parent_id` VARCHAR(50) COMMENT '父级ID',
    `base_name` VARCHAR(50) COMMENT '所属基地名称 (冗余查询)',
    `sort_order` INT DEFAULT '0'
) UNIQUE KEY(`org_id`)
DISTRIBUTED BY HASH(`org_id`) BUCKETS 1
PROPERTIES("replication_num" = "1");

-- 物料维度
CREATE TABLE `dim_material` (
    `material_id` VARCHAR(50) NOT NULL COMMENT '物料ID',
    `material_name` VARCHAR(100) NOT NULL COMMENT '物料名称',
    `category` VARCHAR(20) NOT NULL COMMENT '分类: CLINKER(熟料), CEMENT(水泥)',
    `spec` VARCHAR(50) COMMENT '规格: P.O42.5, M32.5 等',
    `package_type` VARCHAR(20) COMMENT '包装: BULK(散装), BAG(袋装)',
    `unit` VARCHAR(10) DEFAULT '吨'
) UNIQUE KEY(`material_id`)
DISTRIBUTED BY HASH(`material_id`) BUCKETS 1
PROPERTIES("replication_num" = "1");
```

### 3.2 明细事实表 (DWD)

```sql
-- 生产日报明细表 (日粒度)
CREATE TABLE `dwd_production_daily` (
    `date` DATE NOT NULL COMMENT '日期',
    `org_id` VARCHAR(50) NOT NULL COMMENT '产线ID/基地ID',
    `material_id` VARCHAR(50) NOT NULL COMMENT '物料ID',
    `qty_produced` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '生产数量(吨)',
    `qty_consumed` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '消耗数量(如熟料消耗)',
    `device_run_hours` DECIMAL(10, 2) SUM DEFAULT '0' COMMENT '设备运行小时数',
    `electricity_consume` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '用电量(度)'
) AGGREGATE KEY(`date`, `org_id`, `material_id`)
PARTITION BY RANGE(`date`) ()
DISTRIBUTED BY HASH(`org_id`) BUCKETS 10
PROPERTIES("replication_num" = "1");

-- 销售日报明细表 (日粒度)
CREATE TABLE `dwd_sales_daily` (
    `date` DATE NOT NULL COMMENT '日期',
    `org_id` VARCHAR(50) NOT NULL COMMENT '销售组织/基地ID',
    `customer_region` VARCHAR(50) NOT NULL COMMENT '销售区域',
    `material_id` VARCHAR(50) NOT NULL COMMENT '物料ID',
    `qty_sold` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '销售数量(吨)',
    `amount_sold` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '销售金额(元)'
) AGGREGATE KEY(`date`, `org_id`, `customer_region`, `material_id`)
PARTITION BY RANGE(`date`) ()
DISTRIBUTED BY HASH(`org_id`) BUCKETS 10
PROPERTIES("replication_num" = "1");

-- 库存日报快照表 (日粒度，保留每日快照)
CREATE TABLE `dwd_inventory_daily` (
    `date` DATE NOT NULL COMMENT '日期',
    `org_id` VARCHAR(50) NOT NULL COMMENT '基地ID',
    `material_id` VARCHAR(50) NOT NULL COMMENT '物料ID',
    `qty_inventory` DECIMAL(20, 4) REPLACE COMMENT '期末库存(吨)',
    `capacity_max` DECIMAL(20, 4) REPLACE COMMENT '库容上限(吨)',
    `ratio_usage` DECIMAL(10, 4) REPLACE COMMENT '库容利用率'
) DUPLICATE KEY(`date`, `org_id`, `material_id`)
PARTITION BY RANGE(`date`) ()
DISTRIBUTED BY HASH(`org_id`) BUCKETS 10
PROPERTIES("replication_num" = "1");
```

### 3.3 汇总表 (DWS) - 供看板快速查询

```sql
-- 月度产销存汇总表
CREATE TABLE `dws_production_sales_monthly` (
    `month` VARCHAR(7) NOT NULL COMMENT '月份 YYYY-MM',
    `org_id` VARCHAR(50) NOT NULL COMMENT '基地ID',
    `material_category` VARCHAR(20) NOT NULL COMMENT '物料分类(水泥/熟料)',
    `qty_prod_plan` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '计划产量',
    `qty_prod_actual` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '实际产量',
    `qty_sales_plan` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '计划销量',
    `qty_sales_actual` DECIMAL(20, 4) SUM DEFAULT '0' COMMENT '实际销量',
    `qty_inv_end` DECIMAL(20, 4) MAX DEFAULT '0' COMMENT '月末库存'
) AGGREGATE KEY(`month`, `org_id`, `material_category`)
DISTRIBUTED BY HASH(`org_id`) BUCKETS 5
PROPERTIES("replication_num" = "1");
```

## 4. MySQL 业务模型设计 (DDL)

用于管理数据上传、审核与日志。

```sql
-- 数据上传记录表
CREATE TABLE `sys_upload_record` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `batch_id` VARCHAR(50) NOT NULL COMMENT '批次ID',
    `template_type` VARCHAR(50) NOT NULL COMMENT '模板类型: production_daily, plan_monthly',
    `file_name` VARCHAR(200) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `upload_user` VARCHAR(50) NOT NULL,
    `upload_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `status` VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING, AUDITED, REJECTED, PROCESSED',
    `audit_user` VARCHAR(50),
    `audit_time` DATETIME,
    `audit_comment` VARCHAR(200),
    `process_log` TEXT COMMENT 'ETL处理日志'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 基础映射配置表 (用于名称归一化)
CREATE TABLE `sys_dict_mapping` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category` VARCHAR(50) NOT NULL COMMENT '类别: ORG, MATERIAL',
    `source_name` VARCHAR(100) NOT NULL COMMENT 'Excel中的名称',
    `target_code` VARCHAR(50) NOT NULL COMMENT '系统中的标准代码',
    `target_name` VARCHAR(100) NOT NULL COMMENT '系统中的标准名称'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 5. ETL 映射规则 (Source -> Target)

### 5.1 生产日报表 Excel 映射

**源文件**: `生产日报表.xlsx` (Sheet `1` ~ `31`)

| 目标表 | 目标字段 | 源 Sheet 位置 | 源字段/逻辑 | 备注 |
|---|---|---|---|---|
| `dwd_production_daily` | `date` | Sheet名称 (1-31) | 结合文件名年月 + Sheet名 | 如 2025-12-01 |
| `dwd_production_daily` | `org_id` | Col A (第5行起) | 基地名称 (如"安砂建福") | 需映射为 ID |
| `dwd_production_daily` | `material_id` | Col C (第6行起) | 品种 (如 "P.O52.5", "M32.5") | 需映射为 ID |
| `dwd_production_daily` | `qty_produced` | Col G | "日生产/进厂" - "日" | 熟料/水泥产量 |
| `dwd_sales_daily` | `qty_sold` | Col J | "日消耗/出厂" - "日" | 水泥为销量, 熟料为消耗 |
| `dwd_inventory_daily` | `qty_inventory` | Col M | "期末库存" | |
| `dwd_inventory_daily` | `ratio_usage` | Col N | "库容率%" | |
| `dwd_production_daily` | `device_run_hours` | Col X/Y | "运行时间(h)" - "日" | 对应产线行 |
| `dwd_production_daily` | `qty_device_hourly` | Col R | "台时产量" | 对应产线行 |

### 5.2 名称归一化映射 (示例)

**组织机构**:
- "安砂" / "安砂建福" -> `ORG_BASE_ANSHA`
- "永安" / "永安建福" -> `ORG_BASE_YONGAN`
- "回转窑1" (安砂下) -> `ORG_LINE_ANSHA_KILN_1`

**物料**:
- "P.O52.5" -> `MAT_CEM_PO525_BULK` (默认散装，需结合其他信息判断)
- "M32.5" -> `MAT_CEM_M325_BULK`
- "M32.5袋" -> `MAT_CEM_M325_BAG` (需根据包装列或名称区分)

## 6. 后续行动计划

1.  **Doris 建表**: 在生产环境执行上述 Doris DDL。
2.  **MySQL 建表**: 在业务库执行 MySQL DDL。
3.  **开发解析脚本**: 编写 Python 脚本 (`backend/utils/excel_parser.py`) 实现上述 Excel 解析逻辑。
4.  **初始化字典**: 填充 `sys_dict_mapping` 表，覆盖所有历史 Excel 中出现的名称。
5.  **数据导入**: 运行脚本导入 2025 年历史数据。
