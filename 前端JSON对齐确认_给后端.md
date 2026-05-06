# 前端 JSON 对齐确认 — 给后端同事

**发件人**: 前端 竞祺  
**收件人**: 后端开发  
**日期**: 2026-05-06

---

## 修正后的 Mock JSON 结构（按前端实际绑定字段）

### 1. 订单状态统计 `/api/orders/status-counts/`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "pending": 12,      // 待审核 ✓
    "paid": 8,          // 待发货（注意：不是 processing）
    "exception": 3,     // 物流异常 ✓
    "completed": 45     // 已完成（注意：不是 delivered）
  }
}
```

> 前端只用到这 4 个字段，其他字段（cancelled/returned）不展示。

---

### 2. 物流追踪列表 `/api/logistics/shipments/`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "waybill_no": "SF1234567890",
        "order_id": "ORD-001",
        "carrier": "顺丰速运",
        "origin": "深圳仓",
        "destination": "美国洛杉矶",
        "current_location": "洛杉矶清关中心",
        "fee": 68.50,
        "status": "in_transit",
        "status_text": "运输中",
        "last_update": "2026-05-06 10:30:00",
        "exception_reason": null
      }
    ],
    "total": 5
  }
}
```

> 注意字段名差异（我已按我前端代码的实际映射调整）：
> - `waybill_no`（不是 tracking_no）
> - `order_id`（不是 order_no）
> - `status_text`（不是 status_label）
> - `last_update`（不是 updated_at）
> - 补充了 `fee` 和 `current_location`

---

### 3. 库存管理 `/api/goods/`（主列表）

```json
{
  "code": 200,
  "data": {
    "results": [
      {
        "sku": "TX-2026-M",
        "name": "夏季纯棉T恤",
        "warehouse": "深圳主仓",
        "stock": 120,
        "available": 115,
        "locked": 5,
        "safety_stock": 20,
        "status": "normal",
        "last_in": "2026-05-01",
        "last_out": "2026-05-06",
        "predicted_days": 18,
        "daily_sales": 6.5
      }
    ],
    "total": 8,
    "total_sku": 156,
    "total_stock": 5890,
    "alert_count": 3,
    "out_of_stock_count": 1
  }
}
```

> 库存概览从 `getInventoryOverview()` 获取，期望返回 `total_sku`、`total_stock`、`alert_count`、`out_of_stock_count`。

---

### 4. 销售趋势 `/api/dashboard/sales-trend`（⚠️ 特别注意格式）

```json
{
  "code": 200,
  "data": {
    "labels": ["周一","周二","周三","周四","周五","周六","周日"],
    "values": [32000, 28500, 41000, 38000, 52000, 48000, 35000]
  }
}
```

> ⚠️ **必须保持 `{labels, values}` 格式**，不要改成数组格式。  
> 前端 ECharts 图表直接绑定 `data.labels` 和 `data.values`。  
> 若改为 `[{date, amount}]` 格式会导致图表崩溃。

---

### 5. 店铺列表 `/api/shops/`

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "name": "TikTok 美国旗舰店",
      "icon": "/platform-icons/tiktok.svg",
      "platformName": "TikTok Shop",
      "account": "tiktok_us@demo.com",
      "status": "active",
      "products": 58,
      "orders_count": 58,
      "revenue": 185000.0
    }
  ]
}
```

> 前端直接 `tableData.value = res.data`，无映射。  
> 需要的字段：`name`、`icon`（不是 avatar）、`platformName`（不是 platform_label）、`account`、`status`、`products`。

---

### 6. 报表汇总 `/api/reports/summary/`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_orders": 128,
    "total_revenue": 386500.0,
    "total_products": 8,
    "total_customers": 96,
    "avg_order_value": 3019.53,
    "monthly_growth": 12.5,
    "period": {
      "start": "2026-04-06",
      "end": "2026-05-06"
    }
  }
}
```

> ✅ 这个结构 OK，前端直接绑定。

---

### 7. 订单列表 `/api/orders/`（当前正常，仅供参考）

```json
{
  "code": 200,
  "data": {
    "results": [
      {
        "id": 1001,
        "platform": "TikTok",
        "buyer": { "name": "Alice", "phone": "138****0001" },
        "products": [{ "name": "连衣裙", "sku": "SKU001", "price": 29.99, "quantity": 1, "image": "" }],
        "amount": 29.99,
        "status": "paid",
        "status_text": "待发货",
        "order_time": "2026-05-06T10:30:00",
        "pay_time": "2026-05-06T10:35:00",
        "shipping": { "address": "New York, US", "waybill_no": "", "carrier": "" },
        "buyer_message": "",
        "operation_logs": []
      }
    ],
    "total": 7
  }
}
```

> 当前 mock 数据格式基本匹配，注意 `products` 是对象数组不是简单字符串。

---

## 总结本次前端已修复项

| # | 内容 | 状态 |
|---|------|------|
| 1 | handleShip/handleAddress/handleRemark 增加 `!row?.id` 守卫，防止 `/api/orders/undefined/xxx` | ✅ 已修复 |
| 2 | handleCancel/handleView 增加 null 守卫 | ✅ 已修复 |
| 3 | initWorldMap ECharts 空数据保护，空时显示占位地图不崩溃 | ✅ 已修复 |
| 4 | 平台图标：SVG 文件全部在 `public/platform-icons/` 下，打包正常 | ✅ 无需修复 |

**请后端按以上修正后的字段名调整 Mock 数据。**
