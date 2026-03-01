/**
 * React应用入口
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// 配置Ant Design主题
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <ConfigProvider locale={zhCN}>
    <App />
  </ConfigProvider>
);
