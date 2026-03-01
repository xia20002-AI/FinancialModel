/**
 * 财务报表展示模块
 */

import React from 'react';
import { Card, Table, Row, Col, Divider, Statistic, Empty, Tabs } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useAnalysisStore } from '../../services/store';

export const FinancialStatementsModule: React.FC = () => {
  const { financialModel } = useAnalysisStore();

  if (!financialModel) {
    return <Empty description="没有数据" />;
  }

  const { income_statement, balance_sheet, cash_flow_statement, kpis } =
    financialModel;

  // 转换为表格数据
  const incomeData = Object.entries(income_statement || {}).reduce(
    (acc: any[], [key, value]: [string, any]) => {
      if (
        key !== 'Year' &&
        Array.isArray(value) &&
        typeof value[0] === 'number'
      ) {
        acc.push({
          key: key,
          name: key,
          ...value.reduce((obj: any, v: any, i: number) => {
            obj[`year${i + 1}`] = v;
            return obj;
          }, {}),
        });
      }
      return acc;
    },
    []
  );

  const years = income_statement['Year'] || [];
  const columns = [
    { title: '项目', dataIndex: 'name', key: 'name', frozen: true },
    ...years.map((year: number, i: number) => ({
      title: `Year ${year}`,
      dataIndex: `year${i + 1}`,
      key: `year${i + 1}`,
      render: (value: number) => {
        if (value === undefined) return '-';
        return (
          <span>
            {(value / 1000000).toFixed(0)}
            <span style={{ color: '#999', fontSize: '12px' }}>M</span>
          </span>
        );
      },
    })),
  ];

  // KPI指标数据
  const kpiEntries = Object.entries(kpis || {}).filter(([key]) =>
    key.includes('Y1')
  );

  return (
    <div style={{ padding: '24px' }}>
      <Tabs
        items={[
          {
            key: '1',
            label: '📊 损益表 (Income Statement)',
            children: (
              <Card style={{ marginTop: '16px' }}>
                <Table
                  dataSource={incomeData}
                  columns={columns}
                  pagination={false}
                  scroll={{ x: true }}
                  size="small"
                />
              </Card>
            ),
          },
          {
            key: '2',
            label: '🏦 资产负债表 (Balance Sheet)',
            children: (
              <Card style={{ marginTop: '16px' }}>
                <Table
                  dataSource={(() => {
                    const bsData = Object.entries(balance_sheet || {}).reduce(
                      (acc: any[], [key, value]: [string, any]) => {
                        if (
                          key !== 'Year' &&
                          Array.isArray(value) &&
                          typeof value[0] === 'number'
                        ) {
                          acc.push({
                            key: key,
                            name: key,
                            ...value.reduce((obj: any, v: any, i: number) => {
                              obj[`year${i + 1}`] = v;
                              return obj;
                            }, {}),
                          });
                        }
                        return acc;
                      },
                      []
                    );
                    return bsData;
                  })()}
                  columns={columns}
                  pagination={false}
                  scroll={{ x: true }}
                  size="small"
                />
              </Card>
            ),
          },
          {
            key: '3',
            label: '💵 现金流量表 (Cash Flow Statement)',
            children: (
              <Card style={{ marginTop: '16px' }}>
                <Table
                  dataSource={(() => {
                    const cfData = Object.entries(
                      cash_flow_statement || {}
                    ).reduce((acc: any[], [key, value]: [string, any]) => {
                      if (
                        key !== 'Year' &&
                        Array.isArray(value) &&
                        typeof value[0] === 'number'
                      ) {
                        acc.push({
                          key: key,
                          name: key,
                          ...value.reduce((obj: any, v: any, i: number) => {
                            obj[`year${i + 1}`] = v;
                            return obj;
                          }, {}),
                        });
                      }
                      return acc;
                    }, []);
                    return cfData;
                  })()}
                  columns={columns}
                  pagination={false}
                  scroll={{ x: true }}
                  size="small"
                />
              </Card>
            ),
          },
        ]}
      />

      {/* KPI指标 */}
      <Divider />
      <h3>关键绩效指标 (KPIs) - 第1年</h3>
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        {kpiEntries.map(([key, value]) => (
          <Col xs={24} sm={12} md={8} lg={6} key={key}>
            <Card style={{ textAlign: 'center' }}>
              <Statistic
                title={key.replace('_Y1', '')}
                value={typeof value === 'number' ? value : 0}
                precision={2}
                suffix={typeof value === 'number' && Math.abs(value) < 1 ? '%' : ''}
                valueStyle={{
                  color: typeof value === 'number' && value > 0 ? '#3f8600' : '#cf1322',
                  fontSize: '14px',
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};
