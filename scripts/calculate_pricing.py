"""
calculate_pricing.py
--------------------
根据 pricing_config.json 和 product.optimized.json 中的 SKU 成本信息，
计算每个 SKU 的建议售价、活动价、利润等，输出 product.pricing.json。

用法:
    python scripts/calculate_pricing.py \
        --optimized outputs/<product_code>/product.optimized.json \
        --config configs/pricing_config.example.json \
        --output outputs/<product_code>/product.pricing.json
"""

import argparse
import json
import math
import os


def round_to_end_with_9(price: float) -> float:
    """将价格向上取整到以9结尾的整数，如 91 -> 99, 100 -> 109"""
    base = math.ceil(price)
    remainder = base % 10
    if remainder <= 9:
        return base + (9 - remainder)
    return base


def calculate_sku_pricing(sku: dict, config: dict) -> dict:
    """
    计算单个 SKU 的定价结果。

    sku 字段说明:
        sku_id: SKU 编号
        rmb_cost: 人民币采购成本
        stock: 库存（不参与定价）

    config 字段说明:
        currency.rmb_to_php: 人民币兑菲律宾比索汇率
        platform.net_receive_rate: 平台实收比例（扣除平台佣金后）
        platform.fixed_cost_php: 每单固定成本（PHP）
        pricing.base_multiplier: 定价倍率
        pricing.min_margin_php: 最低利润（PHP）
        pricing.rounding_rule: 尾数规则（目前支持 end_with_9）
        campaign.discount_price_ratio: 活动价折扣比例
    """
    rmb_cost = sku.get("rmb_cost", 0)
    currency = config["currency"]
    platform = config["platform"]
    pricing = config["pricing"]
    campaign = config["campaign"]

    php_cost = rmb_cost * currency["rmb_to_php"]
    raw_price = php_cost * pricing["base_multiplier"] + platform["fixed_cost_php"]

    # 尾数处理
    if pricing["rounding_rule"] == "end_with_9":
        suggested_sale_price = round_to_end_with_9(raw_price)
    else:
        suggested_sale_price = math.ceil(raw_price)

    suggested_original_price = round_to_end_with_9(suggested_sale_price * 1.2)
    campaign_price = round_to_end_with_9(suggested_sale_price * campaign["discount_price_ratio"])

    # 确保活动价不低于最低利润线
    net_receive = campaign_price * platform["net_receive_rate"]
    margin = net_receive - php_cost - platform["fixed_cost_php"]
    if margin < pricing["min_margin_php"]:
        # 活动价上调至满足最低利润
        min_campaign_price = (php_cost + platform["fixed_cost_php"] + pricing["min_margin_php"]) / platform["net_receive_rate"]
        campaign_price = round_to_end_with_9(min_campaign_price)
        net_receive = campaign_price * platform["net_receive_rate"]
        margin = net_receive - php_cost - platform["fixed_cost_php"]

    return {
        "sku": sku["sku_id"],
        "rmb_cost": round(rmb_cost, 2),
        "estimated_php_cost": round(php_cost, 2),
        "suggested_original_price": suggested_original_price,
        "suggested_sale_price": suggested_sale_price,
        "campaign_price": campaign_price,
        "estimated_net_receive": round(net_receive, 2),
        "estimated_margin": round(margin, 2),
        "margin_warning": margin < pricing["min_margin_php"]
    }


def main():
    parser = argparse.ArgumentParser(description="计算产品定价")
    parser.add_argument("--optimized", required=True, help="product.optimized.json 路径")
    parser.add_argument("--config", required=True, help="pricing_config.json 路径")
    parser.add_argument("--output", required=True, help="输出 product.pricing.json 路径")
    args = parser.parse_args()

    with open(args.optimized, "r", encoding="utf-8") as f:
        optimized = json.load(f)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    skus = optimized.get("skus", [])
    if not skus:
        print("[ERROR] product.optimized.json 中没有 skus 字段")
        exit(1)

    results = []
    warnings = []
    for sku in skus:
        if "rmb_cost" not in sku:
            warnings.append(f"[WARN] SKU {sku.get('sku_id', '?')} 缺少 rmb_cost，跳过定价")
            continue
        result = calculate_sku_pricing(sku, config)
        results.append(result)
        if result["margin_warning"]:
            warnings.append(f"[WARN] SKU {result['sku']} 利润偏低: {result['estimated_margin']:.2f} PHP")

    pricing_output = {"skus": results}

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(pricing_output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 定价结果已写入: {args.output}")
    for w in warnings:
        print(w)


if __name__ == "__main__":
    main()
