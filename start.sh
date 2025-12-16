#!/bin/bash
# PO清单分箱优化系统 - 启动脚本

set -e

echo "================================"
echo "PO清单分箱优化系统启动中..."
echo "================================"

# 设置默认环境变量
export PYTHONUNBUFFERED=1
export PORT=${PORT:-5001}
export HOST=${HOST:-0.0.0.0}
export WORKERS=${WORKERS:-2}

# 创建必要的目录
echo "创建数据目录..."
mkdir -p data/output data/uploads

# 检查依赖
echo "检查 Python 环境..."
python --version

# 启动服务
echo "启动 Web 服务..."
echo "监听地址: ${HOST}:${PORT}"
echo "Worker 数量: ${WORKERS}"

# 使用 gunicorn 启动
exec gunicorn \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    src.web.app:app
