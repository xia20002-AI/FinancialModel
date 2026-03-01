/**
 * Express后端服务器 - 作为中间层
 * 主要作用：与前端通信、调用Python财务引擎、处理缓存等
 */

import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import axios from 'axios';
import { createProxyMiddleware } from 'express-http-proxy';
import path from 'path';

const app: Express = express();
const PORT = process.env.PORT || 3000;
const PYTHON_API = process.env.PYTHON_API || 'http://localhost:8000';

// 中间件
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// 日志中间件
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${new Date().toISOString()} ${req.method} ${req.path} ${res.statusCode} ${duration}ms`);
  });
  next();
});

// ============ API 路由 ============

/**
 * 代理 - 直接转发到Python FastAPI
 * 所有对/api/的请求都转发到Python服务器
 */
app.use(
  '/api',
  createProxyMiddleware({
    target: PYTHON_API,
    changeOrigin: true,
    pathRewrite: {
      '^/api': '', // 移除/api前缀
    },
    onError: (err, req, res) => {
      console.error('Proxy error:', err);
      res.status(503).json({
        error: 'Python服务不可用',
        details: err.message,
      });
    },
  })
);

/**
 * 健康检查
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    python_api: PYTHON_API,
  });
});

/**
 * 根路径
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    message: '财务分析平台后端服务',
    version: '1.0.0',
    api_docs: 'http://localhost:8000/docs',
    frontend: 'http://localhost:3000',
  });
});

// ============ 错误处理 ============

app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    error: '服务器错误',
    message: err.message,
  });
});

// ============ 启动服务器 ============

app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════╗
║  财务分析平台后端服务已启动           ║
╠════════════════════════════════════════╣
║  服务器: http://localhost:${PORT}                  ║
║  Python API: ${PYTHON_API}           ║
║  健康检查: http://localhost:${PORT}/health        ║
╚════════════════════════════════════════╝
  `);
});

export default app;
