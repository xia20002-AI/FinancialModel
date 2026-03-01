/**
 * 输入模块 - 用户输入股票代码和财务假设
 */

import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Row,
  Col,
  Tabs,
  Table,
  Select,
  InputNumber,
  AutoComplete,
  Space,
  Divider,
  Alert,
  Collapse,
  Statistic,
} from 'antd';
import { SearchOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useAnalysisStore } from '../../services/store';
import { api, SearchResult } from '../../services/api';

export const InputModule: React.FC = () => {
  const [form] = Form.useForm();
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<SearchResult | null>(null);

  const {
    ticker,
    assumptions,
    scenario,
    projectionYears,
    sharesOutstanding,
    currentStockPrice,
    loading,
    setTicker,
    setCompanyName,
    setSharesOutstanding,
    setCurrentStockPrice,
    setAssumptions,
    setScenario,
    setProjectionYears,
    searchCompany,
    runAnalysis,
  } = useAnalysisStore();

  // 搜索公司
  const handleSearchCompany = async (value: string) => {
    if (!value) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const results = await searchCompany(value);
      setSearchResults(results);
    } finally {
      setSearchLoading(false);
    }
  };

  // 选择公司
  const handleSelectCompany = (result: SearchResult) => {
    setSelectedCompany(result);
    setTicker(result.ticker);
    setCompanyName(result.name);
    form.setFieldValue('ticker', result.ticker);
  };

  // 运行分析
  const handleRunAnalysis = async () => {
    const values = await form.validateFields();
    if (!ticker) {
      alert('请先选择公司');
      return;
    }

    try {
      await runAnalysis(ticker);
    } catch (error) {
      console.error('分析失败:', error);
    }
  };

  // 初始化表单
  useEffect(() => {
    if (assumptions) {
      form.setFieldsValue({
        ...assumptions,
        // 展平嵌套的增长率
        revenue_growth_y1: assumptions.revenue_growth_rates[1],
        revenue_growth_y2: assumptions.revenue_growth_rates[2],
        revenue_growth_y3: assumptions.revenue_growth_rates[3],
        revenue_growth_y4: assumptions.revenue_growth_rates[4],
        revenue_growth_y5: assumptions.revenue_growth_rates[5],
      });
    }
  }, [assumptions, form]);

  // 更新假设
  const handleFormChange = (changedValues: any) => {
    if (assumptions) {
      const revenue_growth_rates = {
        1: changedValues.revenue_growth_y1 || assumptions.revenue_growth_rates[1],
        2: changedValues.revenue_growth_y2 || assumptions.revenue_growth_rates[2],
        3: changedValues.revenue_growth_y3 || assumptions.revenue_growth_rates[3],
        4: changedValues.revenue_growth_y4 || assumptions.revenue_growth_rates[4],
        5: changedValues.revenue_growth_y5 || assumptions.revenue_growth_rates[5],
      };

      const newAssumptions = {
        ...assumptions,
        ...changedValues,
        revenue_growth_rates,
      };

      setAssumptions(newAssumptions);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        {/* 左侧：股票搜索和公司信息 */}
        <Col xs={24} lg={8}>
          <Card
            title="🔍 股票搜索"
            extra={<SearchOutlined />}
            style={{ marginBottom: '24px' }}
          >
            <Form layout="vertical" form={form} onValuesChange={handleFormChange}>
              <Form.Item label="搜索公司" name="search">
                <AutoComplete
                  placeholder="输入股票代码或公司名称 (如: MSFT, Apple)"
                  options={searchResults.map(r => ({
                    value: r.ticker,
                    label: `${r.ticker} - ${r.name}`,
                  }))}
                  onSearch={handleSearchCompany}
                  loading={searchLoading}
                  onSelect={(value) => {
                    const result = searchResults.find(r => r.ticker === value);
                    if (result) {
                      handleSelectCompany(result);
                    }
                  }}
                />
              </Form.Item>

              {selectedCompany && (
                <>
                  <Divider />
                  <Form.Item label="股票代码">
                    <Input value={selectedCompany.ticker} disabled />
                  </Form.Item>
                  <Form.Item label="公司名称">
                    <Input value={selectedCompany.name} disabled />
                  </Form.Item>
                  {selectedCompany.industry && (
                    <Form.Item label="行业">
                      <Input value={selectedCompany.industry} disabled />
                    </Form.Item>
                  )}
                </>
              )}
            </Form>
          </Card>

          {/* 估值参数 */}
          <Card title="💰 估值参数">
            <Form layout="vertical" form={form} onValuesChange={handleFormChange}>
              <Form.Item
                label="发行在外股份数 (百万)"
                name="shares_outstanding"
              >
                <InputNumber
                  value={sharesOutstanding / 1000000}
                  onChange={(val) => {
                    if (val) {
                      setSharesOutstanding(val * 1000000);
                    }
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item label="当前股价" name="current_stock_price">
                <InputNumber
                  prefix="$"
                  placeholder="可选"
                  onChange={setCurrentStockPrice}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item label="分析场景" name="scenario">
                <Select
                  value={scenario}
                  onChange={setScenario}
                  options={[
                    { label: '基准情景', value: 'base' },
                    { label: '乐观情景', value: 'bull' },
                    { label: '悲观情景', value: 'bear' },
                    { label: '自定义', value: 'custom' },
                  ]}
                />
              </Form.Item>

              <Form.Item label="预测年数" name="projection_years">
                <InputNumber
                  min={3}
                  max={10}
                  value={projectionYears}
                  onChange={setProjectionYears}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：财务假设 */}
        <Col xs={24} lg={16}>
          <Form layout="vertical" form={form} onValuesChange={handleFormChange}>
            <Collapse
              defaultActiveKey={['1', '2', '3']}
              items={[
                {
                  key: '1',
                  label: '📊 收入驱动 (Revenue Drivers)',
                  children: (
                    <Row gutter={16}>
                      {[1, 2, 3, 4, 5].map(year => (
                        <Col xs={12} sm={8} key={year}>
                          <Form.Item
                            label={`第${year}年增长率`}
                            name={`revenue_growth_y${year}`}
                          >
                            <InputNumber
                              min={-1}
                              max={1}
                              step={0.01}
                              formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                              parser={value =>
                                Number(value?.replace('%', '')) / 100
                              }
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                      ))}
                    </Row>
                  ),
                },
                {
                  key: '2',
                  label: '💸 成本结构 (Cost Structure)',
                  children: (
                    <Row gutter={16}>
                      <Col xs={12} sm={8}>
                        <Form.Item
                          label="COGS占收入比例"
                          name="cogs_pct_revenue"
                        >
                          <InputNumber
                            min={0}
                            max={1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={12} sm={8}>
                        <Form.Item
                          label="OpEx占收入比例"
                          name="opex_pct_revenue"
                        >
                          <InputNumber
                            min={0}
                            max={1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={12} sm={8}>
                        <Form.Item
                          label="CapEx占收入比例"
                          name="capex_pct_revenue"
                        >
                          <InputNumber
                            min={0}
                            max={1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                  ),
                },
                {
                  key: '3',
                  label: '🏦 融资和估值 (Financing & Valuation)',
                  children: (
                    <Row gutter={16}>
                      <Col xs={12} sm={8}>
                        <Form.Item label="所得税率" name="tax_rate">
                          <InputNumber
                            min={0}
                            max={1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={12} sm={8}>
                        <Form.Item label="WACC (折现率)" name="wacc">
                          <InputNumber
                            min={0}
                            max={1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={12} sm={8}>
                        <Form.Item
                          label="终端增长率"
                          name="terminal_growth_rate"
                        >
                          <InputNumber
                            min={0}
                            max={0.1}
                            step={0.01}
                            formatter={value => `${(Number(value) * 100).toFixed(1)}%`}
                            parser={value =>
                              Number(value?.replace('%', '')) / 100
                            }
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                  ),
                },
              ]}
            />
          </Form>

          {/* 运行分析按钮 */}
          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            {!ticker && (
              <Alert
                type="info"
                message="请先选择要分析的公司"
                style={{ marginBottom: '16px' }}
              />
            )}
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleRunAnalysis}
              disabled={!ticker || loading}
              loading={loading}
              style={{ minWidth: '200px' }}
            >
              {loading ? '分析中...' : '运行财务模型 & DCF估值'}
            </Button>
          </div>
        </Col>
      </Row>
    </div>
  );
};
