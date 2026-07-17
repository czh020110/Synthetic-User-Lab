# 多阶段构建：Stage1 用 node 构建前端 dist，Stage2 用 Playwright 官方镜像跑后端（已预装浏览器二进制+系统库）

# ============================ Stage 1: 前端构建 ============================ #
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend

# 先拷依赖清单，利用 Docker 层缓存
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# 再拷源码构建（.dockerignore 已排除 node_modules/dist）
COPY frontend/ ./
RUN npm run build

# ============================ Stage 2: 后端运行时 ============================ #
# Playwright 官方镜像预装 Chromium 等浏览器二进制与系统依赖，免去 playwright install
# 镜像 tag 必须与 pyproject.toml 钉死的 playwright 版本一致（二进制路径按版本命名）
FROM mcr.microsoft.com/playwright:v1.60.0-jammy

# 用官方 uv 二进制镜像拷贝 uv，无需 pip（playwright 基础镜像未装 pip）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# 先拷依赖清单，利用层缓存；--no-dev 不装 pytest 等开发依赖（生产镜像）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 拷后端代码与前端构建产物
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./static

# 容器内专用配置：监听全网卡、前端产物路径；base_url/database_url 由 compose environment 注入
ENV SYNTHETIC_USER_LAB_HOST=0.0.0.0 \
    SYNTHETIC_USER_LAB_PORT=8000 \
    SYNTHETIC_USER_LAB_FRONTEND_DIR=/app/static

EXPOSE 8000

# uvicorn 跑后端，同时托管前端 SPA（main.py 已挂载 /static）
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
