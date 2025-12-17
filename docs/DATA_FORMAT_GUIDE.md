# 数据格式指南

## 排程文件格式说明

系统现在支持两种排程文件格式，**会自动检测并转换**，无需手动处理。

## 支持的格式

### 格式一：二维交叉表（推荐）

这是最直观的格式，行列交叉展示数据：

| SKU/DATE | 2025-11-23 | 2025-11-30 | 2025-12-07 | ... |
|----------|------------|------------|------------|-----|
| A1665011 | 100        | 200        | 300        | ... |
| A1665021 | 0          | 150        | 250        | ... |
| A1665061 | 300        | 400        | 0          | ... |

**特点：**
- ✅ 第一列：SKU 编号
- ✅ 第一行：日期（列标题）
- ✅ 单元格：对应SKU在该日期的排程数量
- ✅ 适合从 Excel 直接导出

**示例文件：** `data/input/shechle.xlsx`

### 格式二：长表格式

这是系统内部使用的格式，每行代表一条记录：

| 日期       | SKU      | 计划产量 |
|-----------|----------|---------|
| 2025-10-02 | A1665011 | 100     |
| 2025-10-09 | A1665011 | 0       |
| 2025-10-16 | A1665011 | 0       |
| 2025-10-23 | A1665011 | 400     |

**特点：**
- ✅ 列1：日期
- ✅ 列2：SKU 编号
- ✅ 列3：计划产量
- ✅ 适合数据库导出

**示例文件：** `data/input/shechle_aim.xlsx`

## 自动转换功能

### 🔄 工作流程

1. **上传文件**
   - 用户上传排程文件（任意格式）

2. **自动检测**
   - 系统自动识别文件格式
   - 检测依据：列名、数据类型、结构

3. **智能转换**
   - 交叉表 → 自动转换为长表
   - 长表 → 标准化列名
   - 添加 week_num 列

4. **无缝使用**
   - 转换后的文件自动保存
   - 后续优化直接使用转换结果

### ✨ 转换特性

#### 交叉表转换
```
输入: 20行 × 15列 (交叉表)
输出: 280行 × 4列 (长表)

新增列:
- 日期: 从列标题提取
- SKU: 从行标题提取
- 计划产量: 从单元格提取
- week_num: 自动计算的周编号
```

#### 列名标准化
```
自动识别并标准化列名:
- "date" / "日期" / "时间" → 日期
- "sku" / "产品" / "物料" → SKU
- "quantity" / "数量" / "计划产量" → 计划产量
```

#### 周编号生成
```
格式: YYYYWW
示例:
- 2025-11-23 → 202547 (2025年第47周)
- 2025-12-01 → 202548 (2025年第48周)
```

## 前端提示

### 上传成功提示

**交叉表格式：**
```
✅ 文件上传成功！已自动转换交叉表格式
```

**长表格式：**
```
✅ 文件上传成功！
```

### 数据预览

上传后会显示转换信息：

```
📊 数据概览
行数: 280  SKU数: 20
列: 日期, SKU, 计划产量, week_num

🔄 已自动转换交叉表格式为长表格式
```

## 文件准备建议

### ✅ 推荐做法

1. **使用交叉表格式**
   - 直接从 Excel 导出
   - 行 = SKU，列 = 日期
   - 最直观，易于理解

2. **日期格式**
   - 使用标准日期格式
   - 建议：YYYY-MM-DD
   - Excel 日期类型会自动识别

3. **数据完整性**
   - 确保所有SKU都有数据
   - 缺失值用 0 填充
   - 不要有合并单元格

### ❌ 避免的问题

1. **格式混乱**
   - 不要在同一文件混用两种格式
   - 不要有多余的标题行

2. **列名问题**
   - 第一列不要留空
   - 日期列不要用文本格式

3. **数据问题**
   - 避免非数字的计划产量
   - 不要有重复的日期列

## 命令行工具

### 独立转换工具

如需单独转换文件，可使用命令行工具：

```bash
# 转换交叉表为长表
python src/core/data_transformer.py data/input/shechle.xlsx data/output/converted.xlsx

# 只检测格式（不转换）
python3 << 'EOF'
from src.core.data_transformer import ScheduleTransformer
import pandas as pd

df = pd.read_excel('your_file.xlsx')
transformer = ScheduleTransformer()
format_type = transformer.detect_format(df)
print(f"文件格式: {format_type}")
EOF
```

## API 接口

### 上传接口

**URL:** `POST /api/upload`

**Request:**
```
FormData:
- schedule_aim: 排程文件（任意格式）
- po_lists: PO清单文件
```

**Response:**
```json
{
  "success": true,
  "message": "文件上传成功",
  "data": {
    "schedule_aim": {
      "filename": "shechle.xlsx",
      "rows": 280,
      "columns": ["日期", "SKU", "计划产量", "week_num"],
      "skus": ["A1665011", "A1665021", ...]
    },
    "conversion": {
      "format": "cross_table",
      "converted": true,
      "message": "已自动转换交叉表格式为长表格式"
    }
  }
}
```

## 常见问题

### Q: 我的文件是哪种格式？
A: 无需担心！系统会自动检测。上传后查看提示信息即可。

### Q: 转换会改变我的原始文件吗？
A: 不会。原始文件保持不变，转换后的文件单独保存。

### Q: 为什么要转换成长表？
A: 长表格式更适合数据处理和优化算法，也更节省存储空间。

### Q: 转换后数据会丢失吗？
A: 不会。所有数据都完整保留，包括数量为 0 的记录。

### Q: 如何确认转换正确？
A: 上传后查看数据预览，确认行数、SKU数是否符合预期。

### Q: 系统无法识别我的格式怎么办？
A: 请参考上面的格式说明，调整文件结构，或联系技术支持。

## 技术实现

### 格式检测逻辑

```python
def detect_format(df):
    # 检测长表特征
    if has_date_column and has_sku_column and has_quantity_column:
        return 'long_format'

    # 检测交叉表特征
    if first_column_is_sku and most_columns_are_dates:
        return 'cross_table'

    return 'unknown'
```

### 转换算法

```python
def transform_cross_table_to_long(df):
    # 1. 提取SKU列（第一列）
    skus = df[sku_col_name].values

    # 2. 提取日期列（其他列）
    dates = df.columns[1:]

    # 3. 遍历生成长表记录
    for sku in skus:
        for date in dates:
            quantity = df.loc[sku, date]
            append_record(date, sku, quantity)

    # 4. 添加周编号
    add_week_number(result_df)

    return result_df
```

## 更新日志

### v1.1.0 (2025-12-17)
- ✨ 新增自动格式检测功能
- ✨ 新增交叉表转长表转换
- ✨ 新增列名标准化
- ✨ 新增周编号自动计算
- 🎨 前端显示转换状态
- 📚 新增数据格式指南

---

**提示：** 如有其他问题或建议，请参考主文档或提交 Issue。
