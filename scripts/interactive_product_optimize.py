"""
interactive_product_optimize.py
---------------------------------
交互式产品信息优化脚本。
根据 product.raw.json 或现有 product.optimized.json，
通过交互式确认流程生成符合品牌规范的 product.optimized.json 和 product.pricing.json。

处理顺序：
  Step 1: 标题生成与确认（JUCYEE前缀，≤100字符，含关键词）
  Step 2: SKU 命名规则确认（parentSKU、产品SKU、变种命名）
  Step 3: 产品描述生成（自动嵌入品牌前缀/后缀模板）
  Step 4: 定价交互确认（采购价 → 推荐折扣价 → 最终售价）

用法:
    python scripts/interactive_product_optimize.py \
        --input outputs/<product_code>/product.optimized.json \
        --output outputs/<product_code>/product.optimized.json \
        --pricing-output outputs/<product_code>/product.pricing.json \
        --description-template configs/product_description_template.md
"""

import argparse
import json
import math
import os
import re
import sys


# ============================================================
# 工具函数
# ============================================================

def round_to_end_with_9(price: float) -> int:
    """将价格向上取整到以9结尾的整数，如 91 -> 99, 100 -> 109"""
    base = math.ceil(price)
    remainder = base % 10
    if remainder <= 9:
        return base + (9 - remainder)
    return base


def load_description_template(template_path: str) -> tuple[str, str]:
    """
    从 product_description_template.md 中提取前缀和后缀文本。
    返回: (prefix_text, suffix_text)
    """
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取前缀（## 前缀 到 ## 动态内容 之间的代码块）
    prefix_match = re.search(r'## 前缀.*?```text\n(.*?)```', content, re.DOTALL)
    prefix = prefix_match.group(1).strip() if prefix_match else ""

    # 提取后缀（## 后缀 到文件末尾的代码块）
    suffix_match = re.search(r'## 后缀.*?```text\n(.*?)```', content, re.DOTALL)
    suffix = suffix_match.group(1).strip() if suffix_match else ""

    return prefix, suffix


def ask_user(prompt: str) -> str:
    """向用户提问并获取输入"""
    print(f"\n{prompt}")
    print("-" * 60)
    return input("> ").strip()


def confirm_or_modify(label: str, recommended: str) -> str:
    """
    展示推荐值，等待用户确认或修改。
    用户直接回车或输入 'y'/'ok'/'确认' 表示接受推荐。
    """
    print(f"\n{label}")
    print(f"  推荐：{recommended}")
    user_input = input("  确认请直接回车，修改请输入新内容：> ").strip()
    if not user_input or user_input.lower() in ("y", "ok", "确认", "yes"):
        return recommended
    return user_input


# ============================================================
# Step 1: 标题优化
# ============================================================

def optimize_title(current_title: str) -> str:
    """
    确认或优化产品标题：
    - 必须以 JUCYEE 开头
    - 总字符数 ≤ 100
    """
    print("\n" + "=" * 60)
    print("【Step 1】标题生成与确认")
    print("=" * 60)

    # 如果标题没有 JUCYEE 前缀，自动添加
    if not current_title.startswith("JUCYEE"):
        recommended = f"JUCYEE {current_title}"
    else:
        recommended = current_title

    # 截断到100字符
    if len(recommended) > 100:
        recommended = recommended[:97] + "..."

    char_count = len(recommended)
    status = "✅" if char_count <= 100 else "❌ 超出限制"

    print(f"\n当前标题：{current_title}")
    print(f"推荐标题：{recommended}")
    print(f"字符数：{char_count} {status}")

    user_input = input("\n确认请直接回车，修改请输入新标题：> ").strip()
    if not user_input or user_input.lower() in ("y", "ok", "确认", "yes"):
        final_title = recommended
    else:
        final_title = user_input
        # 确保有 JUCYEE 前缀
        if not final_title.startswith("JUCYEE"):
            final_title = f"JUCYEE {final_title}"

    # 最终字符数检查
    if len(final_title) > 100:
        print(f"  ⚠️  标题超过100字符（当前{len(final_title)}字符），已自动截断")
        final_title = final_title[:97] + "..."

    print(f"\n✅ 最终标题（{len(final_title)}字符）：{final_title}")
    return final_title


# ============================================================
# Step 2: SKU 命名规则确认
# ============================================================

def _infer_parent_sku(current_parent_sku: str) -> str:
    """根据当前 parent_sku 推荐格式"""
    # 如果已经是规范格式（如 JB0213），直接推荐
    if re.match(r'^[A-Z]{2}\d{4}$', current_parent_sku):
        return current_parent_sku
    # 否则推荐保留原值
    return current_parent_sku


def _infer_sku_example(parent_sku: str, first_sku: dict) -> str:
    """根据第一个 SKU 推断 SKU 规则示例"""
    variant_val = first_sku.get("variant_value_1", "Color 01")
    # 清理中文
    variant_val_clean = re.sub(r'[\u4e00-\u9fff]+', '', variant_val).strip()
    if not variant_val_clean:
        variant_val_clean = "Color 01"
    return f"{parent_sku}-{variant_val_clean}"


def _infer_variant_example(first_sku: dict) -> str:
    """根据第一个 SKU 推断变种命名示例"""
    variant_val = first_sku.get("variant_value_1", "")
    # 清理中文，保留英文和数字
    variant_val_clean = re.sub(r'[\u4e00-\u9fff]+', '', variant_val).strip()
    if not variant_val_clean:
        variant_val_clean = "Color #01"
    # 截断到20字符
    if len(variant_val_clean) > 20:
        variant_val_clean = variant_val_clean[:20]
    return variant_val_clean


def _apply_sku_rule_from_natural_language(rule_text: str, skus: list, parent_sku: str) -> list:
    """
    根据用户的自然语言规则，批量生成 SKU 列表。
    目前支持：
    - 数字序号类规则（如 "JB0213-Star touch 01 是01色号"）
    - 变种命名类规则（如 "WaveBottle ST #01 是01色号"）
    """
    updated_skus = []
    for i, sku in enumerate(skus):
        num = str(i + 1).zfill(2)
        new_sku = dict(sku)

        # 尝试从规则中提取模式
        # 匹配 "XXX 01 是01色号" 或 "XXX #01 是01色号" 格式
        pattern_match = re.search(r'(.+?)(?:#?\d+)\s+是\d+色号', rule_text)
        if pattern_match:
            prefix_part = pattern_match.group(1).strip()
            # 检测是否用 # 分隔
            if '#' in rule_text:
                new_sku["sku_id"] = f"{parent_sku}-{prefix_part}#{num}"
            else:
                new_sku["sku_id"] = f"{parent_sku}-{prefix_part} {num}"
        else:
            # 无法解析，保留原 sku_id
            pass

        updated_skus.append(new_sku)
    return updated_skus


def _apply_variant_rule_from_natural_language(rule_text: str, skus: list) -> list:
    """
    根据用户的自然语言变种命名规则，批量更新 variant_value_1。
    """
    updated_skus = []
    for i, sku in enumerate(skus):
        num = str(i + 1).zfill(2)
        new_sku = dict(sku)

        # 匹配 "WaveBottle ST #01 是01色号" 格式
        pattern_match = re.search(r'(.+?)(?:#?\d+)\s+是\d+色号', rule_text)
        if pattern_match:
            prefix_part = pattern_match.group(1).strip()
            if '#' in rule_text:
                variant_val = f"{prefix_part}#{num}"
            else:
                variant_val = f"{prefix_part} {num}"
            # 截断到20字符
            if len(variant_val) > 20:
                variant_val = variant_val[:20]
            new_sku["variant_value_1"] = variant_val
        else:
            # 无法解析，清理中文
            original_val = sku.get("variant_value_1", "")
            cleaned = re.sub(r'[\u4e00-\u9fff]+', '', original_val).strip()
            if len(cleaned) > 20:
                cleaned = cleaned[:20]
            new_sku["variant_value_1"] = cleaned if cleaned else f"Color #{num}"

        updated_skus.append(new_sku)
    return updated_skus


def optimize_sku(optimized: dict) -> dict:
    """
    交互式确认 SKU 命名规则，批量更新 parent_sku 和所有 SKU。
    """
    print("\n" + "=" * 60)
    print("【Step 2】SKU 命名规则确认")
    print("=" * 60)

    skus = optimized.get("skus", [])
    if not skus:
        print("  ⚠️  没有找到 SKU 数据，跳过此步骤")
        return optimized

    current_parent = optimized.get("parent_sku", "")
    first_sku = skus[0]

    # 推荐 parent SKU
    recommended_parent = _infer_parent_sku(current_parent)
    print(f"\n当前 parentSKU：{current_parent}")
    parent_input = input(f"  推荐 parentSKU：{recommended_parent}\n  确认请直接回车，修改请输入新值：> ").strip()
    final_parent = parent_input if parent_input else recommended_parent

    # 推荐产品 SKU 规则
    recommended_sku_example = _infer_sku_example(final_parent, first_sku)
    print(f"\n产品SKU规则示例（第1个SKU）：")
    print(f"  推荐：{recommended_sku_example} 是01色号")
    sku_rule_input = input("  确认请直接回车，修改请用自然语言描述规则：> ").strip()

    # 推荐变种命名规则
    recommended_variant_example = _infer_variant_example(first_sku)
    print(f"\n变种命名规则示例（第1个变种）：")
    print(f"  推荐：{recommended_variant_example} 是01色号")
    variant_rule_input = input("  确认请直接回车，修改请用自然语言描述规则：> ").strip()

    # 应用规则到所有 SKU
    updated_skus = []
    for i, sku in enumerate(skus):
        num = str(i + 1).zfill(2)
        new_sku = dict(sku)

        # 处理 sku_id
        if sku_rule_input:
            pattern_match = re.search(r'(.+?)(?:#?\d+)\s+是\d+色号', sku_rule_input)
            if pattern_match:
                prefix_part = pattern_match.group(1).strip()
                if '#' in sku_rule_input:
                    new_sku["sku_id"] = f"{final_parent}-{prefix_part}#{num}"
                else:
                    new_sku["sku_id"] = f"{final_parent}-{prefix_part} {num}"
            else:
                # 无法解析，使用 parent_sku + 序号
                new_sku["sku_id"] = f"{final_parent}-{num}"
        else:
            # 使用推荐规则
            new_sku["sku_id"] = f"{final_parent}-{recommended_sku_example.split('-', 1)[1] if '-' in recommended_sku_example else num}"
            # 如果推荐的是简单的 parent-num 格式
            new_sku["sku_id"] = f"{final_parent}-{num}"

        # 处理 variant_value_1
        if variant_rule_input:
            pattern_match = re.search(r'(.+?)(?:#?\d+)\s+是\d+色号', variant_rule_input)
            if pattern_match:
                prefix_part = pattern_match.group(1).strip()
                if '#' in variant_rule_input:
                    variant_val = f"{prefix_part}#{num}"
                else:
                    variant_val = f"{prefix_part} {num}"
                if len(variant_val) > 20:
                    variant_val = variant_val[:20]
                new_sku["variant_value_1"] = variant_val
            else:
                # 清理中文
                original_val = sku.get("variant_value_1", "")
                cleaned = re.sub(r'[\u4e00-\u9fff]+', '', original_val).strip()
                if len(cleaned) > 20:
                    cleaned = cleaned[:20]
                new_sku["variant_value_1"] = cleaned if cleaned else f"Color #{num}"
        else:
            # 使用推荐规则：清理中文
            original_val = sku.get("variant_value_1", "")
            cleaned = re.sub(r'[\u4e00-\u9fff]+', '', original_val).strip()
            if len(cleaned) > 20:
                cleaned = cleaned[:20]
            new_sku["variant_value_1"] = cleaned if cleaned else recommended_variant_example.replace("01", num)

        updated_skus.append(new_sku)

    optimized["parent_sku"] = final_parent
    optimized["skus"] = updated_skus

    print(f"\n✅ SKU 规则已应用，共 {len(updated_skus)} 个 SKU")
    print(f"   parentSKU：{final_parent}")
    print(f"   示例 SKU：{updated_skus[0]['sku_id']} | 变种：{updated_skus[0]['variant_value_1']}")
    return optimized


# ============================================================
# Step 3: 产品描述生成
# ============================================================

def optimize_description(optimized: dict, prefix: str, suffix: str) -> dict:
    """
    将产品描述嵌入品牌标准前缀/后缀模板。
    """
    print("\n" + "=" * 60)
    print("【Step 3】产品描述生成")
    print("=" * 60)

    current_description = optimized.get("description", "")

    # 检查是否已经有前缀
    if current_description.startswith("<<All the products"):
        print("  ℹ️  描述已包含品牌前缀，跳过重复添加")
        final_description = current_description
    else:
        final_description = f"{prefix}\n\n{current_description}\n\n{suffix}"
        print(f"\n  ✅ 已自动添加品牌前缀和后缀")
        print(f"  描述总长度：{len(final_description)} 字符")

    optimized["description"] = final_description
    return optimized


# ============================================================
# Step 4: 定价交互确认
# ============================================================

def optimize_pricing(optimized: dict, pricing_output_path: str) -> dict:
    """
    交互式定价确认：
    - 询问采购价
    - 计算推荐折扣价
    - 用户确认后生成 product.pricing.json
    """
    print("\n" + "=" * 60)
    print("【Step 4】定价交互确认")
    print("=" * 60)

    # 询问汇率（使用默认值）
    default_rate = 8.2
    rate_input = input(f"\n当前汇率（1 RMB = ? PHP）[默认 {default_rate}]：> ").strip()
    rate = float(rate_input) if rate_input else default_rate

    # 询问采购价
    cost_input = input("\n采购价（人民币，所有SKU相同）：> ").strip()
    try:
        rmb_cost = float(cost_input)
    except ValueError:
        print("  ❌ 无效的采购价，使用默认值 0")
        rmb_cost = 0.0

    # 计算推荐折扣价
    raw_discount = rmb_cost * rate * 2.5
    recommended_discount = round_to_end_with_9(raw_discount)
    recommended_sale_price = round_to_end_with_9(recommended_discount / 2)

    print(f"\n  计算过程：")
    print(f"  采购价：¥{rmb_cost}")
    print(f"  汇率：1 RMB = {rate} PHP")
    print(f"  推荐折扣价：{rmb_cost} × {rate} × 2.5 = {raw_discount:.2f} → 凑整 → {recommended_discount} PHP")
    print(f"  最终售价（价格*）：{recommended_discount} ÷ 2 = {recommended_discount/2:.1f} → 凑整 → {recommended_sale_price} PHP")

    discount_input = input(f"\n  确认折扣价 {recommended_discount} PHP？直接回车确认，或输入新折扣价：> ").strip()
    final_discount = int(discount_input) if discount_input.isdigit() else recommended_discount
    final_sale_price = round_to_end_with_9(final_discount / 2)

    print(f"\n✅ 最终定价：折扣价 {final_discount} PHP | 售价 {final_sale_price} PHP")

    # 生成 product.pricing.json
    skus = optimized.get("skus", [])
    pricing_skus = []
    for sku in skus:
        php_cost = rmb_cost * rate
        net_receive = final_sale_price * 0.70  # 平台实收70%
        margin = net_receive - php_cost - 5  # 扣除固定成本5PHP

        pricing_skus.append({
            "sku": sku.get("sku_id", ""),
            "rmb_cost": round(rmb_cost, 2),
            "estimated_php_cost": round(php_cost, 2),
            "suggested_original_price": round_to_end_with_9(final_discount * 1.2),
            "suggested_sale_price": final_sale_price,
            "campaign_price": final_discount,
            "estimated_net_receive": round(net_receive, 2),
            "estimated_margin": round(margin, 2),
            "margin_warning": margin < 20
        })

    pricing_output = {"skus": pricing_skus}

    os.makedirs(os.path.dirname(pricing_output_path), exist_ok=True)
    with open(pricing_output_path, "w", encoding="utf-8") as f:
        json.dump(pricing_output, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 定价文件已生成：{pricing_output_path}")
    return optimized


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="交互式产品信息优化")
    parser.add_argument("--input", required=True, help="输入 product.optimized.json 路径")
    parser.add_argument("--output", required=True, help="输出 product.optimized.json 路径")
    parser.add_argument("--pricing-output", required=True, help="输出 product.pricing.json 路径")
    parser.add_argument("--description-template", required=True, help="产品描述模板路径")
    args = parser.parse_args()

    # 加载数据
    with open(args.input, "r", encoding="utf-8") as f:
        optimized = json.load(f)

    # 加载描述模板
    prefix, suffix = load_description_template(args.description_template)

    print("\n" + "=" * 60)
    print("  产品信息交互式优化工作流")
    print(f"  产品：{optimized.get('title', 'N/A')}")
    print(f"  SKU 数：{len(optimized.get('skus', []))}")
    print("=" * 60)

    # Step 1: 标题
    optimized["title"] = optimize_title(optimized.get("title", ""))

    # Step 2: SKU
    optimized = optimize_sku(optimized)

    # Step 3: 描述
    optimized = optimize_description(optimized, prefix, suffix)

    # Step 4: 定价
    optimized = optimize_pricing(optimized, args.pricing_output)

    # 保存结果
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(optimized, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ 所有步骤完成！")
    print(f"   product.optimized.json → {args.output}")
    print(f"   product.pricing.json   → {args.pricing_output}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
