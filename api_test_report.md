# API 接口测试报告

**测试时间**: 2026-04-29 15:33:30  
**测试地址**: http://127.0.0.1:8000  
**后端版本**: backend-new (2026-04-29)

## 汇总

| 指标 | 数量 | 占比 |
|------|------|------|
| 总计 | 52 | 100% |
| ✅ 通过 | 43 | 82.7% |
| ⚠️ 需认证 | 9 | 17.3% |
| ❌ 失败 | 0 | 0.0% |

## 详细结果

| 接口描述 | 路径 | 方法 | 状态码 | 结果 |
|----------|------|------|--------|------|
| 健康检查 | `/api/health/` | GET | 200 | ✅ 通过 |
| Swagger UI | `/swagger/` | GET | 200 | ✅ 通过 |
| Redoc 文档 | `/redoc/` | GET | 200 | ✅ 通过 |
| OpenAPI Schema | `/api/schema/` | GET | 200 | ✅ 通过 |
| Demo登录 | `/api/auth/login` | POST | 200 | ✅ 通过 |
| Demo注册 | `/api/auth/register` | POST | 200 | ✅ 通过 |
| Demo获取当前用户 | `/api/auth/me` | GET | 200 | ✅ 通过 |
| Demo刷新Token | `/api/auth/refresh` | POST | 200 | ✅ 通过 |
| Demo发送短信 | `/api/auth/send-sms` | POST | 200 | ✅ 通过 |
| Demo验证短信 | `/api/auth/verify-sms` | POST | 200 | ✅ 通过 |
| Demo商品列表 | `/api/v1/goods/list` | GET | 200 | ✅ 通过 |
| Demo商品详情 | `/api/v1/goods/detail/1/` | GET | 200 | ✅ 通过 |
| Demo产品列表 | `/api/v1/products/` | GET | 200 | ✅ 通过 |
| Demo商品上架 | `/api/v1/goods/listing/` | POST | 200 | ✅ 通过 |
| Demo批量上架 | `/api/v1/goods/listing/batch/` | POST | 200 | ✅ 通过 |
| Demo采集1688单商品 | `/api/v1/collect/1688/single/` | POST | 200 | ✅ 通过 |
| Demo采集1688批量 | `/api/v1/collect/1688/batch/` | POST | 200 | ✅ 通过 |
| Demo创建采集任务 | `/api/v1/collect/task/` | POST | 200 | ✅ 通过 |
| Demo采集任务列表 | `/api/v1/collect/task/list/` | GET | 200 | ✅ 通过 |
| Demo采集授权状态 | `/api/v1/collect/1688/auth/status/` | GET | 200 | ✅ 通过 |
| Demo订单列表 | `/api/v1/orders/` | GET | 200 | ✅ 通过 |
| Demo订单统计 | `/api/v1/orders/stats/` | GET | 200 | ✅ 通过 |
| Demo订单详情 | `/api/v1/orders/1/` | GET | 200 | ✅ 通过 |
| Demo取消订单 | `/api/v1/orders/1/cancel/` | POST | 200 | ✅ 通过 |
| Demo库存列表 | `/api/v1/inventory/list/` | GET | 200 | ✅ 通过 |
| Demo库存预警 | `/api/v1/inventory/alerts/` | GET | 200 | ✅ 通过 |
| DemoSKU库存 | `/api/v1/inventory/sku/SKU001/` | GET | 200 | ✅ 通过 |
| Demo库存概览 | `/api/v1/inventory/overview/` | GET | 200 | ✅ 通过 |
| Demo仓库列表 | `/api/v1/inventory/warehouses/` | GET | 200 | ✅ 通过 |
| Demo库存日志 | `/api/v1/inventory/logs/` | GET | 200 | ✅ 通过 |
| Demo库存调整 | `/api/v1/inventory/adjust/` | POST | 200 | ✅ 通过 |
| Demo物流发货 | `/api/v1/logistics/shipments/` | GET | 200 | ✅ 通过 |
| Demo物流统计 | `/api/v1/logistics/stats/` | GET | 200 | ✅ 通过 |
| Demo物流追踪 | `/api/v1/logistics/track/SF123456/` | GET | 200 | ✅ 通过 |
| Demo承运商列表 | `/api/v1/logistics/carriers/` | GET | 200 | ✅ 通过 |
| Demo订阅物流 | `/api/v1/logistics/subscribe/` | POST | 200 | ✅ 通过 |
| Demo AI生成标题 | `/api/ai/generate-title/` | POST | 200 | ✅ 通过 |
| Demo AI生成描述 | `/api/ai/generate-description/` | POST | 200 | ✅ 通过 |
| Demo AI生成卖点 | `/api/ai/generate-features/` | POST | 200 | ✅ 通过 |
| Demo AI对话 | `/api/ai/chat/` | POST | 200 | ✅ 通过 |
| Demo AI翻译 | `/api/ai/translate/` | POST | 200 | ✅ 通过 |
| Demo AI优化描述 | `/api/ai/refine-description/` | POST | 200 | ✅ 通过 |
| 正式商品列表 | `/api/goods/` | GET | 401 | ⚠️ 需认证 |
| 店铺列表 | `/api/shops/` | GET | 401 | ⚠️ 需认证 |
| 正式订单列表 | `/api/orders/` | GET | 401 | ⚠️ 需认证 |
| 库存预警 | `/api/inventory/alerts` | GET | 401 | ⚠️ 需认证 |
| 库存日志 | `/api/inventory/logs` | GET | 401 | ⚠️ 需认证 |
| 物流发货 | `/api/logistics/shipments/` | GET | 401 | ⚠️ 需认证 |
| 创建采集任务 | `/api/tasks/collect/` | POST | 401 | ⚠️ 需认证 |
| 同步日志 | `/api/sync/log/` | GET | 401 | ⚠️ 需认证 |
| 运维Whoami | `/api/ops/whoami/` | GET | 401 | ⚠️ 需认证 |
| v1健康检查 | `/v1/health/` | GET | 200 | ✅ 通过 |

## 说明

- **✅ 通过**: 接口正常响应 (HTTP 200/201/204)
- **⚠️ 需认证**: 接口需要登录认证 (HTTP 401/403)，功能正常
- **❌ 失败**: 接口异常或不存在 (HTTP 404/405/500 或连接错误)

## 分类统计

### Demo 接口 (免登录)
Demo 接口用于前端开发测试，无需真实认证即可返回模拟数据。

### 正式接口 (需认证)
正式接口需要有效的 JWT Token 才能访问，返回真实业务数据。

## 建议

1. **Demo 接口失败**: 检查后端 DEMO_MODE 是否开启
2. **正式接口 401**: 这是预期行为，需要前端携带 Token 访问
3. **404/405 错误**: 检查 URL 路径和方法是否正确
4. **500 错误**: 后端代码异常，需要查看后端日志
