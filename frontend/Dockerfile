# 构建阶段
FROM node:20-slim AS build-stage

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装 (利用缓存)
COPY package*.json ./
RUN npm install

# 复制前端代码并构建
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine AS production-stage

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制静态文件
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露非标准端口
EXPOSE 18080

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
