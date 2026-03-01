/**
 * API 服务层
 * 所有对后端API的调用都通过这一层
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface SearchResult {
  ticker: string;
  name: string;
  industry?: string;
  market_cap?: number;
  type?: string;
}

interface FinancialModel {
  ticker: string;
  company_name: string;
  income_statement: any;
  balance_sheet: any;
  cash_flow_statement: any;
  kpis: { [key: string]: number };
  validation: { [key: string]: boolean };
  timestamp: string;
}

interface DCFValuation {
  ticker: string;
  company_name: string;
  valuation_date: string;
  
  // WACC
  wacc: number;
  wacc_details: {
    cost_of_equity: number;
    cost_of_debt: number;
    tax_rate: number;
    equity_weight: number;
    debt_weight: number;
  };
  
  // 现金流信息
  free_cash_flows: { [year: number]: number };
  pv_fcf: number;
  
  // 终端价值
  terminal_value: number;
  terminal_growth_rate: number;
  pv_terminal_value: number;
  
  // 估值结果
  enterprise_value: number;
  net_debt: number;
  equity_value: number;
  shares_outstanding: number;
  intrinsic_value_per_share: number;
  
  // 当前股价对比
  current_stock_price?: number;
  upside_downside?: number;
  upside_downside_pct?: number;
  
  // 投资建议
  recommendation: string;
}

interface Assumptions {
  revenue_growth_rates: { [year: number]: number };
  cogs_pct_revenue: number;
  opex_pct_revenue: number;
  capex_pct_revenue: number;
  tax_rate: number;
  ar_days: number;
  inventory_days: number;
  ap_days: number;
  wacc: number;
  terminal_growth_rate: number;
  risk_free_rate: number;
  market_risk_premium: number;
  beta: number;
}

class FinancialAnalysisAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 错误处理中间件
    this.client.interceptors.response.use(
      response => response,
      error => {
        console.error('API错误:', error);
        throw error;
      }
    );
  }

  /**
   * 获取健康状况
   */
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * 搜索公司
   */
  async searchCompany(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await this.client.get<SearchResult[]>('/search', {
      params: { q: query, limit },
    });
    return response.data;
  }

  /**
   * 获取公司信息
   */
  async getCompanyInfo(ticker: string): Promise<any> {
    const response = await this.client.get(`/company/${ticker}`);
    return response.data;
  }

  /**
   * 运行财务模型
   */
  async runFinancialModel(
    ticker: string,
    assumptions: Assumptions,
    scenario: string = 'base',
    projectionYears: number = 5
  ): Promise<any> {
    const response = await this.client.post('/financial-model', {
      ticker,
      assumptions,
      scenario,
      projection_years: projectionYears,
    });
    return response.data;
  }

  /**
   * 运行DCF估值
   */
  async runDCFValuation(
    ticker: string,
    assumptions: Assumptions,
    sharesOutstanding: number,
    currentStockPrice?: number,
    scenario: string = 'base'
  ): Promise<any> {
    const response = await this.client.post('/dcf-valuation', {
      ticker,
      assumptions,
      shares_outstanding: sharesOutstanding,
      current_stock_price: currentStockPrice,
      scenario,
    });
    return response.data;
  }

  /**
   * 获取场景模板
   */
  async getScenarioTemplates(): Promise<any> {
    const response = await this.client.get('/scenario-templates');
    return response.data;
  }

  /**
   * 获取假设指南
   */
  async getAssumptionsGuide(): Promise<any> {
    const response = await this.client.get('/docs/assumptions');
    return response.data;
  }
}

// 导出单例
export const api = new FinancialAnalysisAPI();
export type { SearchResult, FinancialModel, DCFValuation, Assumptions };
