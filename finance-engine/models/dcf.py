"""
DCF (Discounted Cash Flow) 估值模型

基于三表模型的自由现金流预测进行股权价值估值。

计算流程：
1. 计算自由现金流 (FCF) = Operating CF - CapEx
2. 计算终端价值 (Terminal Value)
3. 贴现回现值 (NPV)
4. 计算权益价值和每股价值
"""

from typing import Dict, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WACCComponents:
    """加权平均资本成本 (WACC) 组成部分"""
    
    cost_of_equity: float           # 股权成本 (Ke)
    cost_of_debt: float             # 债务成本 (Kd)
    tax_rate: float                 # 税率
    market_cap: float               # 市值
    debt_value: float               # 债务价值
    
    @property
    def wacc(self) -> float:
        """计算WACC = Ke * (E/V) + Kd * (1-Tc) * (D/V)"""
        total_value = self.market_cap + self.debt_value
        if total_value == 0:
            return 0.08  # 默认值
        
        equity_weight = self.market_cap / total_value
        debt_weight = self.debt_value / total_value
        
        return (self.cost_of_equity * equity_weight + 
                self.cost_of_debt * (1 - self.tax_rate) * debt_weight)
    
    def __str__(self):
        return (f"WACC={self.wacc:.2%} "
                f"(Ke={self.cost_of_equity:.2%}, Kd={self.cost_of_debt:.2%}, "
                f"E/V={self.market_cap/(self.market_cap+self.debt_value):.1%})")


class DCFValuation:
    """DCF估值引擎
    
    原则：
    - 基于三表模型的自由现金流
    - WACC作为折现率
    - 多种终端价值计算方法
    - 敏感性分析
    """
    
    def __init__(self, 
                 three_statement_model,
                 shares_outstanding: float = 1000000,
                 current_stock_price: float = None):
        """
        Args:
            three_statement_model: 三表财务模型
            shares_outstanding: 发行在外股份数
            current_stock_price: 当前股价（用于与估值对比）
        """
        self.model = three_statement_model
        self.shares_outstanding = shares_outstanding
        self.current_stock_price = current_stock_price
        
        # 估值结果容器
        self.free_cash_flows: Dict[int, float] = {}
        self.terminal_value: float = 0.0
        self.enterprise_value: float = 0.0
        self.equity_value: float = 0.0
        self.intrinsic_value_per_share: float = 0.0
        
        # WACC计算
        self.wacc_components: WACCComponents = None
        self.wacc: float = 0.08  # 默认值
        
    def calculate_free_cash_flow(self) -> Dict[int, float]:
        """计算自由现金流
        
        FCF = Operating CF - CapEx - Change in NWC + NWC Recovery at end
        
        或简化：FCF = NOPAT + D&A - CapEx - Change in NWC
        其中NOPAT (Net Operating Profit After Tax) = EBIT * (1-税率)
        """
        fcf = {}
        
        for i in range(len(self.model.income_statement)):
            year = i + 1
            
            # 方法1：从现金流量表计算
            operating_cf = self.model.cash_flow_statement.loc[i, 'Operating CF']
            capex = self.model.cash_flow_statement.loc[i, 'CapEx']
            
            fcf[year] = operating_cf - capex
        
        self.free_cash_flows = fcf
        return fcf
    
    def calculate_wacc(self, risk_free_rate: float = 0.03, 
                      market_risk_premium: float = 0.07,
                      beta: float = 1.0,
                      cost_of_debt: float = None) -> float:
        """计算WACC
        
        步骤：
        1. 计算股权成本 (CAPM): Ke = Rf + β(Rm - Rf)
        2. 计算加权平均资本成本
        
        Args:
            risk_free_rate: 无风险利率
            market_risk_premium: 市场风险溢价
            beta: 贝塔系数 (相对市场波动性)
            cost_of_debt: 债务成本 (如果为None则自动计算)
        
        Returns:
            WACC 加权平均资本成本
        """
        # 计算股权成本 (CAPM)
        cost_of_equity = risk_free_rate + beta * market_risk_premium
        
        # 获取债务和市值信息 (从最后一年的BS)
        final_year = len(self.model.balance_sheet) - 1
        debt = self.model.balance_sheet.loc[final_year, 'Debt']
        equity = self.model.balance_sheet.loc[final_year, 'Equity']
        
        # 如果未提供债务成本，根据债务估算
        if cost_of_debt is None:
            interest_expense = self.model.income_statement.loc[final_year, 'Interest Expense']
            cost_of_debt = interest_expense / debt if debt > 0 else 0.05
        
        tax_rate = self.model.assumptions.tax_rate
        
        # 创建WACC组件
        self.wacc_components = WACCComponents(
            cost_of_equity=cost_of_equity,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
            market_cap=equity,
            debt_value=debt
        )
        
        self.wacc = self.wacc_components.wacc
        
        return self.wacc
    
    def calculate_terminal_value_perpetuity(self) -> float:
        """永续增长法计算终端价值
        
        TV = FCF(最后一年) * (1 + g) / (WACC - g)
        
        其中g是长期增长率（通常等于GDP增长率）
        """
        final_year = len(self.model.cash_flow_statement)
        final_fcf = self.free_cash_flows[final_year]
        
        g = self.model.assumptions.terminal_growth_rate
        
        if self.wacc <= g:
            raise ValueError(f"WACC ({self.wacc:.2%}) 必须大于增长率 ({g:.2%})")
        
        tv = final_fcf * (1 + g) / (self.wacc - g)
        self.terminal_value = tv
        
        return tv
    
    def calculate_terminal_value_exit_multiple(self, 
                                              exit_multiple: float,
                                              metric: str = 'EBITDA') -> float:
        """倍数法计算终端价值
        
        TV = Final Year Metric * Exit Multiple
        
        Args:
            exit_multiple: 出口倍数 (如EBITDA倍数)
            metric: 使用的指标 ('EBITDA', 'Revenue', 'Net Income')
        """
        final_year = len(self.model.income_statement) - 1
        
        if metric == 'EBITDA':
            final_metric = self.model.income_statement.loc[final_year, 'EBITDA']
        elif metric == 'Revenue':
            final_metric = self.model.income_statement.loc[final_year, 'Revenue']
        elif metric == 'Net Income':
            final_metric = self.model.income_statement.loc[final_year, 'Net Income']
        else:
            raise ValueError(f"未知的metric: {metric}")
        
        tv = final_metric * exit_multiple
        self.terminal_value = tv
        
        return tv
    
    def calculate_enterprise_value(self) -> float:
        """计算企业价值 (Enterprise Value)
        
        EV = PV(预测期FCF) + PV(终端价值)
        """
        pv_fcf = 0.0
        
        # 每年的现值
        for year, fcf in self.free_cash_flows.items():
            pv = fcf / ((1 + self.wacc) ** year)
            pv_fcf += pv
        
        # 终端价值的现值
        forecast_years = len(self.free_cash_flows)
        pv_terminal_value = self.terminal_value / ((1 + self.wacc) ** forecast_years)
        
        self.enterprise_value = pv_fcf + pv_terminal_value
        
        return self.enterprise_value
    
    def calculate_equity_value(self) -> float:
        """计算权益价值
        
        Equity Value = Enterprise Value - Net Debt
        其中 Net Debt = Total Debt - Cash
        """
        final_year = len(self.model.balance_sheet) - 1
        total_debt = self.model.balance_sheet.loc[final_year, 'Debt']
        cash = self.model.balance_sheet.loc[final_year, 'Cash']
        
        net_debt = total_debt - cash
        self.equity_value = self.enterprise_value - net_debt
        
        return self.equity_value
    
    def calculate_intrinsic_value_per_share(self) -> float:
        """计算每股内在价值
        
        Per Share Value = Equity Value / Shares Outstanding
        """
        self.intrinsic_value_per_share = self.equity_value / self.shares_outstanding
        return self.intrinsic_value_per_share
    
    def calculate(self, 
                 risk_free_rate: float = 0.03,
                 market_risk_premium: float = 0.07,
                 beta: float = 1.0,
                 terminal_growth_rate: float = None) -> Dict:
        """运行完整的DCF估值
        
        返回详细的估值结果
        """
        # 如果提供了terminal growth rate，设置到模型
        if terminal_growth_rate is not None:
            self.model.assumptions.terminal_growth_rate = terminal_growth_rate
        
        # 1. 计算自由现金流
        self.calculate_free_cash_flow()
        
        # 2. 计算WACC
        self.calculate_wacc(risk_free_rate, market_risk_premium, beta)
        
        # 3. 计算终端价值 (使用永续增长法)
        self.calculate_terminal_value_perpetuity()
        
        # 4. 计算企业价值
        self.calculate_enterprise_value()
        
        # 5. 计算权益价值
        self.calculate_equity_value()
        
        # 6. 计算每股内在价值
        self.calculate_intrinsic_value_per_share()
        
        # 计算上下行空间（如果有当前股价）
        upside_downside = None
        upside_downside_pct = None
        if self.current_stock_price:
            upside_downside = self.intrinsic_value_per_share - self.current_stock_price
            upside_downside_pct = upside_downside / self.current_stock_price
        
        return {
            'ticker': self.model.ticker,
            'company_name': self.model.company_name,
            'valuation_date': datetime.now().isoformat(),
            
            # WACC信息
            'wacc': self.wacc,
            'wacc_details': {
                'cost_of_equity': self.wacc_components.cost_of_equity,
                'cost_of_debt': self.wacc_components.cost_of_debt,
                'tax_rate': self.wacc_components.tax_rate,
                'equity_weight': self.wacc_components.market_cap / (self.wacc_components.market_cap + self.wacc_components.debt_value),
                'debt_weight': self.wacc_components.debt_value / (self.wacc_components.market_cap + self.wacc_components.debt_value)
            },
            
            # 现金流信息
            'free_cash_flows': self.free_cash_flows,
            'pv_fcf': sum(fcf / ((1 + self.wacc) ** year) 
                         for year, fcf in self.free_cash_flows.items()),
            
            # 终端价值
            'terminal_value': self.terminal_value,
            'terminal_growth_rate': self.model.assumptions.terminal_growth_rate,
            'pv_terminal_value': self.terminal_value / ((1 + self.wacc) ** len(self.free_cash_flows)),
            
            # 估值结果
            'enterprise_value': self.enterprise_value,
            'net_debt': (self.model.balance_sheet.iloc[-1]['Debt'] - 
                        self.model.balance_sheet.iloc[-1]['Cash']),
            'equity_value': self.equity_value,
            'shares_outstanding': self.shares_outstanding,
            'intrinsic_value_per_share': self.intrinsic_value_per_share,
            
            # 当前股价对比
            'current_stock_price': self.current_stock_price,
            'upside_downside': upside_downside,
            'upside_downside_pct': upside_downside_pct,
            
            # 投资建议
            'recommendation': self._get_recommendation(),
        }
    
    def _get_recommendation(self) -> str:
        """基于上下行空间给出投资建议"""
        if self.current_stock_price is None:
            return "HOLD"
        
        upside_pct = (self.intrinsic_value_per_share - self.current_stock_price) / self.current_stock_price
        
        if upside_pct > 0.25:
            return "STRONG BUY"
        elif upside_pct > 0.10:
            return "BUY"
        elif upside_pct > -0.10:
            return "HOLD"
        elif upside_pct > -0.25:
            return "SELL"
        else:
            return "STRONG SELL"
    
    def sensitivity_analysis(self, 
                            wacc_range: Tuple[float, float] = (-0.02, 0.02),
                            terminal_growth_range: Tuple[float, float] = (-0.02, 0.02),
                            steps: int = 5) -> pd.DataFrame:
        """敏感性分析
        
        创建一个关于WACC和终端增长率的敏感性表格
        """
        base_wacc = self.wacc
        base_tg = self.model.assumptions.terminal_growth_rate
        
        wacc_values = np.linspace(
            base_wacc + wacc_range[0],
            base_wacc + wacc_range[1],
            steps
        )
        
        tg_values = np.linspace(
            base_tg + terminal_growth_range[0],
            base_tg + terminal_growth_range[1],
            steps
        )
        
        # 创建敏感性矩阵
        sensitivity_matrix = np.zeros((len(wacc_values), len(tg_values)))
        
        for i, wacc in enumerate(wacc_values):
            for j, tg in enumerate(tg_values):
                # 临时改变参数
                old_wacc = self.wacc
                old_tg = self.model.assumptions.terminal_growth_rate
                
                self.wacc = wacc
                self.model.assumptions.terminal_growth_rate = tg
                
                # 重新计算终端价值和EV
                tv = self.calculate_terminal_value_perpetuity()
                ev = self.enterprise_value
                equity_v = self.calculate_equity_value()
                per_share = self.calculate_intrinsic_value_per_share()
                
                sensitivity_matrix[i, j] = per_share
                
                # 恢复参数
                self.wacc = old_wacc
                self.model.assumptions.terminal_growth_rate = old_tg
        
        # 转换为DataFrame
        df = pd.DataFrame(
            sensitivity_matrix,
            index=[f"{w:.2%}" for w in wacc_values],
            columns=[f"{tg:.2%}" for tg in tg_values]
        )
        
        df.index.name = 'WACC'
        df.columns.name = 'Terminal Growth Rate'
        
        return df


if __name__ == "__main__":
    from three_statement import ThreeStatementModel, ScenarioType
    
    # 创建示例数据
    test_data = pd.DataFrame({
        'Revenue': [100000000, 110000000, 121000000],
        'PPE': [50000000, 55000000, 60000000]
    })
    
    # 创建并运行三表模型
    model = ThreeStatementModel(
        ticker='TEST',
        company_name='Test Company',
        historical_financial_data=test_data,
        projection_years=5
    )
    
    model.set_assumptions(
        ScenarioType.BASE,
        revenue_growth_rates={1: 0.10, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.03}
    )
    
    model.run()
    
    # 运行DCF估值
    dcf = DCFValuation(
        three_statement_model=model,
        shares_outstanding=100000000,
        current_stock_price=50.0
    )
    
    valuation = dcf.calculate()
    
    print("=== DCF 估值结果 ===")
    print(f"企业价值: ${valuation['enterprise_value']:,.0f}")
    print(f"权益价值: ${valuation['equity_value']:,.0f}")
    print(f"每股内在价值: ${valuation['intrinsic_value_per_share']:.2f}")
    print(f"当前股价: ${valuation['current_stock_price']:.2f}")
    print(f"上下行空间: {valuation['upside_downside_pct']:.2%}")
    print(f"投资建议: {valuation['recommendation']}")
