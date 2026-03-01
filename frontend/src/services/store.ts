/**
 * 应用状态管理（使用Zustand）
 */

import { create } from 'zustand';
import { api, Assumptions } from './api';

interface AnalysisState {
  // 输入状态
  ticker: string;
  companyName: string;
  sharesOutstanding: number;
  currentStockPrice?: number;
  
  // 假设状态
  assumptions: Assumptions | null;
  scenario: 'base' | 'bull' | 'bear' | 'custom';
  projectionYears: number;
  
  // 计算结果
  financialModel: any;
  dcfValuation: any;
  sensivityAnalysis: any;
  
  // UI状态
  loading: boolean;
  error: string | null;
  activeTab: 'input' | 'financial' | 'valuation' | 'sensitivity';
  
  // 操作方法
  setTicker: (ticker: string) => void;
  setCompanyName: (name: string) => void;
  setSharesOutstanding: (shares: number) => void;
  setCurrentStockPrice: (price: number) => void;
  setAssumptions: (assumptions: Assumptions) => void;
  setScenario: (scenario: string) => void;
  setProjectionYears: (years: number) => void;
  setActiveTab: (tab: 'input' | 'financial' | 'valuation' | 'sensitivity') => void;
  
  // 异步操作
  searchCompany: (query: string) => Promise<any[]>;
  getCompanyInfo: (ticker: string) => Promise<any>;
  runAnalysis: (ticker: string) => Promise<void>;
  
  // 重置状态
  reset: () => void;
}

const defaultAssumptions: Assumptions = {
  revenue_growth_rates: { 1: 0.08, 2: 0.07, 3: 0.06, 4: 0.05, 5: 0.03 },
  cogs_pct_revenue: 0.35,
  opex_pct_revenue: 0.20,
  capex_pct_revenue: 0.05,
  tax_rate: 0.25,
  ar_days: 45,
  inventory_days: 30,
  ap_days: 30,
  wacc: 0.08,
  terminal_growth_rate: 0.03,
  risk_free_rate: 0.03,
  market_risk_premium: 0.07,
  beta: 1.0,
};

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // 初始状态
  ticker: '',
  companyName: '',
  sharesOutstanding: 100000000,
  currentStockPrice: undefined,
  assumptions: defaultAssumptions,
  scenario: 'base',
  projectionYears: 5,
  
  financialModel: null,
  dcfValuation: null,
  sensivityAnalysis: null,
  
  loading: false,
  error: null,
  activeTab: 'input',
  
  // 简单状态更新
  setTicker: (ticker: string) => set({ ticker }),
  setCompanyName: (companyName: string) => set({ companyName }),
  setSharesOutstanding: (sharesOutstanding: number) => set({ sharesOutstanding }),
  setCurrentStockPrice: (currentStockPrice: number) => set({ currentStockPrice }),
  setAssumptions: (assumptions: Assumptions) => set({ assumptions }),
  setScenario: (scenario: string) => set({ 
    scenario: scenario as 'base' | 'bull' | 'bear' | 'custom' 
  }),
  setProjectionYears: (projectionYears: number) => set({ projectionYears }),
  setActiveTab: (activeTab) => set({ activeTab }),
  
  // 搜索公司
  searchCompany: async (query: string) => {
    set({ loading: true, error: null });
    try {
      const results = await api.searchCompany(query);
      return results;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '搜索失败';
      set({ error: errorMsg, loading: false });
      return [];
    }
  },
  
  // 获取公司信息
  getCompanyInfo: async (ticker: string) => {
    set({ loading: true, error: null });
    try {
      const info = await api.getCompanyInfo(ticker);
      return info;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '获取公司信息失败';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },
  
  // 运行完整分析
  runAnalysis: async (ticker: string) => {
    set({ loading: true, error: null });
    try {
      const state = get();
      const assumptions = state.assumptions || defaultAssumptions;
      
      // 运行财务模型
      const financialModel = await api.runFinancialModel(
        ticker,
        assumptions,
        state.scenario,
        state.projectionYears
      );
      
      // 运行DCF估值
      const dcfValuation = await api.runDCFValuation(
        ticker,
        assumptions,
        state.sharesOutstanding,
        state.currentStockPrice,
        state.scenario
      );
      
      set({
        ticker,
        financialModel,
        dcfValuation,
        loading: false,
        activeTab: 'financial',
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '分析失败';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },
  
  // 重置状态
  reset: () => set({
    ticker: '',
    companyName: '',
    sharesOutstanding: 100000000,
    currentStockPrice: undefined,
    assumptions: defaultAssumptions,
    scenario: 'base',
    projectionYears: 5,
    financialModel: null,
    dcfValuation: null,
    sensivityAnalysis: null,
    error: null,
    activeTab: 'input',
  }),
}));
