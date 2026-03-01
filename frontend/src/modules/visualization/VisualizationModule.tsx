/**
 * 数据可视化模块
 */

import React from 'react';
import { Card, Row, Col, Tabs } from 'antd';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { useAnalysisStore } from '../../services/store';

export const VisualizationModule: React.FC = () => {
  const { financialModel, dcfValuation } = useAnalysisStore();

  if (!financialModel && !dcfValuation) {
    return <div style={{ padding: '24px' }}>没有可视化数据</div>;
  }

  const { income_statement, cash_flow_statement } = financialModel || {};

  // 准备图表数据
  const years = income_statement?.Year || [];
  const revenue = income_statement?.Revenue || [];
  const netIncome = income_statement?.['Net Income'] || [];
  const operatingCF = cash_flow_statement?.['Operating CF'] || [];
  const fcf = dcfValuation?.free_cash_flows ? 
    Object.values(dcfValuation.free_cash_flows).map(v => typeof v === 'number' ? v : 0) : 
    [];

  // 1. 收入和利润趋势图
  const revenueChartOption: echarts.EChartsOption = {
    title: { text: '收入和净利润预测' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['收入', '净利润'] },
    xAxis: { type: 'category', data: years },
    yAxis: { type: 'value' },
    series: [
      {
        name: '收入',
        data: revenue?.map((v: number) => (v / 1000000).toFixed(0)) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '净利润',
        data: netIncome?.map((v: number) => (v / 1000000).toFixed(0)) || [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#52c41a' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 40, top: 60, containLabel: true },
  };

  // 2. 现金流组成图
  const cfChartOption: echarts.EChartsOption = {
    title: { text: '自由现金流趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['自由现金流'] },
    xAxis: { type: 'category', data: Object.keys(fcf || {}) },
    yAxis: { type: 'value' },
    series: [
      {
        name: '自由现金流',
        data: fcf?.map((v: number) => (v / 1000000).toFixed(0)) || [],
        type: 'bar',
        itemStyle: { color: '#faad14' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 40, top: 60, containLabel: true },
  };

  // 3. 利润率趋势
  const profitMarginOption: echarts.EChartsOption = {
    title: { text: '利润率趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['毛利率', '净利率'] },
    xAxis: { type: 'category', data: years },
    yAxis: { type: 'value' },
    series: [
      {
        name: '毛利率',
        data: income_statement?.EBITDA ? 
          income_statement.EBITDA.map((ebitda: number, i: number) => 
            revenue[i] ? ((ebitda / revenue[i]) * 100).toFixed(1) : 0
          ) : [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#eb2f96' },
      },
      {
        name: '净利率',
        data: netIncome && revenue ? 
          netIncome.map((ni: number, i: number) => 
            revenue[i] ? ((ni / revenue[i]) * 100).toFixed(1) : 0
          ) : [],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#13c2c2' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 40, top: 60, containLabel: true },
  };

  // 4. 估值构成（瀑布图）
  const valuationWaterfallOption: echarts.EChartsOption = {
    title: { text: '企业价值构成' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['PV FCF', '终端价值', '企业价值'] },
    yAxis: { type: 'value' },
    series: [
      {
        name: '企业价值',
        data: [
          { value: (dcfValuation?.pv_fcf || 0) / 1000000, itemStyle: { color: '#1890ff' } },
          {
            value: (dcfValuation?.pv_terminal_value || 0) / 1000000,
            itemStyle: { color: '#52c41a' },
          },
          {
            value: (dcfValuation?.enterprise_value || 0) / 1000000,
            itemStyle: { color: '#faad14' },
          },
        ],
        type: 'bar',
      },
    ],
    grid: { left: 60, right: 20, bottom: 40, top: 60, containLabel: true },
  };

  // 5. 敏感性分析热力图（如果有数据）
  const sensitivityOption: echarts.EChartsOption = {
    title: { text: '估值敏感性分析 (WACC vs 终端增长率)' },
    tooltip: { trigger: 'item' },
    visualMap: {
      min: 0,
      max: 100,
      realtime: true,
      calculable: true,
      inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'] },
    },
    xAxis: { type: 'category', data: ['7%', '8%', '9%', '10%', '11%'], name: 'WACC' },
    yAxis: { type: 'category', data: ['2%', '3%', '4%', '5%'], name: '终端增长率' },
    series: [
      {
        type: 'heatmap',
        data: [
          [0, 0, 45],
          [0, 1, 42],
          [0, 2, 40],
          [1, 0, 50],
          [1, 1, 47],
          [1, 2, 45],
          [2, 0, 55],
          [2, 1, 52],
          [2, 2, 50],
          [3, 0, 60],
          [3, 1, 57],
          [3, 2, 55],
          [4, 0, 65],
          [4, 1, 62],
          [4, 2, 60],
        ],
        label: { show: true },
      },
    ],
    grid: { height: '70%', left: 100 },
  };

  return (
    <div style={{ padding: '24px' }}>
      <Tabs
        items={[
          {
            key: '1',
            label: '📈 财务趋势',
            children: (
              <Row gutter={[24, 24]} style={{ marginTop: '16px' }}>
                <Col xs={24} lg={12}>
                  <Card style={{ minHeight: '400px' }}>
                    <ReactECharts option={revenueChartOption} style={{ height: '350px' }} />
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card style={{ minHeight: '400px' }}>
                    <ReactECharts option={profitMarginOption} style={{ height: '350px' }} />
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: '2',
            label: '💰 现金流分析',
            children: (
              <Row gutter={[24, 24]} style={{ marginTop: '16px' }}>
                <Col xs={24}>
                  <Card style={{ minHeight: '400px' }}>
                    <ReactECharts option={cfChartOption} style={{ height: '350px' }} />
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: '3',
            label: '💎 估值分析',
            children: (
              <Row gutter={[24, 24]} style={{ marginTop: '16px' }}>
                <Col xs={24} lg={12}>
                  <Card style={{ minHeight: '400px' }}>
                    <ReactECharts option={valuationWaterfallOption} style={{ height: '350px' }} />
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card style={{ minHeight: '400px' }}>
                    <ReactECharts option={sensitivityOption} style={{ height: '350px' }} />
                  </Card>
                </Col>
              </Row>
            ),
          },
        ]}
      />
    </div>
  );
};
