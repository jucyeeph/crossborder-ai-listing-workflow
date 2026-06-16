"""
calculate_pricing.py
--------------------
根据 pricing_config.json 和 product.optimized.json 中的 SKU 成本信息，
计算每个 SKU 的建议售价、活动价、利润等，输出 product.pricing.json。

定价逻辑（修正版，2026-06-16）：
    推荐折扣价 = 采购价(RMB) × 汇率(RMB→PHP) × 倍率(base_multiplier)
                 → 个位数凑整到 9（如 131 → 139）
    最终售价（价格*）= 推荐折扣价 × 2
                       → 个位数凑整到 9
    活动价 = 推荐折扣价（即折扣价本身，作为 Shopee 折扣活动价）

汇率获取策略：
    1. 优先尝试从 xe.com 获取实时汇率
    2. 获取到实时汇率后，加上 config 中的 rate_buffer（默认 0.5）并向上凑整到 0.5 的倍数
    3. 若网络请求失败，回退到 config 中的 rmb_to_php 默认值

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

try:
    import urllib.request
    import re as _re
    _HAS_URLLIB = True
except ImportError:
    _HAS_URLLIB = False


def fetch_live_rate_cny_php() -> float | None:
    """
    尝试从 xe.com 获取 CNY→PHP 实时汇率。
    返回 float 或 None（失败时）。
    """
    if not _HAS_URLLIB:
        return None
    try:
        url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=CNY&To=PHP"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; pricing-script/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # 匹配 "1 CNY = X.XXXX PHP" 或 meta 中的汇率
        m = _re.search(r'1\s*CNY\s*=\s*([\d.]+)\s*PHP', html)
        if m:
            return float(m.group(1))
        # 备用：匹配 "rate":"X.XXXX" 或类似 JSON 片段
        m = _re.search(r'"mid"\s*:\s*([\d.]+)', html)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None


def apply_rate_buffer(live_rate: float, buffer: float) -> float:
    """
    将实时汇率加上浮动缓冲，然后向上凑整到 0.5 的倍数。
    例如：8.93 + 0.5 = 9.43 → 凑整 → 9.5
    """
    raw = live_rate + buffer
    # 向上凑整到 0.5 的倍数
    return math.ceil(raw * 2) / 2


def round_to_end_with_9(price: float) -> int:
    """
    将价格向上取整到以 9 结尾的整数。
    例如：131 → 139，139 → 139，140 → 149
    """
    base = math.ceil(price)
    remainder = base % 10
    if remainder == 9:
        return base
    elif remainder < 9:
        return base + (9 - remainder)
    else:
        return base + (19 - remainder)


def calculate_sku_pricing(sku: dict, config: dict, effective_rate: float) -> dict:
    """
    计算单个 SKU 的定价结果。

    定价公式：
        php_cost          = rmb_cost × effective_rate
        discount_price    = round_to_9(rmb_cost × effective_rate × base_multiplier)
        sale_price（价格*）= round_to_9(discount_price × 2)
        campaign_price    = discount_price（折扣价即活动价）

    sku 字段说明：
        sku_id    : SKU 编号
        rmb_cost  : 人民币采购成本

    config 字段说明：
        platform.net_receive_rate  : 平台实收比例（扣除平台佣金后）
        platform.fixed_cost_php    : 每单固定成本（PHP）
        pricing.base_multiplier    : 定价倍率（默认 2.5）
        pricing.min_margin_php     : 最低利润（PHP）
        pricing.rounding_rule      : 尾数规则（目前支持 end_with_9）
    """
    rmb_cost = sku.get("rmb_cost", 0)
    platform = config["platform"]
    pricing = config["pricing"]

    php_cost = rmb_cost * effective_rate

    # 推荐折扣价 = 采购价 × 汇率 × 倍率，凑整到 9
    raw_discount = rmb_cost * effective_rate * pricing["base_multiplier"]
    if pricing.get("rounding_rule") == "end_with_9":
        discount_price = round_to_end_with_9(raw_discount)
    else:
        discount_price = math.ceil(raw_discount)

    # 最终售价（价格*）= 折扣价 × 2，凑整到 9
    raw_sale = discount_price * 2
    if pricing.get("rounding_rule") == "end_with_9":
        sale_price = round_to_end_with_9(raw_sale)
    else:
        sale_price = math.ceil(raw_sale)

    # 活动价 = 折扣价（Shopee 折扣活动展示价）
    campaign_price = discount_price

    # 利润估算（基于折扣价实收）
    net_receive = discount_price * platform["net_receive_rate"]
    margin = net_receive - php_cost - platform["fixed_cost_php"]

    # 利润警告
    margin_warning = margin < pricing["min_margin_php"]

    return {
        "sku": sku["sku_id"],
        "rmb_cost": round(rmb_cost, 2),
        "effective_rate": effective_rate,
        "estimated_php_cost": round(php_cost, 2),
        "discount_price": discount_price,
        "sale_price": sale_price,
        # 兼容旧字段名，供 generate_bigseller_excel.py 使用
        "suggested_original_price": sale_price,
        "suggested_sale_price": discount_price,
        "campaign_price": campaign_price,
        "estimated_net_receive": round(net_receive, 2),
        "estimated_margin": round(margin, 2),
        "margin_warning": margin_warning
    }


def main():
    parser = argparse.ArgumentParser(description="计算产品定价")
    parser.add_argument("--optimized", required=True, help="product.optimized.json 路径")
    parser.add_argument("--config", required=True, help="pricing_config.json 路径")
    parser.add_argument("--output", required=True, help="输出 product.pricing.json 路径")
    parser.add_argument("--no-live-rate", action="store_true", help="跳过实时汇率获取，使用 config 默认值")
    args = parser.parse_args()

    with open(args.optimized, "r", encoding="utf-8") as f:
        optimized = json.load(f)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    # ===== 汇率确定 =====
    default_rate = config["currency"]["rmb_to_php"]
    rate_buffer = config["currency"].get("rate_buffer", 0.5)
    effective_rate = default_rate
    rate_source = "config_default"

    if not args.no_live_rate:
        print("[INFO] 正在获取实时 CNY→PHP 汇率...")
        live_rate = fetch_live_rate_cny_php()
        if live_rate:
            effective_rate = apply_rate_buffer(live_rate, rate_buffer)
            rate_source = f"live({live_rate:.4f}) + buffer({rate_buffer}) → {effective_rate}"
            print(f"[INFO] 实时汇率: {live_rate:.4f}，加浮动 {rate_buffer} 凑整 → 使用汇率: {effective_rate}")
        else:
            print(f"[WARN] 实时汇率获取失败，回退到 config 默认值: {default_rate}")
            rate_source = f"config_fallback({default_rate})"
    else:
        print(f"[INFO] 使用 config 默认汇率: {default_rate}")

    # ===== 定价计算 =====
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
        result = calculate_sku_pricing(sku, config, effective_rate)
        results.append(result)
        if result["margin_warning"]:
            warnings.append(f"[WARN] SKU {result['sku']} 利润偏低: {result['estimated_margin']:.2f} PHP")

    pricing_output = {
        "rate_source": rate_source,
        "effective_rate": effective_rate,
        "skus": results
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(pricing_output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 定价结果已写入: {args.output}")
    for w in warnings:
        print(w)


if __name__ == "__main__":
    main()
