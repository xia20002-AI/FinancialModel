# 财务分析平台

## 项目概述
一个模块化的上市公司财务分析平台，支持三表财务模型建模和DCF估值分析。用户可通过输入股票代码或公司名称，自动匹配并分析财务数据。

## 设计原则 (FAST标准)
- **Flexible** - 灵活的假设修改和场景分析
- **Appropriate** - 适当的模型复杂度
- **Structured** - 清晰的模块化架构
- **Transparent** - 完全透明的计算逻辑

## 项目结构

```
financial-analysis-platform/
├── frontend/                 # React前端应用
│   ├── public/
│   ├── src/
│   │   ├── components/      # UI组件
│   │   ├── modules/         # 功能模块
│   │   │   ├── input/       # 输入模块
│   │   │   ├── dashboard/   # 仪表板输出
│   │   │   ├── visualization/ # 可视化
│   │   │   └── analysis/    # 分析展示
│   │   ├── services/        # API服务层
│   │   └── App.tsx
│   └── package.json
│
├── backend/                  # Express后端API
│   ├── src/
│   │   ├── controllers/      # 业务逻辑
│   │   ├── routes/           # API路由
│   │   ├── services/         # 服务层
│   │   ├── utils/            # 工具函数
│   │   └── app.ts
│   ├── package.json
│   └── tsconfig.json
│
├── finance-engine/           # Python财务计算引擎
│   ├── models/               # 财务模型
│   │   ├── three_statement.py   # 三表模型（IS/BS/CFS）
│   │   ├── dcf.py               # DCF估值
│   │   ├── scenarios.py          # 场景分析
│   │   └── kpis.py              # KPI计算
│   ├── data_processing/      # 数据处理
│   │   ├── yahoo_finance.py  # 数据获取
│   │   └── data_cleaner.py   # 数据清洗
│   ├── api_server.py         # FastAPI服务
│   ├── requirements.txt
│   └── README.md
│
└── README.md
```

## 模块化设计

### 1. 输入模块 (Input)
- 股票代码/公司名称输入框
- 自动完成匹配
- 基础假设设置（增长率、贴现率等）
- 场景配置器

### 2. 计算引擎 (Calculation Engine)
- **三表财务模型**：按照FAST标准
  - Income Statement (损益表)
  - Balance Sheet (资产负债表)
  - Cash Flow Statement (现金流量表)
  - 完整链接和对账机制

- **DCF估值模型**
  - 自由现金流预测
  - 终端价值计算
  - 加权平均资本成本(WACC)

- **敏感性分析**
  - 参数敏感性表
  - 情景分析

### 3. 输出模块 (Output)
- 财务报表展示
- KPI仪表板
- DCF估值结果
- 数据可视化图表
- PDF报告生成

## 关键特性

1. **完全的关注点分离**
   - 输入层：独立的假设和参数管理
   - 计算层：纯Python财务逻辑
   - 输出层：React可视化和报告

2. **数据驱动的财务建模**
   - 从Yahoo Finance实时获取财务数据
   - 自动对账和验证
   - 完整的审计踪迹

3. **灵活的场景分析**
   - 基准场景、悲观、中性、乐观四种场景
   - 独立修改假设而不影响其他计算
   - 版本控制和变更日志

4. **自动化检查和验证**
   - 资产负债表平衡检查
   - 现金流对账
   - 公式完整性验证

## 技术栈

- **前端**: React 18 + TypeScript + ECharts可视化
- **后端**: Node.js/Express + TypeScript
- **财务引擎**: Python 3.9+ + NumPy/Pandas
- **数据源**: Yahoo Finance API
- **部署**: Docker + Docker Compose

## 快速开始

### 前端
```bash
cd frontend
npm install
npm start
```

### 后端
```bash
cd backend
npm install
npm run dev
```

### 财务引擎
```bash
cd finance-engine
pip install -r requirements.txt
python api_server.py
```

## API文档

详见 [backend/API.md](backend/API.md)

## 财务模型文档

详见 [finance-engine/README.md](finance-engine/README.md)

## 参考资源

- [beefed.ai 模块化三表财务模型最佳实践](https://beefed.ai/zh/modular-3-statement-financial-model)
- [FAST标准](https://www.fast-standard.org/)

## 许可证

MIT
