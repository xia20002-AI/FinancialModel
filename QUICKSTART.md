# 财务分析平台 - 快速启动指南

## 项目概览

一个模块化的上市公司财务分析平台，支持三表财务模型建模和DCF估值分析。

**核心特性：**
- 📊 完整的三表财务模型 (IS/BS/CFS)
- 💰 DCF估值计算
- 📈 敏感性分析和场景分析
- 🎨 交互式数据可视化
- ⚙️ 模块化设计，关注点完全分离

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    React前端应用                         │
│            (输入模块 | 报表 | 估值 | 可视化)             │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────┐
│               Express后端服务 (Node.js)                 │
│                  (API路由 | 缓存 | 代理)                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│          Python财务引擎 (FastAPI)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 三表核心                                        │    │
│  │ - 时间表驱动的计算                              │    │
│  │ - 完整的链接机制                                │    │
│  │ - 自动对账                                      │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ DCF估值                                         │    │
│  │ - WACC计算                                      │    │
│  │ - 敏感性分析                                    │    │
│  │ - 情景分析                                      │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ 数据获取                                        │    │
│  │ - Yahoo Finance API                            │    │
│  │ - 财务数据清洗                                  │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    Yahoo Finance API      本地数据库(可选)
```

## 快速启动

### 方式1: 使用Docker Compose（推荐）

```bash
# 1. 进入项目目录
cd financial-analysis-platform

# 2. 启动所有服务
docker-compose up -d

# 3. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:3001
# Python API文档: http://localhost:8000/docs

# 4. 查看日志
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f financial-engine

# 5. 停止服务
docker-compose down
```

### 方式2: 本地开发启动

#### 前置条件
- Node.js 16+ 和 npm
- Python 3.9+
- pip

#### 启动步骤

**1. 启动Python财务引擎**
```bash
cd finance-engine
pip install -r requirements.txt
python api_server.py
# 访问: http://localhost:8000
# 文档: http://localhost:8000/docs (交互式API文档)
```

**2. 启动Express后端**（开新终端）
```bash
cd backend
npm install
npm run dev
# 访问: http://localhost:3001
```

**3. 启动React前端**（开新终端）
```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:3001 npm start
# 访问: http://localhost:3000
```

## 使用流程

### 1. 搜索公司
- 输入股票代码（如 MSFT, 0700.HK）或公司名称
- 系统自动显示匹配结果

### 2. 配置假设
- **收入驱动**: 设置5年的收入增长率
- **成本结构**: COGS、OpEx、CapEx占收入的比例
- **融资参数**: 所得税率、WACC、终端增长率
- 选择分析场景（基准/乐观/悲观）

### 3. 运行分析
- 点击"运行财务模型 & DCF估值"
- 系统自动：
  - 从Yahoo Finance获取财务数据
  - 构建三表财务模型
  - 计算DCF估值
  - 生成可视化报表

### 4. 查看结果

**财务报表标签页**
- 损益表 (Income Statement)
- 资产负债表 (Balance Sheet)
- 现金流量表 (Cash Flow Statement)
- 关键绩效指标 (KPIs)

**DCF估值标签页**
- 每股内在价值
- 投资建议 (BUY/HOLD/SELL)
- 上下行空间
- 敏感性分析

**数据可视化标签页**
- 收入和利润趋势
- 现金流分析
- 利润率趋势
- 估值构成分析

## 模型特性

### FAST标准实现

所有模型遵循**FAST标准**（Flexible, Appropriate, Structured, Transparent）：

| 特性 | 实现 |
|------|------|
| **Flexible** | 可随时修改任何假设，模型自动重新计算 |
| **Appropriate** | 适当的复杂度：支持3-10年预测期，简化模型 |
| **Structured** | 清晰的模块划分：输入→计算→输出 |
| **Transparent** | 完全的审计踪迹，每一步计算可追踪 |

### 关注点完全分离

```
输入层 (Input)
├─ 公司选择
├─ 假设设置
├─ 参数管理

计算层 (Calculation)
├─ 时间表驱动计算
│  ├─ 收入日程表
│  ├─ 成本日程表
│  ├─ CapEx日程表
│  ├─ 营运资本日程表
├─ 三表核心
│  ├─ 损益表
│  ├─ 资产负债表
│  ├─ 现金流量表
├─ DCF估值
│  ├─ WACC计算
│  ├─ FCF预测
│  ├─ 终端价值

输出层 (Output)
├─ 财务报表
├─ KPI指标
├─ 估值结果
├─ 可视化图表
```

### 完整的链接机制

```
收入驱动 
    ↓
损益表 (EBIT, Net Income)
    ├→ 资产负债表 (Retained Earnings, Equity)
    └→ 现金流量表 (Operating Activities)
    
CapEx&折旧
    ├→ 损益表 (D&A)
    ├→ 资产负债表 (PPE)
    └→ 现金流量表 (Investing Activities)

债务安排
    ├→ 损益表 (Interest Expense)
    ├→ 资产负债表 (Debt)
    └→ 现金流量表 (Financing Activities)
```

## 财务模型详解

### 三表财务模型

按照行业最佳实践构建，遵循FAST标准。

#### 损益表 (Income Statement)
```
Revenue
  ├─ COGS (成本占收入%)
  ├─ Gross Profit
  ├─ OpEx (运营支出占收入%)
  ├─ EBITDA
  ├─ D&A (从CapEx日程表)
  ├─ EBIT
  ├─ Interest Expense (从债务日程表)
  ├─ EBT
  ├─ Taxes
  └─ Net Income → 资产负债表 → 现金流量表
```

#### 资产负债表 (Balance Sheet)
```
Assets
├─ Current Assets
│  ├─ Cash
│  ├─ AR (应收账款 = 收入 × AR Days / 365)
│  └─ Inventory (库存 = COGS × Inventory Days / 365)
├─ PPE (从CapEx日程表: PPE = 期初 + CapEx - D&A)
└─ Total Assets

Liabilities & Equity
├─ AP (应付账款 = COGS × AP Days / 365)
├─ Debt (从债务日程表)
├─ Total Liabilities
├─ Retained Earnings (= 期初 + Net Income)
├─ Common Equity
└─ Total Equity

验证: Assets = Liabilities + Equity
```

#### 现金流量表 (Cash Flow Statement)
```
Operating Activities
├─ Net Income
├─ + D&A (加回非现金费用)
├─ - ΔWorking Capital
└─ = Operating CF

Investing Activities
├─ - CapEx
└─ = Investing CF

Financing Activities
├─ + Debt Drawdown
├─ - Debt Repayment
├─ - Dividends
└─ = Financing CF

Ending Cash = Beginning Cash + OCF + ICF + FCF
验证: Ending Cash = Balance Sheet Cash
```

### DCF估值模型

#### WACC计算
```
股权成本 (Cost of Equity) = Rf + β × (Rm - Rf)
  - Rf: 无风险利率 (默认3%)
  - β: 贝塔系数 (默认1.0)
  - Rm - Rf: 市场风险溢价 (默认7%)

WACC = Ke × (E/V) + Kd × (1-Tc) × (D/V)
  - E/V: 股权权重
  - D/V: 债务权重
  - Tc: 税率
```

#### 企业价值计算
```
Enterprise Value = PV(Forecast Period FCF) + PV(Terminal Value)

其中：
- Forecast Period: 5年(可调整)
- FCF = Operating CF - CapEx - ΔWorking Capital
- Terminal Value = FCF(final) × (1+g) / (WACC - g)
  - g: 终端增长率 (默认3%)

折现因子: 1 / (1 + WACC)^year
```

#### 股权价值和每股价值
```
Equity Value = Enterprise Value - Net Debt
Per Share Value = Equity Value / Shares Outstanding

上下行空间 = (Per Share Value - Current Price) / Current Price
```

## API端点

### Python FastAPI (http://localhost:8000)

```
GET  /health                  # 健康检查
GET  /search?q={query}        # 搜索公司
GET  /company/{ticker}        # 获取公司信息和财务数据
POST /financial-model         # 运行三表财务模型
POST /dcf-valuation          # 运行DCF估值
GET  /scenario-templates     # 获取场景模板
GET  /docs/assumptions       # 获取假设指南
```

### Express后端 (http://localhost:3001)

```
GET  /health                 # 健康检查
GET  /                       # 服务信息
     (其他请求都转发到Python API)
```

### React前端 (http://localhost:3000)

交互式Web应用，所有功能通过API调用实现。

## 开发指南

### 添加新的财务指标

在 `finance-engine/models/three_statement.py` 的 `calculate_kpis()` 方法中添加：

```python
def calculate_kpis(self):
    kpis = {}
    
    for i in range(self.projection_years):
        suffix = f"_Y{i+1}"
        
        # 添加你的KPI
        revenue = self.income_statement.loc[i, 'Revenue']
        ni = self.income_statement.loc[i, 'Net Income']
        
        kpis[f'MyKPI{suffix}'] = ni / revenue  # 示例
    
    self.kpis = kpis
    return kpis
```

### 修改财务假设

在 `finance-engine/models/three_statement.py` 的 `Assumptions` 类中添加新字段：

```python
@dataclass
class Assumptions:
    # ... 现有字段 ...
    my_new_assumption: float = 0.10  # 新假设
```

### 更新前端模块

编辑 `frontend/src/modules/` 下的对应模块文件来添加新的输入或输出。

## 故障排除

### Python API不可用
```bash
# 检查Python服务
curl http://localhost:8000/health

# 重启服务
cd finance-engine
python api_server.py
```

### 前端无法连接后端
```bash
# 检查环境变量
echo $REACT_APP_API_URL

# 或在 frontend/.env 中配置
REACT_APP_API_URL=http://localhost:3001
```

### 数据加载失败
- 检查网络连接
- 确保Yahoo Finance API可访问
- 查看浏览器console和服务器日志

## 参考资源

- 📖 [FAST标准](https://www.fast-standard.org/)
- 📊 [beefed.ai - 模块化三表财务模型](https://beefed.ai/zh/modular-3-statement-financial-model)
- 💻 [Flask/FastAPI文档](https://fastapi.tiangolo.com/)
- ⚛️ [React文档](https://react.dev/)

## 许可证

MIT

## 免责声明

⚠️ 本平台仅供学习和参考使用，不构成投资建议。使用者需自行承担投资风险。所有财务数据和估值结果均为示例，实际应用时需验证数据准确性。
