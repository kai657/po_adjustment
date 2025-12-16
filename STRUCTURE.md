# 项目目录结构说明

## 最终标准化目录结构

本项目采用标准的Python Web应用目录结构，符合业界最佳实践。

```
po_adjustment/
│
├── 📄 run.py                          # 主程序入口（推荐使用）
├── 📄 README.md                       # 项目说明（主文档）
├── 📄 STRUCTURE.md                    # 目录结构说明（本文档）
├── 📄 requirements.txt                # Python依赖包列表
├── 📄 .gitignore                      # Git忽略配置
│
├── 📁 templates/                      # HTML模板目录（根目录）
│   └── 📄 index.html                  # Web主页面
│
├── 📁 static/                         # 静态资源目录（根目录）
│   ├── 📁 css/                        # 样式表
│   │   └── 📄 style.css               # 主样式文件
│   └── 📁 js/                         # JavaScript脚本
│       └── 📄 app.js                  # 前端交互逻辑
│
├── 📁 src/                            # 源代码目录
│   ├── 📄 __init__.py                 # 包初始化文件
│   │
│   ├── 📁 core/                       # 核心算法模块
│   │   ├── 📄 __init__.py             # 模块初始化
│   │   ├── 📄 po_adjustment.py        # PO优化算法实现
│   │   └── 📄 visualization.py        # 可视化图表生成
│   │
│   └── 📁 web/                        # Web应用模块
│       ├── 📄 __init__.py             # 模块初始化
│       └── 📄 app.py                  # Flask应用主文件
│
├── 📁 data/                           # 数据目录
│   ├── 📁 input/                      # 输入数据
│   │   ├── 📄 shechle_aim.xlsx        # 排程目标文件（示例）
│   │   └── 📄 po_lists.xlsx           # PO清单文件（示例）
│   │
│   ├── 📁 output/                     # 输出结果（自动生成）
│   │   ├── 📄 po_lists_optimized.xlsx # 优化后的PO清单
│   │   ├── 📄 comparison_report.xlsx  # 详细对比报告
│   │   ├── 📄 po_comparison.png       # 数量对比图
│   │   └── 📄 deviation_comparison.png# 偏差对比图
│   │
│   └── 📁 uploads/                    # Web上传临时目录（自动生成）
│       └── 📄 .gitkeep                # 保留空目录
│
├── 📁 scripts/                        # 脚本工具目录
│   ├── 📄 start_web.sh                # Web应用启动脚本
│   └── 📄 run_optimization.py         # 命令行优化脚本（兼容旧版）
│
├── 📁 docs/                           # 文档目录
│   ├── 📄 README.md                   # 完整技术文档
│   ├── 📄 QUICKSTART.md               # 快速开始指南
│   ├── 📄 WEB_GUIDE.md                # Web界面使用指南
│   ├── 📄 PROJECT_OVERVIEW.md         # 项目总览和架构
│   ├── 📄 DEMO.md                     # 演示脚本和指南
│   └── 📄 FILE_LIST.txt               # 文件清单
│
└── 📁 tests/                          # 测试目录（预留）
    └── 📄 .gitkeep                    # 保留空目录
```

## 重要说明

### templates/ 和 static/ 为何在根目录？

**原因：满足部署平台要求**

许多Web部署平台（如本系统）要求：
- ✅ `index.html` 必须在根目录或一级子文件夹
- ✅ 静态资源需要在根目录便于访问
- ✅ 符合Flask默认约定

**设计选择：**
1. `templates/` - 根目录，Flask默认查找位置
2. `static/` - 根目录，Web服务器直接访问
3. `src/web/app.py` - 通过配置指向根目录的templates和static

这种结构兼顾了：
- ✅ 部署平台要求
- ✅ Flask最佳实践
- ✅ 代码组织清晰
- ✅ 易于维护

## 目录说明

### 1. 根目录文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `run.py` | 主程序入口 | 统一的命令行接口，支持CLI和Web两种模式 |
| `README.md` | 项目说明 | 项目概述、快速开始、使用说明 |
| `STRUCTURE.md` | 结构说明 | 本文档，详细的目录结构说明 |
| `requirements.txt` | 依赖列表 | Python包依赖声明 |
| `.gitignore` | Git忽略 | 指定不纳入版本控制的文件 |

### 2. templates/ - HTML模板（根目录）

**为何在根目录？**
- 满足部署平台要求（index.html必须在根目录或一级子目录）
- Flask默认查找位置
- 便于静态文件服务器访问

| 文件 | 说明 |
|------|------|
| `index.html` | Web主页面，四步骤向导式界面 |

### 3. static/ - 静态资源（根目录）

**为何在根目录？**
- Web服务器直接访问
- CDN部署友好
- 符合Web标准约定

| 子目录/文件 | 说明 |
|------------|------|
| `css/style.css` | 主样式表，现代化UI设计 |
| `js/app.js` | 前端交互逻辑，AJAX通信 |

### 4. src/ - 源代码目录

**核心原则**：业务逻辑代码在 `src/` 目录下。

#### 4.1 src/core/ - 核心算法模块

| 文件 | 说明 | 功能 |
|------|------|------|
| `po_adjustment.py` | 优化算法 | 分箱优化、约束验证、并行处理 |
| `visualization.py` | 可视化生成 | 对比图表、汇总报告 |

#### 4.2 src/web/ - Web应用模块

| 文件 | 说明 | 功能 |
|------|------|------|
| `app.py` | Flask应用 | REST API、文件上传、优化调度<br>**配置指向根目录的templates和static** |

### 5. data/ - 数据目录

| 子目录 | 说明 | 特点 |
|--------|------|------|
| `input/` | 输入数据 | 用户提供的原始数据文件 |
| `output/` | 输出结果 | 优化后的结果文件（自动生成） |
| `uploads/` | 上传临时 | Web上传的临时文件（自动清理） |

### 6. scripts/ - 脚本目录

| 文件 | 说明 | 用途 |
|------|------|------|
| `start_web.sh` | Web启动脚本 | 一键启动Web应用 |
| `run_optimization.py` | CLI脚本 | 兼容旧版的命令行接口 |

### 7. docs/ - 文档目录

| 文件 | 说明 | 受众 |
|------|------|------|
| `README.md` | 完整文档 | 开发者、高级用户 |
| `QUICKSTART.md` | 快速开始 | 新手用户 |
| `WEB_GUIDE.md` | Web指南 | Web界面用户 |
| `PROJECT_OVERVIEW.md` | 项目总览 | 技术人员、架构师 |
| `DEMO.md` | 演示指南 | 演示人员 |

## 设计原则

### 1. 关注点分离

- **src/core**: 纯算法逻辑，不依赖Web框架
- **src/web**: Web应用逻辑，调用core模块
- **templates/static**: Web界面资源
- **data**: 数据文件，独立于代码
- **docs**: 文档，独立维护

### 2. 部署友好

- `templates/` 和 `static/` 在根目录，满足平台要求
- Flask通过配置指向根目录
- 结构符合Web标准

### 3. 模块化设计

每个模块都有 `__init__.py`，可以作为独立包导入：

```python
from src.core import POOptimizer, POVisualizer
from src.web import app
```

### 4. 路径规范

- 所有路径使用相对于项目根目录的路径
- Flask配置明确指定template_folder和static_folder
- 使用 `os.path.join()` 构建跨平台路径

## Flask配置说明

在 `src/web/app.py` 中：

```python
# 使用根目录的templates和static
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

app = Flask(__name__,
            template_folder=os.path.join(PROJECT_ROOT, 'templates'),
            static_folder=os.path.join(PROJECT_ROOT, 'static'))
```

这样配置的好处：
- ✅ 满足部署平台要求
- ✅ index.html在根目录下一级
- ✅ 静态资源易于访问
- ✅ 代码逻辑仍然在src/中

## 使用指南

### 开发模式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行Web应用（开发模式）
python run.py web

# 运行CLI（开发模式）
python run.py cli -s data/input/schedule.xlsx -p data/input/po.xlsx
```

### 生产部署

```bash
# 使用生产级WSGI服务器
gunicorn -w 4 -b 0.0.0.0:5001 src.web.app:app
```

### 添加新功能

1. **新增核心功能**：在 `src/core/` 添加新模块
2. **新增Web接口**：在 `src/web/app.py` 添加路由
3. **新增页面**：在 `templates/` 添加HTML
4. **新增样式**：在 `static/css/` 添加CSS
5. **新增脚本**：在 `static/js/` 添加JS

## 常见问题

### Q: 为什么templates和static不在src/web下？

**A**:
1. **部署平台要求** - 许多平台要求index.html在根目录或一级子目录
2. **Web标准** - 静态资源通常在根目录，便于Web服务器直接访问
3. **Flask约定** - Flask默认在根目录查找templates和static
4. **灵活配置** - Flask支持通过参数指定位置，无需固定在app.py旁边

### Q: 如何部署到生产环境？

**A**:
```bash
# 方法1: 使用Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 src.web.app:app

# 方法2: 使用uWSGI
uwsgi --http :5001 --module src.web.app:app --processes 4

# 方法3: 使用Nginx + Gunicorn
# Nginx配置指向static目录，反向代理到Gunicorn
```

### Q: 可以改回src/web/templates吗？

**A**: 技术上可以，但：
- ❌ 不满足某些部署平台要求
- ❌ 需要修改部署配置
- ✅ 当前结构更标准、更灵活

### Q: 如何引用静态资源？

**A**: 在HTML中使用Flask模板语法：
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

## 技术栈

- **Python**: 3.7+
- **Web框架**: Flask
- **数据处理**: Pandas, NumPy
- **可视化**: Matplotlib
- **文件格式**: Excel (openpyxl)

## 更新日志

### v1.0.1 (2025-12-16)
- 🔧 调整templates和static到根目录
- 🔧 满足部署平台index.html路径要求
- 📝 更新文档反映新结构
- ✅ 测试通过

### v1.0.0 (2025-12-16)
- ✨ 重构为标准化目录结构
- ✨ 统一的主程序入口 (`run.py`)
- ✨ 模块化的代码组织
- ✨ 完善的文档体系

---

**项目维护**: 保持目录结构清晰，遵循设计原则，定期更新文档。
