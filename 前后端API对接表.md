# 前后端API对接表

> 来源：嘉瑞提供的「前端联调表.xlsx」
> 更新时间：2026-04-20

---

## 一、公共接口（无需鉴权）

| 接口名称 | 方法 | 路径 | 状态 | 备注 |
|----------|------|------|------|------|
| OpenAPI Schema | GET | `/api/schema/` | 🔴待联调 | **契约唯一来源** |
| Swagger UI | GET | `/swagger/` | 🔴待联调 | 在线文档页面 |
| ReDoc | GET | `/redoc/` | 🔴待联调 | 备用文档 |

---

## 二、核心认证模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 当前用户信息 | GET | `/api/auth/me` | ✅是 | 🔴待开发 | Header: Authorization |
| 图形验证码挑战 | GET | `/api/auth/captcha/challenge` | ❌否 | 🔴待开发 | |
| 发送短信验证码 | POST | `/api/auth/sms/send-code` | ❌否 | 🔴待开发 | 手机号+验证码信息 |
| 校验短信验证码 | POST | `/api/auth/sms/verify-code` | ❌否 | 🔴待开发 | 手机号+验证码 |
| 手机号登录 | POST | `/api/auth/mobile/login` | ❌否 | 🔴待开发 | 返回Token |
| 第三方登录发起 | GET | `/api/auth/{platform}/login/` | ❌否 | 🔴待开发 | platform如tiktok |
| 第三方登录回调 | GET | `/api/auth/{platform}/callback/` | ❌否 | 🔴待开发 | |
| 第三方令牌刷新 | POST | `/api/auth/{platform}/refresh/` | ✅是 | 🔴待开发 | |

**前端现状**：`src/api/auth.js` 只有简单的用户名密码登录，与后端接口不匹配

---

## 三、用户模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 注销账户 | DELETE | `/api/user/account/` | ✅是 | 🔴待开发 | |
| 手机号换绑申诉 | POST | `/api/user/phone-rebind-appeals` | ✅是 | 🔴待开发 | |

---

## 四、商品模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 商品列表/创建 | GET,POST | `/api/goods/` | ✅是 | 🟡部分实现 | `src/api/sku.js` |
| 商品详情 | GET,PUT,PATCH,DELETE | `/api/goods/{goods_id}` | ✅是 | 🔴待开发 | |

**前端现状**：`src/api/sku.js` 有 `getSkuList()` 但字段可能与后端不一致

---

## 五、店铺模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 店铺列表 | GET | `/api/shops/` | ✅是 | 🔴待开发 | 分页与筛选 |

---

## 六、库存模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 库存预警 | GET | `/api/inventory/alerts` | ✅是 | 🔴待开发 | |
| 库存日志 | GET | `/api/inventory/logs` | ✅是 | 🔴待开发 | |
| 库存同步 | POST | `/api/inventory/sync` | ✅是 | 🔴待开发 | 需要api_integrator权限 |

**前端现状**：库存页面使用mock数据

---

## 七、订单模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 订单列表 | GET | `/api/orders/` | ✅是 | 🟡部分实现 | `src/api/order.js` |
| 更新收货地址 | PATCH | `/api/orders/{order_id}/address` | ✅是 | 🔴待开发 | |
| 更新订单状态 | PATCH | `/api/orders/{order_id}/status` | ✅是 | 🔴待开发 | |

**前端现状**：`src/api/order.js` 有 `getOrderList()` 但字段可能与后端不一致

---

## 八、物流模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 物流追踪 | GET | `/api/logistics/` | ✅是 | 🟡部分实现 | |
| 物流详情 | GET | `/api/logistics/{logistics_id}/` | ✅是 | 🔴待开发 | |

---

## 九、选品引擎模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 选品列表 | GET | `/api/selection/products/` | ✅是 | 🔴待开发 | |
| 商品详情 | GET | `/api/selection/products/{product_id}/` | ✅是 | 🔴待开发 | |
| 批量创建 | POST | `/api/selection/batch/` | ✅是 | 🔴待开发 | |
| 批量预览列表 | GET | `/api/selection/batch/{batch_id}/preview/` | ✅是 | 🔴待开发 | |

---

## 十、创作者管理模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| AI多语种话术 | POST | `/api/ai/multilingual-pitch/` | ✅是 | 🔴待开发 | |
| 内容分析任务 | POST | `/api/ai/content-analysis/jobs/` | ✅是 | 🔴待开发 | |
| 评论挖掘任务 | POST | `/api/ai/review-mining/jobs/` | ✅是 | 🔴待开发 | |
| AI任务状态 | GET | `/api/ai/jobs/{job_id}/` | ✅是 | 🔴待开发 | |
| 导入平台创作者 | POST | `/api/creators/import/platform/` | ✅是 | 🔴待开发 | |
| TikTok授权 | GET | `/api/creators/auth/tiktok/login/` | ✅是 | 🔴待开发 | |
| 创作者搜索 | GET | `/api/creators/search/` | ✅是 | 🔴待开发 | |
| 同步受众数据 | POST | `/api/creators/{creator_id}/sync-audience/` | ✅是 | 🔴待开发 | |
| 发送邀约 | POST | `/api/invitations/{creator_id}/send/` | ✅是 | 🔴待开发 | |

---

## 十一、履约模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 履约单发货 | POST | `/api/fulfillment-orders/{order_id}/dispatch/` | ✅是 | 🔴待开发 | |
| 履约物流跟踪 | GET | `/api/fulfillment-orders/{order_id}/tracking/` | ✅是 | 🔴待开发 | |
| 资产授权 | POST | `/api/fulfillment-assets/{asset_id}/authorize/` | ✅是 | 🔴待开发 | |
| 上传地址申请 | POST | `/api/assets/upload-url/` | ✅是 | 🔴待开发 | |
| 履约物流Webhook | POST | `/api/webhooks/logistics/` | ❌否 | 🔴待开发 | 建议签名验证 |

---

## 十二、看板模块

| 接口名称 | 方法 | 路径 | 鉴权 | 前端状态 | 备注 |
|----------|------|------|------|----------|------|
| 创作者看板聚合 | GET | `/api/dashboard/creator-board/` | ✅是 | 🔴待开发 | |

---

## 十三、AI功能（拓岳AI - 已接入）

| 接口名称 | 方法 | 路径 | 状态 | 备注 |
|----------|------|------|------|------|
| AI生成标题 | POST | 拓岳API | ✅已实现 | `src/api/ai.js` |
| AI生成描述 | POST | 拓岳API | ✅已实现 | `src/api/ai.js` |
| AI生成卖点 | POST | 拓岳API | ✅已实现 | `src/api/ai.js` |
| AI翻译 | POST | 拓岳API | ✅已实现 | `src/api/ai.js` |
| AI生成图片 | POST | 拓岳API | ✅已实现 | `src/api/ai.js` |

---

## 总结

### 接口总数：约50+个

### 按前端实现程度分类：

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅已实现 | 5个 | AI功能（拓岳） |
| 🟡部分实现 | 3个 | SKU、订单、物流（但字段可能不一致） |
| 🔴待开发 | 40+个 | 所有其他模块 |

### 下一步行动：

1. **立即**：修改 `src/api/auth.js` 对接新的登录接口（手机号+验证码）
2. **立即**：修改 `src/api/sku.js`、`src/api/order.js`、`src/api/logistics.js` 适配新接口
3. **后续**：开发店铺、选品、创作者、履约等新模块

---

## 附录：接口字段对比

> 待从 `/api/schema/` 获取完整的 OpenAPI Schema 后填写
