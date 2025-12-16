# PO清单分箱优化系统

> 智能化PO采购订单优化工具，基于分箱算法自动调整要货日期，最小化每周数量偏差

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方式

#### 方式一：Web界面（推荐）

```bash
# 使用启动脚本
./scripts/start_web.sh

# 或直接运行
python run.py web
```

然后访问：http://localhost:5001

#### 方式二：命令行

```bash
# 使用主程序（推荐）
python run.py cli \
  -s data/input/shechle_aim.xlsx \
  -p data/input/po_lists.xlsx \
  -o data/output

# 或使用脚本（兼容旧版）
python scripts/run_optimization.py
```

## 项目结构

```
po_adjustment/
├── run.py                      # 主程序入口（推荐使用）
├── requirements.txt            # Python依赖
├── .gitignore                  # Git忽略配置
│
├── templates/                  # HTML模板（Web界面）
│   └── index.html
│
├── static/                     # 静态资源（Web界面）
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── core/                   # 核心算法模块
│   │   ├── __init__.py
│   │   ├── po_adjustment.py    # 优化算法
│   │   └── visualization.py    # 可视化生成
│   └── web/                    # Web应用模块
│       ├── __init__.py
│       └── app.py              # Flask应用
│
├── data/                       # 数据目录
│   ├── input/                  # 输入文件
│   │   ├── shechle_aim.xlsx    # 排程目标
│   │   └── po_lists.xlsx       # PO清单
│   ├── output/                 # 输出结果（自动生成）
│   └── uploads/                # Web上传临时目录（自动生成）
│
├── scripts/                    # 脚本目录
│   ├── start_web.sh            # Web启动脚本
│   └── run_optimization.py     # 命令行脚本（兼容旧版）
│
├── docs/                       # 文档目录
│   ├── README.md               # 完整文档
│   ├── QUICKSTART.md           # 快速开始
│   ├── WEB_GUIDE.md            # Web使用指南
│   ├── PROJECT_OVERVIEW.md     # 项目总览
│   └── DEMO.md                 # 演示指南
│
└── tests/                      # 测试目录（预留）
    └── .gitkeep
```

## 核心功能

### 1. 智能优化算法
- 基于贪心策略的分箱算法
- 加权偏差最小化（优先保障前2个月）
- 考虑日期接近度的次要优化目标
- 按SKU并行处理

### 2. 多重约束条件
- ✅ 日期范围：2025-10-01 至 2026-06-01
- ✅ 周一约束：所有要货日期必须为周一
- ✅ 节假日约束：自动排除中国法定节假日
- ✅ 数量匹配：保持PO订单总量不变

### 3. 可视化分析
- 每周数量对比图
- 偏差改善对比图
- 详细Excel报告
- 汇总统计表

### 4. 双模式运行
- **Web界面**：图形化交互，适合日常使用
- **命令行**：批处理模式，适合自动化

## 命令行参数

### Web模式

```bash
python run.py web [OPTIONS]

选项:
  --host TEXT      监听地址 (默认: 0.0.0.0)
  --port INTEGER   监听端口 (默认: 5001)
  --no-debug       禁用调试模式
```

### CLI模式

```bash
python run.py cli [OPTIONS]

选项:
  -s, --schedule TEXT  排程目标文件路径 [必需]
  -p, --po TEXT        PO清单文件路径 [必需]
  -o, --output TEXT    输出目录 (默认: data/output)
```

## 输入文件格式

### 排程目标文件 (shechle_aim.xlsx)

| 列名 | 说明 | 示例 |
|------|------|------|
| 日期 | 周的日期 | 2025-10-02 |
| week_num | 周编号 | 202540 |
| SKU | 产品SKU | A1665011 |
| 计划产量 | 该周目标数量 | 100 |

### PO清单文件 (po_lists.xlsx)

| 列名 | 说明 | 示例 |
|------|------|------|
| SKU | 产品SKU | A16650B1 |
| 数量 | PO订单数量 | 1000 |
| 修改要货日期 | 原要货日期 | 2025-09-20 |
| week_num | 周编号 | 202538 |
| PO-PO行-发运行号 | PO标识 | PO2525SFSD010001-24-1 |

## 输出文件

优化完成后，在 `data/output/` 目录生成：

1. **po_lists_optimized.xlsx** - 优化后的PO清单（核心结果）
2. **comparison_report.xlsx** - 详细对比报告
   - Sheet1: 详细对比（按SKU+周）
   - Sheet2: 汇总统计
3. **po_comparison.png** - 每周数量对比图
4. **deviation_comparison.png** - 偏差改善对比图

## 开发指南

### 添加新功能

1. 核心算法：修改 `src/core/` 下的文件
2. Web界面：修改 `src/web/` 下的文件
3. 脚本工具：添加到 `scripts/` 目录

### 运行测试

```bash
# 预留功能
python -m pytest tests/
```

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 添加适当的文档字符串
- 保持模块化设计

## 依赖说明

### 核心依赖
- **pandas** >= 2.0.0 - 数据处理
- **numpy** >= 1.24.0 - 数值计算
- **matplotlib** >= 3.7.0 - 图表生成
- **openpyxl** >= 3.1.0 - Excel文件处理

### Web依赖
- **flask** >= 3.0.0 - Web框架
- **werkzeug** >= 3.0.0 - WSGI工具库

## 常见问题

### Q: 如何更改端口号？
```bash
python run.py web --port 8000
```

### Q: 输入文件在哪里？
放在 `data/input/` 目录下

### Q: 输出文件在哪里？
自动生成在 `data/output/` 目录

### Q: 如何批量处理多个文件？
编写Shell脚本调用命令行模式：
```bash
for file in data/input/*.xlsx; do
    python run.py cli -s "$file" -p po_lists.xlsx
done
```

## 文档

- 📘 [完整文档](docs/README.md) - 详细的技术文档
- 🚀 [快速开始](docs/QUICKSTART.md) - 新手指南
- 🌐 [Web指南](docs/WEB_GUIDE.md) - Web界面使用
- 📊 [项目总览](docs/PROJECT_OVERVIEW.md) - 架构设计
- 🎬 [演示指南](docs/DEMO.md) - 演示和展示

## 技术栈

- **后端**: Python 3.7+, Flask, Pandas, NumPy
- **前端**: HTML5, CSS3, JavaScript (Vanilla)
- **可视化**: Matplotlib
- **数据**: Excel (xlsx)

## 版本信息

- **版本**: 1.0.0
- **更新日期**: 2025-12-16
- **Python要求**: 3.7+

## 许可证

内部使用

## 贡献

欢迎提交Issue和Pull Request

## 更新日志

### v1.0.0 (2025-12-16)
- ✨ 初始版本发布
- ✨ 实现核心优化算法
- ✨ 提供Web界面和命令行两种模式
- ✨ 完整的可视化分析功能
- ✨ 标准化项目结构
- 📚 完整的文档体系

---

**感谢使用PO清单分箱优化系统！**

如有问题，请查看 [docs/](docs/) 目录下的详细文档。
