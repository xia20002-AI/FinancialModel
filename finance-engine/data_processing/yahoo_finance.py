"""
Yahoo Finance 数据获取模块

作用：从Yahoo Finance API获取股票财务数据和价格信息
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
from datetime import datetime, timedelta
import json


class YahooFinanceAPI:
    """Yahoo Finance API 封装
    
    支持：
    - 财务报表数据（收入、利润等）
    - 资产负债表数据
    - 现金流数据
    - 股票价格数据
    """
    
    BASE_URL = "https://query1.finance.yahoo.com"
    
    # 关键财务指标映射
    INCOME_STATEMENT_KEYS = {
        'TotalRevenue': 'Revenue',
        'CostOfRevenue': 'COGS',
        'GrossProfit': 'Gross Profit',
        'OperatingExpenses': 'OpEx',
        'OperatingIncome': 'Operating Income',
        'NetIncome': 'Net Income',
    }
    
    BALANCE_SHEET_KEYS = {
        'TotalAssets': 'Total Assets',
        'CurrentAssets': 'Current Assets',
        'CashAndCashEquivalents': 'Cash',
        'AccountsReceivable': 'AR',
        'Inventory': 'Inventory',
        'PropertyPlantEquipment': 'PPE',
        'TotalLiabilities': 'Total Liabilities',
        'CurrentLiabilities': 'Current Liabilities',
        'LongTermDebt': 'Long-term Debt',
        'TotalEquity': 'Equity'
    }
    
    CASH_FLOW_KEYS = {
        'OperatingCashFlow': 'Operating CF',
        'CapitalExpenditures': 'CapEx',
        'NetIncome': 'Net Income',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}  # 缓存API结果
    
    def get_ticker_info(self, ticker: str) -> Dict:
        """获取股票基本信息"""
        try:
            url = f"{self.BASE_URL}/v10/finance/quoteSummary/{ticker}"
            params = {'modules': 'summaryProfile,price'}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('quoteSummary', {}).get('result', [{}])[0]
                
                return {
                    'ticker': ticker,
                    'company_name': data.get('summaryProfile', {}).get('longName', ''),
                    'industry': data.get('summaryProfile', {}).get('industry', ''),
                    'market_cap': data.get('price', {}).get('marketCap', {}).get('raw', 0),
                    'current_price': data.get('price', {}).get('currentPrice', {}).get('raw', 0),
                    'shares_outstanding': data.get('price', {}).get('sharesOutstanding', {}).get('raw', 0),
                    'pe_ratio': data.get('summaryDetail', {}).get('trailingPE', {}).get('raw', None),
                }
        except Exception as e:
            print(f"获取 {ticker} 信息失败: {e}")
            return {}
    
    def get_financial_statements(self, ticker: str, statement_type: str = 'income',
                                 freq: str = 'annual') -> pd.DataFrame:
        """获取财务报表数据
        
        Args:
            ticker: 股票代码
            statement_type: 报表类型 ('income', 'balance', 'cashflow')
            freq: 频度 ('annual' 或 'quarterly')
        
        Returns:
            包含财务数据的DataFrame
        """
        try:
            # 构建URL
            if statement_type == 'income':
                url = f"{self.BASE_URL}/v10/finance/quoteSummary/{ticker}"
                module = 'incomeStatementHistory' if freq == 'annual' else 'incomeStatementHistoryQuarterly'
                key_map = self.INCOME_STATEMENT_KEYS
            elif statement_type == 'balance':
                url = f"{self.BASE_URL}/v10/finance/quoteSummary/{ticker}"
                module = 'balanceSheetHistory' if freq == 'annual' else 'balanceSheetHistoryQuarterly'
                key_map = self.BALANCE_SHEET_KEYS
            elif statement_type == 'cashflow':
                url = f"{self.BASE_URL}/v10/finance/quoteSummary/{ticker}"
                module = 'cashflowStatementHistory' if freq == 'annual' else 'cashflowStatementHistoryQuarterly'
                key_map = self.CASH_FLOW_KEYS
            else:
                raise ValueError(f"未知的报表类型: {statement_type}")
            
            params = {'modules': module}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json().get('quoteSummary', {}).get('result', [{}])[0]
                history = result.get(module, {}).get('histories', [])
                
                # 解析数据
                data = []
                for record in history[:5]:  # 只取最近5年
                    row = {
                        'Date': datetime.fromtimestamp(record['endDate']).strftime('%Y-%m-%d')
                    }
                    
                    for yahoo_key, local_key in key_map.items():
                        value = record.get(yahoo_key, {}).get('raw', 0)
                        row[local_key] = value
                    
                    data.append(row)
                
                if data:
                    df = pd.DataFrame(data)
                    df = df.sort_values('Date')
                    return df
                else:
                    return pd.DataFrame()
            
            return pd.DataFrame()
        
        except Exception as e:
            print(f"获取 {ticker} {statement_type} 报表失败: {e}")
            return pd.DataFrame()
    
    def get_all_financial_data(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """获取所有财务数据
        
        Returns: 包含income, balance, cashflow的数据字典
        """
        return {
            'income': self.get_financial_statements(ticker, 'income'),
            'balance': self.get_financial_statements(ticker, 'balance'),
            'cashflow': self.get_financial_statements(ticker, 'cashflow'),
        }
    
    def search_company(self, query: str) -> List[Dict]:
        """搜索公司
        
        Args:
            query: 搜索关键词（股票代码或公司名称）
        
        Returns: 匹配的公司列表
        """
        try:
            url = f"{self.BASE_URL}/v1/finance/search"
            params = {'q': query}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                quotes = response.json().get('quotes', [])
                
                results = []
                for quote in quotes[:10]:  # 返回前10个结果
                    results.append({
                        'ticker': quote.get('symbol', ''),
                        'name': quote.get('longname') or quote.get('shortname', ''),
                        'market_cap': quote.get('marketCap', 0),
                        'industry': quote.get('industry', ''),
                        'type': quote.get('typeDisp', '')
                    })
                
                return results
            
            return []
        
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def get_historical_prices(self, ticker: str, period: str = '5y') -> pd.DataFrame:
        """获取历史股票价格
        
        Args:
            ticker: 股票代码
            period: 时间段 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y')
        
        Returns: 包含日期、开盘价、收盘价等的DataFrame
        """
        try:
            # 使用通用URL格式
            url = "https://query1.finance.yahoo.com/v7/finance/download/" + ticker
            
            # 计算时间范围
            end_date = int(datetime.now().timestamp())
            period_days = {'1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '5y': 1825}
            days = period_days.get(period, 365)
            start_date = int((datetime.now() - timedelta(days=days)).timestamp())
            
            params = {
                'period1': start_date,
                'period2': end_date,
                'interval': '1d',
                'events': 'history'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                data = []
                
                for line in lines[1:]:  # 跳过header
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 6:
                            try:
                                data.append({
                                    'Date': parts[0],
                                    'Open': float(parts[1]),
                                    'High': float(parts[2]),
                                    'Low': float(parts[3]),
                                    'Close': float(parts[4]),
                                    'Volume': float(parts[5]) if parts[5] != 'null' else 0
                                })
                            except:
                                continue
                
                if data:
                    df = pd.DataFrame(data)
                    df['Date'] = pd.to_datetime(df['Date'])
                    return df
            
            return pd.DataFrame()
        
        except Exception as e:
            print(f"获取历史价格失败: {e}")
            return pd.DataFrame()


class DataCleaner:
    """财务数据清洗和标准化"""
    
    @staticmethod
    def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
        """清洗财务数据
        
        处理：
        - 缺失值
        - 异常值
        - 数据标准化
        """
        df = df.copy()
        
        # 处理缺失值
        df = df.fillna(method='ffill')  # 向前填充
        
        # 移除负数收入（异常）
        if 'Revenue' in df.columns:
            df = df[df['Revenue'] > 0]
        
        # 数据标准化 - 确保数值列是数值类型
        for col in df.columns:
            if col != 'Date':
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    pass
        
        return df
    
    @staticmethod
    def calculate_growth_rates(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """计算增长率"""
        df = df.copy()
        
        if columns is None:
            columns = [col for col in df.columns if col != 'Date']
        
        for col in columns:
            if col in df.columns:
                df[f'{col}_Growth'] = df[col].pct_change()
        
        return df
    
    @staticmethod
    def fill_missing_years(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
        """填补缺失的年份数据（线性插值）"""
        if 'Date' not in df.columns:
            return df
        
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df = df.asfreq('YS').interpolate()  # 按年度频率插值
        df = df.reset_index()
        
        return df


if __name__ == "__main__":
    # 测试
    yf = YahooFinanceAPI()
    
    # 搜索公司
    print("=== 搜索 Microsoft ===")
    results = yf.search_company("Microsoft")
    for r in results[:3]:
        print(f"  {r['ticker']}: {r['name']}")
    
    # 获取财务数据
    print("\n=== 获取 MSFT 财务数据 ===")
    ticker = "MSFT"
    
    # 获取基本信息
    info = yf.get_ticker_info(ticker)
    print(f"公司: {info.get('company_name', '')}")
    print(f"当前股价: ${info.get('current_price', 0):.2f}")
    
    # 获取财务报表
    income = yf.get_financial_statements(ticker, 'income')
    if not income.empty:
        print("\n损益表 (最近数据):")
        print(income.head(2))
    else:
        print("\n无法获取损益表数据")
    
    # 获取历史价格
    prices = yf.get_historical_prices(ticker, '1y')
    if not prices.empty:
        print(f"\n历史价格 (最后3行):")
        print(prices.tail(3))
