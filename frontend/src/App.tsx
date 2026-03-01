/**
 * 主应用程序
 */

import React, { useEffect } from 'react';
import { Layout, Tabs, Card, Empty, Spin, Alert, Space, Button, Modal } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import styles from './App.module.css';
import { useAnalysisStore } from './services/store';
import { InputModule } from './modules/input/InputModule';
import { FinancialStatementsModule } from './modules/financial/FinancialStatementsModule';
import { DCFValuationModule } from './modules/valuation/DCFValuationModule';
import { VisualizationModule } from './modules/visualization/VisualizationModule';

const { Header, Content, Footer } = Layout;

const App: React.FC = () => {
  const {
    activeTab,
    loading,
    error,
    ticker,
    financialModel,
    dcfValuation,
    setActiveTab,
    reset,
  } = useAnalysisStore();

  const handleTabChange = (key: string) => {
    setActiveTab(key as any);
  };

  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      content: '是否确认清空所有数据并开始新分析？',
      okText: '确认',
      cancelText: '取消',
      onOk() {
        reset();
      },
    });
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <h1>📊 财务分析平台</h1>
            <p>三表财务模型 & DCF估值</p>
          </div>
          <div className={styles.headerActions}>
            {ticker && (
              <Space>
                <span className={styles.tickerBadge}>{ticker}</span>
                <Button
                  type="primary"
                  danger
                  onClick={handleReset}
                  disabled={loading}
                >
                  重新开始
                </Button>
              </Space>
            )}
          </div>
        </div>
      </Header>

      {/* 主内容区域 */}
      <Content className={styles.content}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
          {/* 错误提示 */}
          {error && (
            <Alert
              type="error"
              message="错误"
              description={error}
              closable
              style={{ marginBottom: '24px' }}
            />
          )}

          {/* 加载状态 */}
          {loading && (
            <Card style={{ textAlign: 'center', marginBottom: '24px' }}>
              <Spin size="large" tip="分析中..." />
            </Card>
          )}

          {/* 标签页内容 */}
          {!ticker ? (
            <InputModule />
          ) : (
            <Tabs
              activeKey={activeTab}
              onChange={handleTabChange}
              type="card"
              style={{ backgroundColor: 'white', borderRadius: '8px' }}
              items={[
                {
                  key: 'input',
                  label: '📝 输入参数',
                  children: <InputModule />,
                },
                {
                  key: 'financial',
                  label: '📈 财务报表',
                  children: financialModel ? (
                    <FinancialStatementsModule />
                  ) : (
                    <Empty description="请先运行分析" />
                  ),
                },
                {
                  key: 'valuation',
                  label: '💰 DCF估值',
                  children: dcfValuation ? (
                    <DCFValuationModule />
                  ) : (
                    <Empty description="请先运行分析" />
                  ),
                },
                {
                  key: 'visualization',
                  label: '📊 数据可视化',
                  children: financialModel || dcfValuation ? (
                    <VisualizationModule />
                  ) : (
                    <Empty description="请先运行分析" />
                  ),
                },
              ]}
            />
          )}
        </div>
      </Content>

      {/* 页脚 */}
      <Footer className={styles.footer}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p>
            💡 基于<strong>FAST标准</strong>的模块化财务模型 | {' '}
            参考: <a href="https://beefed.ai/zh/modular-3-statement-financial-model" target="_blank" rel="noopener noreferrer">
              beefed.ai 模块化三表财务模型
            </a>
          </p>
          <p style={{ fontSize: '12px', color: '#999' }}>
            ⚠️ 免责声明：本平台仅供学习和参考使用，不构成投资建议。使用者需自行承担投资风险。
          </p>
        </div>
      </Footer>
    </Layout>
  );
};

export default App;
