#!/bin/bash
# PO优化系统Web应用启动脚本

echo "=========================================="
echo "   PO清单分箱优化系统 - Web应用"
echo "=========================================="
echo ""

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查依赖
echo "正在检查依赖..."
python3 -c "import flask, pandas, matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装缺失的依赖..."
    pip3 install -r requirements.txt
fi

# 创建必要的目录
mkdir -p data/uploads data/output

# 启动应用
echo ""
echo "正在启动Web应用..."
echo "访问地址: http://localhost:5001"
echo ""
python3 run.py web

echo ""
echo "应用已停止"
