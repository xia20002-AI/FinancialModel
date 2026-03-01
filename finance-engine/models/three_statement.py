"""
三表财务模型 - 按照FAST标准实现

结构：
1. Assumptions (输入) - 所有可修改的参数
2. Schedules (日程表) - 详细的计算日程
3. Core Statements (核心报表) - IS/BS/CFS完整链接
4. KPIs (输出) - 关键绩效指标
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from datetime import datetime
from enum import Enum


class ScenarioType(Enum):
    """情景类型"""
    BASE = "base"      # 基准情景
    BULL = "bull"      # 乐观情景
    BEAR = "bear"      # 悲观情景
    CUSTOM = "custom"  # 自定义情景


@dataclass
class Assumptions:
    """假设输入层 - 所有驱动参数
    
    设计原则：
    - 所有输入参数在此集中管理
    - 按主题分组（Revenue, Costs, Financing等）
    - 清晰的单位和时间基准标注
    """
    # ==== 基本信息 ====
    ticker: str                                    # 股票代码
    company_name: str                              # 公司名称
    currency: str = "USD"                          # 货币
    timebase: str = "annual"                       # 时间基准 (annual/quarterly)
    
    # ==== 收入驱动 ====
    revenue_growth_rates: Dict[int, float] = field(default_factory=dict)  # 按年份的收入增长率
    
    # ==== 成本驱动 ====
    cogs_pct_revenue: float = 0.35                # COGS占收入比例
    opex_pct_revenue: float = 0.20                # OpEx占收入百分比
    
    # ==== 资本支出 ====
    capex_pct_revenue: float = 0.05               # CapEx占收入比例
    
    # ==== 营运资本 ====
    ar_days: int = 45                             # 应收账款天数
    inventory_days: int = 30                       # 库存天数
    ap_days: int = 30                             # 应付账款天数
    
    # ==== 融资 ====
    debt_ratio: float = 0.3                       # 目标债务比例
    interest_rate: float = 0.05                   # 平均利率
    tax_rate: float = 0.25                        # 所得税率
    
    # ==== DCF参数 ====
    wacc: float = 0.08                            # 加权平均资本成本
    terminal_growth_rate: float = 0.03            # 终端增长率
    projection_years: int = 5                     # 预测年数
    
    # ==== 折旧 ====
    depreciation_pct_revenue: float = 0.03        # 折旧占收入比例
    
    def __str__(self):
        return f"Assumptions({self.ticker}): Revenue growth={self.revenue_growth_rates}, WACC={self.wacc:.1%}"


@dataclass
class ScheduleRow:
    """日程表行项"""
    period: int                                    # 年份或期间
    values: Dict[str, float]                       # 按名称的值
    
    def __getitem__(self, key: str) -> float:
        return self.values.get(key, 0.0)
    
    def __setitem__(self, key: str, value: float):
        self.values[key] = value


class RevenueSchedule:
    """收入日程表 - 驱动优先的实现"""
    
    def __init__(self, assumptions: Assumptions, historical_revenue: List[float], years: int):
        """
        Args:
            assumptions: 假设参数
            historical_revenue: 历史收入
            years: 预测年数
        """
        self.assumptions = assumptions
        self.historical_revenue = historical_revenue
        self.years = years
        self.schedule: List[ScheduleRow] = []
        
    def calculate(self):
        """使用成长率驱动计算预测收入"""
        base_revenue = self.historical_revenue[-1]
        
        for year in range(1, self.years + 1):
            # 获取该年的增长率，如果未指定则使用最后一个已知的率
            growth_rate = self.assumptions.revenue_growth_rates.get(
                year, 
                list(self.assumptions.revenue_growth_rates.values())[-1] if self.assumptions.revenue_growth_rates else 0.03
            )
            
            revenue = base_revenue * ((1 + growth_rate) ** year)
            
            self.schedule.append(ScheduleRow(
                period=year,
                values={"Revenue": revenue}
            ))
        
        return self.schedule


class CostsSchedule:
    """成本日程表 - COGS和OpEx"""
    
    def __init__(self, assumptions: Assumptions, revenue_schedule: List[ScheduleRow]):
        self.assumptions = assumptions
        self.revenue_schedule = revenue_schedule
        self.schedule: List[ScheduleRow] = []
        
    def calculate(self):
        """计算COGS和OpEx"""
        for i, rev_row in enumerate(self.revenue_schedule):
            revenue = rev_row["Revenue"]
            cogs = revenue * self.assumptions.cogs_pct_revenue
            opex = revenue * self.assumptions.opex_pct_revenue
            depreciation = revenue * self.assumptions.depreciation_pct_revenue
            
            self.schedule.append(ScheduleRow(
                period=i + 1,
                values={
                    "COGS": cogs,
                    "OpEx": opex,
                    "Depreciation": depreciation,
                    "Revenue": revenue
                }
            ))
        
        return self.schedule


class CapExSchedule:
    """资本支出和固定资产日程表"""
    
    def __init__(self, assumptions: Assumptions, revenue_schedule: List[ScheduleRow], 
                 initial_ppe: float):
        self.assumptions = assumptions
        self.revenue_schedule = revenue_schedule
        self.initial_ppe = initial_ppe
        self.schedule: List[ScheduleRow] = []
        
    def calculate(self):
        """计算CapEx、折旧、PP&E滚存"""
        ppe = self.initial_ppe
        
        for i, rev_row in enumerate(self.revenue_schedule):
            revenue = rev_row["Revenue"]
            capex = revenue * self.assumptions.capex_pct_revenue
            depreciation = revenue * self.assumptions.depreciation_pct_revenue
            
            # PP&E滚存: 期末 = 期初 + CapEx - 折旧
            ppe = ppe + capex - depreciation
            
            self.schedule.append(ScheduleRow(
                period=i + 1,
                values={
                    "CapEx": capex,
                    "Depreciation": depreciation,
                    "PPE_Beginning": ppe - capex + depreciation,
                    "PPE_Ending": ppe,
                    "Revenue": revenue
                }
            ))
        
        return self.schedule


class WorkingCapitalSchedule:
    """营运资本日程表"""
    
    def __init__(self, assumptions: Assumptions, revenue_schedule: List[ScheduleRow],
                 cogs_schedule: List[ScheduleRow], initial_nwc: float):
        self.assumptions = assumptions
        self.revenue_schedule = revenue_schedule
        self.cogs_schedule = cogs_schedule
        self.initial_nwc = initial_nwc
        self.schedule: List[ScheduleRow] = []
        
    def calculate(self):
        """计算AR/AP/Inventory和营运资本变动"""
        prev_nwc = self.initial_nwc
        
        for i, rev_row in enumerate(self.revenue_schedule):
            revenue = rev_row["Revenue"]
            cogs = self.cogs_schedule[i]["COGS"]
            
            # 计算余额
            ar = revenue * self.assumptions.ar_days / 365
            inventory = cogs * self.assumptions.inventory_days / 365
            ap = cogs * self.assumptions.ap_days / 365
            
            # NWC = AR + Inventory - AP
            nwc = ar + inventory - ap
            nwc_change = nwc - prev_nwc
            
            self.schedule.append(ScheduleRow(
                period=i + 1,
                values={
                    "AR": ar,
                    "Inventory": inventory,
                    "AP": ap,
                    "NWC": nwc,
                    "NWC_Change": nwc_change,
                    "Revenue": revenue
                }
            ))
            
            prev_nwc = nwc
        
        return self.schedule


class ThreeStatementModel:
    """三表财务模型 - 完整实现
    
    架构：
    1. 输入层 (Assumptions)
    2. 日程表层 (Schedules) - 详细驱动
    3. 核心报表 (Statements) - IS/BS/CFS
    4. 输出层 (KPIs & Dashboard)
    
    设计特性：
    - 完全的关注点分离
    - 模块化和独立计算
    - 自动对账和验证
    - 审计追踪
    """
    
    def __init__(self, 
                 ticker: str,
                 company_name: str,
                 historical_financial_data: pd.DataFrame,
                 projection_years: int = 5):
        """
        Args:
            ticker: 股票代码
            company_name: 公司名称
            historical_financial_data: 历史财务数据 (应包含收入、利润等)
            projection_years: 预测年数
        """
        self.ticker = ticker
        self.company_name = company_name
        self.historical_data = historical_financial_data
        self.projection_years = projection_years
        
        # 初始化假设
        self.assumptions = Assumptions(
            ticker=ticker,
            company_name=company_name,
            projection_years=projection_years
        )
        
        # 日程表容器
        self.schedules: Dict[str, List[ScheduleRow]] = {}
        
        # 报表容器
        self.income_statement: pd.DataFrame = pd.DataFrame()
        self.balance_sheet: pd.DataFrame = pd.DataFrame()
        self.cash_flow_statement: pd.DataFrame = pd.DataFrame()
        
        # KPI容器
        self.kpis: Dict[str, float] = {}
        
        # 检查结果
        self.validation_results: Dict[str, bool] = {}
        
    def set_assumptions(self, scenario: ScenarioType, **kwargs):
        """设置假设参数"""
        for key, value in kwargs.items():
            if hasattr(self.assumptions, key):
                setattr(self.assumptions, key, value)
    
    def calculate_schedules(self):
        """计算所有日程表"""
        # 提取历史基数
        historical_revenue = self.historical_data['Revenue'].tolist() if 'Revenue' in self.historical_data.columns else [1000000]
        
        # 收入日程
        revenue_sched = RevenueSchedule(
            self.assumptions,
            historical_revenue,
            self.projection_years
        )
        self.schedules['revenue'] = revenue_sched.calculate()
        
        # 成本日程
        costs_sched = CostsSchedule(self.assumptions, self.schedules['revenue'])
        self.schedules['costs'] = costs_sched.calculate()
        
        # CapEx日程
        initial_ppe = self.historical_data['PPE'].iloc[-1] if 'PPE' in self.historical_data.columns else 1000000
        capex_sched = CapExSchedule(self.assumptions, self.schedules['revenue'], initial_ppe)
        self.schedules['capex'] = capex_sched.calculate()
        
        # 营运资本日程
        initial_nwc = 100000  # 简化假设
        wc_sched = WorkingCapitalSchedule(
            self.assumptions,
            self.schedules['revenue'],
            self.schedules['costs'],
            initial_nwc
        )
        self.schedules['working_capital'] = wc_sched.calculate()
    
    def calculate_income_statement(self):
        """计算损益表"""
        periods = []
        revenue = []
        cogs = []
        opex = []
        depreciation = []
        ebitda = []
        ebit = []
        interest_expense = []
        ebt = []
        taxes = []
        net_income = []
        
        for i in range(self.projection_years):
            period = i + 1
            rev = self.schedules['revenue'][i]['Revenue']
            cogs_val = self.schedules['costs'][i]['COGS']
            opex_val = self.schedules['costs'][i]['OpEx']
            depr_val = self.schedules['costs'][i]['Depreciation']
            
            # 计算
            ebitda_val = rev - cogs_val - opex_val
            ebit_val = ebitda_val - depr_val
            interest_val = ebit_val * 0.05  # 简化假设
            ebt_val = ebit_val - interest_val
            tax_val = max(ebt_val * self.assumptions.tax_rate, 0)
            ni_val = ebt_val - tax_val
            
            periods.append(period)
            revenue.append(rev)
            cogs.append(cogs_val)
            opex.append(opex_val)
            depreciation.append(depr_val)
            ebitda.append(ebitda_val)
            ebit.append(ebit_val)
            interest_expense.append(interest_val)
            ebt.append(ebt_val)
            taxes.append(tax_val)
            net_income.append(ni_val)
        
        self.income_statement = pd.DataFrame({
            'Year': periods,
            'Revenue': revenue,
            'COGS': cogs,
            'OpEx': opex,
            'Depreciation': depreciation,
            'EBITDA': ebitda,
            'EBIT': ebit,
            'Interest Expense': interest_expense,
            'EBT': ebt,
            'Taxes': taxes,
            'Net Income': net_income
        })
    
    def calculate_balance_sheet(self):
        """计算资产负债表"""
        periods = []
        cash = []
        ar = []
        inventory = []
        current_assets = []
        ppe = []
        total_assets = []
        ap = []
        current_liabilities = []
        debt = []
        total_liabilities = []
        retained_earnings = []
        equity = []
        
        cash_balance = 500000
        debt_balance = 500000
        re_balance = 1000000
        
        for i in range(self.projection_years):
            period = i + 1
            
            # 资产
            ar_val = self.schedules['working_capital'][i]['AR']
            inv_val = self.schedules['working_capital'][i]['Inventory']
            cur_assets = cash_balance + ar_val + inv_val
            
            ppe_val = self.schedules['capex'][i]['PPE_Ending']
            tot_assets = cur_assets + ppe_val
            
            # 负债和权益
            ap_val = self.schedules['working_capital'][i]['AP']
            cur_liab = ap_val
            debt_balance = debt_balance * (1 - 0.1)  # 偿还
            tot_liab = cur_liab + debt_balance
            
            ni_val = self.income_statement.loc[i, 'Net Income']
            re_balance = re_balance + ni_val
            equity_val = re_balance + 1000000  # Common equity
            
            periods.append(period)
            cash.append(cash_balance)
            ar.append(ar_val)
            inventory.append(inv_val)
            current_assets.append(cur_assets)
            ppe.append(ppe_val)
            total_assets.append(tot_assets)
            ap.append(ap_val)
            current_liabilities.append(cur_liab)
            debt.append(debt_balance)
            total_liabilities.append(tot_liab)
            retained_earnings.append(re_balance)
            equity.append(equity_val)
        
        self.balance_sheet = pd.DataFrame({
            'Year': periods,
            'Cash': cash,
            'AR': ar,
            'Inventory': inventory,
            'Current Assets': current_assets,
            'PPE': ppe,
            'Total Assets': total_assets,
            'AP': ap,
            'Current Liabilities': current_liabilities,
            'Debt': debt,
            'Total Liabilities': total_liabilities,
            'Retained Earnings': retained_earnings,
            'Equity': equity
        })
    
    def calculate_cash_flow_statement(self):
        """计算现金流量表"""
        periods = []
        net_income = []
        depreciation = []
        nwc_change = []
        operating_cf = []
        capex = []
        investing_cf = []
        debt_change = []
        financing_cf = []
        net_cf = []
        
        for i in range(self.projection_years):
            period = i + 1
            ni = self.income_statement.loc[i, 'Net Income']
            depr = self.income_statement.loc[i, 'Depreciation']
            nwc_ch = self.schedules['working_capital'][i]['NWC_Change']
            capex_val = self.schedules['capex'][i]['CapEx']
            
            ocf = ni + depr - nwc_ch
            icf = -capex_val
            fcf = 0  # 简化
            
            ncf = ocf + icf + fcf
            
            periods.append(period)
            net_income.append(ni)
            depreciation.append(depr)
            nwc_change.append(nwc_ch)
            operating_cf.append(ocf)
            capex.append(capex_val)
            investing_cf.append(icf)
            debt_change.append(0)
            financing_cf.append(fcf)
            net_cf.append(ncf)
        
        self.cash_flow_statement = pd.DataFrame({
            'Year': periods,
            'Net Income': net_income,
            'Depreciation': depreciation,
            'NWC Change': nwc_change,
            'Operating CF': operating_cf,
            'CapEx': capex,
            'Investing CF': investing_cf,
            'Debt Change': debt_change,
            'Financing CF': financing_cf,
            'Net CF': net_cf
        })
    
    def validate_statements(self) -> Dict[str, Tuple[bool, str]]:
        """自动验证和对账"""
        results = {}
        
        # 检查1: 资产负债表平衡
        for i in range(len(self.balance_sheet)):
            assets = self.balance_sheet.loc[i, 'Total Assets']
            liabilities = self.balance_sheet.loc[i, 'Total Liabilities']
            equity = self.balance_sheet.loc[i, 'Equity']
            
            is_balanced = abs(assets - (liabilities + equity)) < 0.01
            results[f'BS_Balance_Y{i+1}'] = (is_balanced, 
                f"Assets={assets:.0f}, Liab+Equity={liabilities+equity:.0f}")
        
        # 检查2: 留存收益滚存
        re_check = all(
            abs(self.balance_sheet.loc[i, 'Retained Earnings'] - 
                (self.balance_sheet.loc[max(0, i-1), 'Retained Earnings'] + 
                 self.income_statement.loc[i, 'Net Income'])) < 0.01
            for i in range(1, len(self.balance_sheet))
        )
        results['RE_Rollforward'] = (re_check, "Retained earnings flow check")
        
        self.validation_results = results
        return results
    
    def calculate_kpis(self):
        """计算关键绩效指标"""
        kpis = {}
        
        for i in range(self.projection_years):
            suffix = f"_Y{i+1}"
            
            # 盈利能力
            revenue = self.income_statement.loc[i, 'Revenue']
            ni = self.income_statement.loc[i, 'Net Income']
            ebit = self.income_statement.loc[i, 'EBIT']
            
            kpis[f'Net Margin{suffix}'] = ni / revenue if revenue > 0 else 0
            kpis[f'EBITDA Margin{suffix}'] = self.income_statement.loc[i, 'EBITDA'] / revenue if revenue > 0 else 0
            
            # 效率
            assets = self.balance_sheet.loc[i, 'Total Assets']
            equity = self.balance_sheet.loc[i, 'Equity']
            
            kpis[f'ROA{suffix}'] = ni / assets if assets > 0 else 0
            kpis[f'ROE{suffix}'] = ni / equity if equity > 0 else 0
            
            # 财务健康
            liabilities = self.balance_sheet.loc[i, 'Total Liabilities']
            kpis[f'Debt_to_Equity{suffix}'] = liabilities / equity if equity > 0 else 0
            
        self.kpis = kpis
        return kpis
    
    def run(self, scenario: ScenarioType = ScenarioType.BASE) -> Dict:
        """运行完整的财务模型"""
        # 1. 计算日程表
        self.calculate_schedules()
        
        # 2. 计算三表
        self.calculate_income_statement()
        self.calculate_balance_sheet()
        self.calculate_cash_flow_statement()
        
        # 3. 验证对账
        validation = self.validate_statements()
        
        # 4. 计算KPI
        self.calculate_kpis()
        
        return {
            'scenario': scenario.value,
            'ticker': self.ticker,
            'company_name': self.company_name,
            'income_statement': self.income_statement.to_dict(),
            'balance_sheet': self.balance_sheet.to_dict(),
            'cash_flow_statement': self.cash_flow_statement.to_dict(),
            'kpis': self.kpis,
            'validation': {k: v[0] for k, v in validation.items()},
            'timestamp': datetime.now().isoformat()
        }
    
    def get_summary(self) -> pd.DataFrame:
        """获取模型摘要"""
        summary_data = {
            'Year': self.income_statement['Year'],
            'Revenue': self.income_statement['Revenue'],
            'EBITDA': self.income_statement['EBITDA'],
            'Net Income': self.income_statement['Net Income'],
            'Operating CF': self.cash_flow_statement['Operating CF']
        }
        return pd.DataFrame(summary_data)


if __name__ == "__main__":
    # 测试数据
    test_data = pd.DataFrame({
        'Revenue': [100000000, 110000000, 121000000],
        'PPE': [50000000, 55000000, 60000000]
    })
    
    # 创建模型
    model = ThreeStatementModel(
        ticker='TEST',
        company_name='Test Company',
        historical_financial_data=test_data,
        projection_years=5
    )
    
    # 设置假设
    model.set_assumptions(
        ScenarioType.BASE,
        revenue_growth_rates={1: 0.10, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.03}
    )
    
    # 运行模型
    results = model.run()
    
    print("收入预测:")
    print(model.income_statement[['Year', 'Revenue', 'EBITDA', 'Net Income']])
    print("\n关键绩效指标:")
    for k, v in model.kpis.items():
        if 'Y1' in k:
            print(f"  {k}: {v:.2%}")
