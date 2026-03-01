# 财务分析引擎

Python财务模型计算库，实现三表财务模型和DCF估值。

## 架构设计

### 核心模块

1. **three_statement.py** - 三表财务模型
   - 完整的IS/BS/CFS模型
   - FAST标准实现
   - 自动对账和验证

2. **dcf.py** - DCF估值模型
   - WACC计算
   - 自由现金流预测
   - 终端价值计算
   - 敏感性分析

3. **scenarios.py** - 场景管理
   - 基准、乐观、中性、悲观场景
   - 参数独立管理
   - 动态场景切换

4. **kpis.py** - KPI计算
   - 盈利能力KPI (ROE, ROA, ROIC等)
   - 效率KPI (周转率等)
   - 财务健康KPI (杠杆率等)

### 数据处理

1. **yahoo_finance.py** - 数据获取
   - 自动从Yahoo Finance获取历史财务数据
   - 财务报表、现金流、平衡表
   - 股票价格数据

2. **data_cleaner.py** - 数据清洗
   - 缺失值处理
   - 异常值检测
   - 数据标准化

## 模型设计原则

### 关注点分离
```
Input Layer      → Assumptions (所有输入参数)
Calculation      → Schedules (详细计算日程表)
Linking Logic    → Core Statements (三表链接)
Output Layer     → KPIs/Dashboard (输出指标)
```

### 完整的链接机制
```
Revenue Drivers → IS → Net Income ↓
                                  ├→ BS (Retained Earnings)
                                  └→ CFS (Operating Activities)
CapEx Schedule → IS (D&A) → BS (PPE) → CFS (Investing Activities)
Debt Schedule  → IS (Interest) → BS (Liabilities) → CFS (Financing)
```

### FAST标准实现
- **Flexible**: 独立修改假设，不影响其他计算
- **Appropriate**: 适当的模型复杂度（行业平均3-5年预测期）
- **Structured**: 清晰的模块划分，命名规范
- **Transparent**: 每个计算步骤可追踪，完整的审计日志

## 使用示例

```python
from models.three_statement import ThreeStatementModel
from models.dcf import DCFValuation
from data_processing.yahoo_finance import YahooFinanceAPI

# 1. 获取财务数据
yf = YahooFinanceAPI()
ticker = "0700.HK"  # 腾讯控股
financial_data = yf.get_financial_data(ticker)

# 2. 构建三表模型
model = ThreeStatementModel(
    ticker=ticker,
    historical_data=financial_data,
    projection_years=5
)

# 3. 运行模型
results = model.run(scenario='base')

# 4. DCF估值
dcf = DCFValuation(model=model)
valuation = dcf.calculate()

# 5. 获取KPI
kpis = model.get_kpis()

print(f"估值: ${valuation['equity_value']:.2f}")
print(f"ROE: {kpis['roe']:.2%}")
```

## API接口

所有模块通过FastAPI暴露HTTP接口，供前端调用。

详见 api_server.py

## 验证和检查

自动化检查列表：
- [ ] 资产负债表平衡: Assets = Liabilities + Equity
- [ ] 现金流对账: CFS Ending Cash = BS Cash
- [ ] 留存收益滚存: RE_End = RE_Begin + NI - Dividends
- [ ] 债务对账: Debt Schedule End = BS Debt
- [ ] 利息对账: Interest Expense = Debt Schedule Interest
- [ ] 公式完整性: 无硬编码数字在关键行
