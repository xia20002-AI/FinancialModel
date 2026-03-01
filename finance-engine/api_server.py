"""
财务分析FastAPI服务器

暴露HTTP接口供前端调用财务模型和DCF估值
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import asyncio

# 导入财务模块
from models.three_statement import ThreeStatementModel, ScenarioType, Assumptions
from models.dcf import DCFValuation
from data_processing.yahoo_finance import YahooFinanceAPI, DataCleaner

# 初始化FastAPI应用
app = FastAPI(
    title="财务分析API",
    description="三表财务模型和DCF估值接口",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据获取API
yf_api = YahooFinanceAPI()
cleaner = DataCleaner()

# ============ 数据模型 ============

class CompanySearchResult(BaseModel):
    """公司搜索结果"""
    ticker: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    type: Optional[str] = None


class AssumptionsInput(BaseModel):
    """财务假设输入"""
    revenue_growth_rates: Dict[int, float]
    cogs_pct_revenue: float = 0.35
    opex_pct_revenue: float = 0.20
    capex_pct_revenue: float = 0.05
    tax_rate: float = 0.25
    ar_days: int = 45
    inventory_days: int = 30
    ap_days: int = 30
    wacc: float = 0.08
    terminal_growth_rate: float = 0.03
    risk_free_rate: float = 0.03
    market_risk_premium: float = 0.07
    beta: float = 1.0


class FinancialModelRequest(BaseModel):
    """财务模型请求"""
    ticker: str
    assumptions: AssumptionsInput
    scenario: str = "base"
    projection_years: int = 5


class DCFValuationRequest(BaseModel):
    """DCF估值请求"""
    ticker: str
    assumptions: AssumptionsInput
    shares_outstanding: int
    current_stock_price: Optional[float] = None
    scenario: str = "base"


# ============ API 端点 ============

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/search", response_model=List[CompanySearchResult])
async def search_company(
    q: str = Query(..., description="搜索关键词（股票代码或公司名称）", min_length=1),
    limit: int = Query(10, description="最多返回结果数")
):
    """搜索公司
    
    Args:
        q: 搜索关键词
        limit: 返回结果数限制
    
    Returns:
        匹配的公司列表
    """
    try:
        results = yf_api.search_company(q)
        return results[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/{ticker}")
async def get_company_info(ticker: str):
    """获取公司基本信息
    
    Args:
        ticker: 股票代码
    
    Returns:
        公司基本信息和财务数据
    """
    try:
        # 获取基本信息
        info = yf_api.get_ticker_info(ticker)
        
        # 获取财务数据
        financials = yf_api.get_all_financial_data(ticker)
        
        # 获取历史价格
        prices = yf_api.get_historical_prices(ticker, '5y')
        
        return {
            'info': info,
            'income_statement': financials['income'].to_dict() if not financials['income'].empty else {},
            'balance_sheet': financials['balance'].to_dict() if not financials['balance'].empty else {},
            'cash_flow': financials['cashflow'].to_dict() if not financials['cashflow'].empty else {},
            'historical_prices': prices.to_dict() if not prices.empty else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/financial-model")
async def financial_model(request: FinancialModelRequest):
    """运行三表财务模型
    
    返回：
    - 损益表
    - 资产负债表
    - 现金流量表
    - KPI指标
    """
    try:
        # 获取财务数据
        financials = yf_api.get_all_financial_data(request.ticker)
        
        if financials['income'].empty:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 {request.ticker} 的财务数据"
            )
        
        # 清洗数据
        historical_data = cleaner.clean_financial_data(financials['income'])
        
        # 创建模型
        model = ThreeStatementModel(
            ticker=request.ticker,
            company_name=request.ticker,
            historical_financial_data=historical_data,
            projection_years=request.projection_years
        )
        
        # 设置假设
        model.set_assumptions(
            ScenarioType(request.scenario),
            revenue_growth_rates=request.assumptions.revenue_growth_rates,
            cogs_pct_revenue=request.assumptions.cogs_pct_revenue,
            opex_pct_revenue=request.assumptions.opex_pct_revenue,
            capex_pct_revenue=request.assumptions.capex_pct_revenue,
            tax_rate=request.assumptions.tax_rate,
            ar_days=request.assumptions.ar_days,
            inventory_days=request.assumptions.inventory_days,
            ap_days=request.assumptions.ap_days,
            wacc=request.assumptions.wacc,
            terminal_growth_rate=request.assumptions.terminal_growth_rate
        )
        
        # 运行模型
        results = model.run(ScenarioType(request.scenario))
        
        # 验证
        validation = model.validate_statements()
        
        return {
            'ticker': request.ticker,
            'scenario': request.scenario,
            'financial_model': results,
            'validation_passed': all(v[0] for v in validation.values()),
            'validation_details': {k: v[1] for k, v in validation.items()},
            'summary': model.get_summary().to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dcf-valuation")
async def dcf_valuation(request: DCFValuationRequest):
    """运行DCF估值
    
    返回：
    - 企业价值
    - 权益价值
    - 每股内在价值
    - 投资建议
    - 敏感性分析
    """
    try:
        # 获取财务数据
        financials = yf_api.get_all_financial_data(request.ticker)
        
        if financials['income'].empty:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 {request.ticker} 的财务数据"
            )
        
        # 清洗数据
        historical_data = cleaner.clean_financial_data(financials['income'])
        
        # 创建三表模型
        model = ThreeStatementModel(
            ticker=request.ticker,
            company_name=request.ticker,
            historical_financial_data=historical_data,
            projection_years=5
        )
        
        # 设置假设
        model.set_assumptions(
            ScenarioType(request.scenario),
            revenue_growth_rates=request.assumptions.revenue_growth_rates,
            cogs_pct_revenue=request.assumptions.cogs_pct_revenue,
            opex_pct_revenue=request.assumptions.opex_pct_revenue,
            capex_pct_revenue=request.assumptions.capex_pct_revenue,
            tax_rate=request.assumptions.tax_rate,
            ar_days=request.assumptions.ar_days,
            inventory_days=request.assumptions.inventory_days,
            ap_days=request.assumptions.ap_days,
            terminal_growth_rate=request.assumptions.terminal_growth_rate
        )
        
        # 运行模型
        model.run(ScenarioType(request.scenario))
        
        # 创建DCF估值
        dcf = DCFValuation(
            three_statement_model=model,
            shares_outstanding=request.shares_outstanding,
            current_stock_price=request.current_stock_price
        )
        
        # 运行估值
        valuation = dcf.calculate(
            risk_free_rate=request.assumptions.risk_free_rate,
            market_risk_premium=request.assumptions.market_risk_premium,
            beta=request.assumptions.beta,
            terminal_growth_rate=request.assumptions.terminal_growth_rate
        )
        
        # 敏感性分析
        sensitivity = dcf.sensitivity_analysis()
        
        return {
            'ticker': request.ticker,
            'valuation': valuation,
            'sensitivity_analysis': sensitivity.to_dict(),
            'free_cash_flows': dcf.free_cash_flows,
            'timestamp': datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scenario-templates")
async def get_scenario_templates():
    """获取场景模板
    
    返回预定义的假设场景
    """
    return {
        'base': {
            'description': '基准场景',
            'revenue_growth_rates': {1: 0.08, 2: 0.07, 3: 0.06, 4: 0.05, 5: 0.03},
            'wacc': 0.08,
            'terminal_growth_rate': 0.03
        },
        'bull': {
            'description': '乐观场景 - 高增长',
            'revenue_growth_rates': {1: 0.15, 2: 0.12, 3: 0.10, 4: 0.08, 5: 0.05},
            'wacc': 0.07,
            'terminal_growth_rate': 0.04
        },
        'bear': {
            'description': '悲观场景 - 低增长',
            'revenue_growth_rates': {1: 0.02, 2: 0.01, 3: 0.00, 4: -0.01, 5: 0.00},
            'wacc': 0.10,
            'terminal_growth_rate': 0.02
        }
    }


@app.get("/docs/assumptions")
async def get_assumptions_guide():
    """获取假设指南
    
    返回每个假设参数的说明和典型范围
    """
    return {
        'revenue_growth_rates': {
            'description': '按年度的收入增长率',
            'example': {1: 0.10, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.03},
            'typical_range': '0% - 20%'
        },
        'cogs_pct_revenue': {
            'description': '销售成本占收入百分比',
            'typical_range': '20% - 60%',
            'industry_example': {'Tech': 0.25, 'Retail': 0.60, 'Manufacturing': 0.50}
        },
        'wacc': {
            'description': '加权平均资本成本（贴现率）',
            'typical_range': '5% - 12%',
            'formula': 'Ke * (E/V) + Kd * (1-Tc) * (D/V)'
        },
        'terminal_growth_rate': {
            'description': '终端永续增长率',
            'typical_range': '2% - 4%',
            'note': '通常等于或略高于GDP增长率'
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
