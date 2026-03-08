# 产销平衡系统 - Docker 部署指南

本项目采用前后端分离架构，通过 Docker 进行容器化封装。为了避免常用端口冲突，系统配置了非标准端口。

## 端口分配

- **前端服务 (Vue + Nginx)**: `32500` (基于水泥等级 32.5)
- **后端服务 (FastAPI)**: `42500` (基于水泥等级 42.5)

## 快速启动

在项目根目录下，使用 Docker Compose 一键启动：

```bash
docker-compose up -d --build
```

启动后可以通过以下地址访问：
- **前端页面**: [http://localhost:32500](http://localhost:32500)
- **后端 API 文档 (Swagger)**: [http://localhost:42500/docs](http://localhost:42500/docs)

## 容器架构

1.  **backend**: 基于 `python:3.10-slim`。
    - 运行 FastAPI 应用，监听 `42500` 端口。
    - 数据持久化：SQLite 数据库写入 `backend/data/sql_app.db`。
2.  **frontend**: 基于 `nginx:alpine` 的多阶段构建。
    - 静态文件托管在 Nginx。
    - 反向代理：Nginx 将 `/api` 请求转发至 `backend:42500`。

## 数据来源说明

- 系统优先读取 Excel 数据文件：`福建水泥2025年12月生产日报表.xlsx`、`12月销售数据.xls`、`12月销售订单数据.xls`。
- Docker 部署时可将上述文件放到 `backend/data-input/` 目录，容器会自动读取。
- 若未提供 Excel 文件，系统会自动使用内置演示数据，确保看板和地图不再空白。

## 常用命令

- **查看日志**: `docker-compose logs -f`
- **停止并移除容器**: `docker-compose down`
- **重启服务**: `docker-compose restart`
- **自定义宿主机端口**: 启动前设置 `FRONTEND_PORT` / `BACKEND_PORT`
