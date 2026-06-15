# 子工作流 4：产品定价工作流

## 目标

根据供应商成本、汇率、平台成本、物流成本、利润要求，生成适合菲律宾市场的定价建议。

## 输入

- `product.raw.json`
- `product.optimized.json`
- `pricing_config.json`

## 输出

- `product.pricing.json`
- `pricing_report.md`

---

## 说明

> **注意（260616-text-fields-interactive 分支起）**：
>
> 定价交互确认流程已整合至 **子工作流 2（`interactive_product_optimize.py`）的 Step 4**。
> 用户在优化产品信息时，会直接输入采购价并确认折扣价，系统自动生成 `product.pricing.json`。
>
> 本子工作流（04）的 `calculate_pricing.py` 脚本仍可独立使用，适用于批量重新计算定价的场景。

---

## 定价计算规则

| 参数 | 说明 |
|---|---|
| 采购价 | 用户输入的人民币采购价 |
| 汇率 | 1 RMB = N PHP（默认 8.2，可更新） |
| 推荐折扣价 | 采购价 × 汇率 × 2.5，个位数凑成 9 |
| 最终售价（价格*） | 折扣价 ÷ 2，个位数凑成 9 |
| 平台实收率 | 70%（扣除平台佣金） |
| 固定成本 | 5 PHP/单 |
