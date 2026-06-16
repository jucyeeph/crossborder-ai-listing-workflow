"""
interactive_product_optimize.py
---------------------------------
交互式产品信息优化脚本。
根据 product.raw.json 或现有 product.optimized.json，
通过交互式确认流程生成符合品牌规范的 product.optimized.json 和 product.pricing.json。

注意：本脚本中的定价步骤仅作为人工交互辅助。
正式 pricing source of truth = scripts/calculate_pricing.py。

处理顺序：
  Step 0: 产品系列档案（Product Brief）总结与确认
          AI 自动提取系列名称、产品类型、核心卖点，用户确认或补充
  Step 1: 标题生成与确认（JUCYEE前缀，≤100字符，含关键词）
  Step 2: SKU 命名规则确认（parentSKU、产品SKU、变种命名）
  Step 3: 产品描述生成（自动嵌入品牌前缀/后缀模板 + Product Brief卖点）
  Step 4: 定价交互确认（采购价 → 推荐折扣价 → 最终售价）

用法:
    python scripts/interactive_product_optimize.py \
        --input outputs/<product_code>/product.optimized.json \
        --output outputs/<product_code>/product.optimized.json \
        --pricing-output outputs/<product_code>/product.pricing.json \
        --description-template configs/product_description_template.md \
        --brief-output outputs/<product_code>/product_brief.md
"""

import argparse
import json
import math
import os
import re


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

    prefix_match = re.search(r'## 前缀.*?```text\n(.*?)```', content, re.DOTALL)
    prefix = prefix_match.group(1).strip() if prefix_match else ""

    suffix_match = re.search(r'## 后缀.*?```text\n(.*?)```', content, re.DOTALL)
    suffix = suffix_match.group(1).strip() if suffix_match else ""

    return prefix, suffix


def load_existing_brief(brief_path: str) -> dict:
    """加载已有的 product_brief.json（如果存在）"""
    if os.path.exists(brief_path):
        with open(brief_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_brief(brief: dict, brief_path: str):
    """保存 product_brief.json"""
    os.makedirs(os.path.dirname(brief_path), exist_ok=True)
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)


# ============================================================
# Step 0: 产品系列档案（Product Brief）总结与确认
# ============================================================

def _infer_series_name(optimized: dict) -> str:
    """从产品标题和 SKU 信息推断系列名称"""
    title = optimized.get("title", "")
    # 尝试从标题中提取系列关键词
    series_keywords = re.findall(
        r'\b(Galaxy|Star Touch|Wave Bottle|Cat Eye|Aurora|Crystal|Diamond|Magnetic|Halo|Glitter)\b',
        title, re.IGNORECASE
    )
    if series_keywords:
        return " ".join(dict.fromkeys(series_keywords))  # 去重保序
    # 如果没有匹配到，返回标题前20字符作为提示
    return title[:30] + "..." if len(title) > 30 else title


def _infer_product_type(optimized: dict) -> str:
    """从产品信息推断产品类型"""
    title = optimized.get("title", "").lower()
    if "cat eye" in title:
        return "Cat Eye Gel Polish（猫眼胶）"
    elif "glitter" in title:
        return "Glitter Gel Polish（闪粉胶）"
    elif "color gel" in title or "colour gel" in title:
        return "Color Gel Polish（彩色甲油胶）"
    elif "gel" in title:
        return "Gel Polish（甲油胶）"
    return "Nail Gel Polish（美甲胶）"


def _infer_selling_points(optimized: dict) -> list[str]:
    """从 selling_points 和 description 提取/推断核心卖点"""
    existing_points = optimized.get("selling_points", [])
    if existing_points:
        return existing_points[:6]  # 最多取6条

    # 从描述中提取
    desc = optimized.get("description", "")
    points = []
    for line in desc.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            clean = re.sub(r'^[\d\.\-\*]+\s*', '', line).strip()
            if clean and len(clean) > 10:
                points.append(clean)
    return points[:6]


def _infer_package_options(optimized: dict) -> list[str]:
    """推断套装/包装选项"""
    skus = optimized.get("skus", [])
    sku_count = len(skus)
    options = [f"Single bottle (15ml) — {sku_count} colors available"]

    # 如果SKU数量多，推荐套装
    if sku_count >= 6:
        options.append(f"Full set with color swatch card — all {sku_count} colors")
    if sku_count >= 12:
        options.append("Starter kit set (selected colors + color chart)")

    return options


def confirm_product_brief(optimized: dict, existing_brief: dict, brief_output_path: str) -> dict:
    """
    Step 0: 产品系列档案总结与确认。
    AI 自动提取信息，用户逐项确认或补充，最终保存为 product_brief.json。
    返回确认后的 brief dict。
    """
    print("\n" + "=" * 60)
    print("【Step 0】产品系列档案（Product Brief）总结与确认")
    print("  AI 将自动总结产品系列信息，请逐项确认或补充。")
    print("=" * 60)

    brief = dict(existing_brief)  # 从已有档案开始

    # --- 系列名称 ---
    inferred_series = brief.get("series_name") or _infer_series_name(optimized)
    print(f"\n【系列名称 Series Name】")
    print(f"  AI 推荐：{inferred_series}")
    user_input = input("  确认请直接回车，修改请输入：> ").strip()
    brief["series_name"] = user_input if user_input else inferred_series

    # --- 产品类型 ---
    inferred_type = brief.get("product_type") or _infer_product_type(optimized)
    print(f"\n【产品类型 Product Type】")
    print(f"  AI 推荐：{inferred_type}")
    user_input = input("  确认请直接回车，修改请输入：> ").strip()
    brief["product_type"] = user_input if user_input else inferred_type

    # --- 核心卖点 ---
    inferred_points = brief.get("selling_points") or _infer_selling_points(optimized)
    print(f"\n【核心卖点 Selling Points】")
    print("  AI 总结的卖点如下（将用于所有同系列产品描述）：")
    for i, pt in enumerate(inferred_points, 1):
        print(f"  {i}. {pt}")
    print("\n  操作选项：")
    print("  - 直接回车：接受以上全部卖点")
    print("  - 输入数字（如 3）：删除第3条卖点")
    print("  - 输入文字：添加新卖点（将追加到列表末尾）")
    print("  - 输入 done：完成编辑")

    current_points = list(inferred_points)
    while True:
        user_input = input("  > ").strip()
        if not user_input or user_input.lower() in ("done", "ok", "确认", "y"):
            break
        elif user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(current_points):
                removed = current_points.pop(idx)
                print(f"  ✅ 已删除：{removed}")
                for i, pt in enumerate(current_points, 1):
                    print(f"  {i}. {pt}")
            else:
                print(f"  ❌ 无效序号，请输入 1-{len(current_points)}")
        else:
            current_points.append(user_input)
            print(f"  ✅ 已添加：{user_input}")

    brief["selling_points"] = current_points

    # --- 套装/包装选项 ---
    inferred_packages = brief.get("package_options") or _infer_package_options(optimized)
    print(f"\n【套装/包装选项 Package Options】")
    print("  AI 推荐的套装选项：")
    for i, pkg in enumerate(inferred_packages, 1):
        print(f"  {i}. {pkg}")
    print("\n  操作选项：")
    print("  - 直接回车：接受以上选项")
    print("  - 输入文字：添加新套装选项")
    print("  - 输入 done：完成编辑")

    current_packages = list(inferred_packages)
    while True:
        user_input = input("  > ").strip()
        if not user_input or user_input.lower() in ("done", "ok", "确认", "y"):
            break
        else:
            current_packages.append(user_input)
            print(f"  ✅ 已添加：{user_input}")

    brief["package_options"] = current_packages

    # --- 特殊说明 ---
    existing_notes = brief.get("special_notes", "")
    print(f"\n【特殊说明 Special Notes】（可选）")
    print(f"  当前说明：{existing_notes if existing_notes else '（无）'}")
    print("  例如：使用前需摇匀；需搭配黑色打底；色号与色板一致等")
    user_input = input("  直接回车跳过，或输入说明：> ").strip()
    if user_input:
        brief["special_notes"] = user_input
    elif existing_notes:
        brief["special_notes"] = existing_notes

    # 保存档案
    save_brief(brief, brief_output_path)
    print(f"\n✅ 产品系列档案已保存：{brief_output_path}")
    print(f"   系列：{brief['series_name']} | 类型：{brief['product_type']}")
    print(f"   卖点数：{len(brief['selling_points'])} | 套装选项：{len(brief['package_options'])}")

    # 同步更新 optimized 的 selling_points
    optimized["selling_points"] = brief["selling_points"]
    optimized["series_name"] = brief["series_name"]

    return brief


# ============================================================
# Step 1: 标题优化
# ============================================================

def optimize_title(current_title: str, brief: dict) -> str:
    """
    确认或优化产品标题：
    - 必须以 JUCYEE 开头
    - 总字符数 ≤ 100
    - 可参考 brief 中的系列名称和产品类型
    """
    print("\n" + "=" * 60)
    print("【Step 1】标题生成与确认")
    print("=" * 60)

    series = brief.get("series_name", "")
    product_type = brief.get("product_type", "")

    # 构建推荐标题
    if not current_title.startswith("JUCYEE"):
        # 尝试融入系列名称
        if series and series.lower() not in current_title.lower():
            recommended = f"JUCYEE {series} {current_title}"
        else:
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
    if series:
        print(f"（已融入系列名称：{series}）")

    user_input = input("\n确认请直接回车，修改请输入新标题：> ").strip()
    if not user_input or user_input.lower() in ("y", "ok", "确认", "yes"):
        final_title = recommended
    else:
        final_title = user_input
        if not final_title.startswith("JUCYEE"):
            final_title = f"JUCYEE {final_title}"

    if len(final_title) > 100:
        print(f"  ⚠️  标题超过100字符（当前{len(final_title)}字符），已自动截断")
        final_title = final_title[:97] + "..."

    print(f"\n✅ 最终标题（{len(final_title)}字符）：{final_title}")
    return final_title


# ============================================================
# Step 2: SKU 命名规则确认
# ============================================================

def optimize_sku(optimized: dict) -> dict:
    """交互式确认 SKU 命名规则，批量更新 parent_sku 和所有 SKU。"""
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
    print(f"\n当前 parentSKU：{current_parent}")
    parent_input = input(f"  推荐 parentSKU：{current_parent}\n  确认请直接回车，修改请输入新值：> ").strip()
    final_parent = parent_input if parent_input else current_parent

    # 推荐产品 SKU 规则示例
    first_variant = first_sku.get("variant_value_1", "")
    clean_variant = re.sub(r'[\u4e00-\u9fff]+', '', first_variant).strip() or "Color 01"
    recommended_sku_example = f"{final_parent}-{clean_variant[:15]} 01"

    print(f"\n产品SKU规则示例（第1个SKU）：")
    print(f"  推荐：{recommended_sku_example} 是01色号")
    sku_rule_input = input("  确认请直接回车，修改请用自然语言描述规则：> ").strip()

    # 推荐变种命名规则
    recommended_variant_example = clean_variant[:18] if len(clean_variant) <= 18 else clean_variant[:18]
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
                sep = "#" if '#' in sku_rule_input else " "
                new_sku["sku_id"] = f"{final_parent}-{prefix_part}{sep}{num}"
            else:
                new_sku["sku_id"] = f"{final_parent}-{num}"
        else:
            new_sku["sku_id"] = f"{final_parent}-{num}"

        # 处理 variant_value_1
        if variant_rule_input:
            pattern_match = re.search(r'(.+?)(?:#?\d+)\s+是\d+色号', variant_rule_input)
            if pattern_match:
                prefix_part = pattern_match.group(1).strip()
                sep = "#" if '#' in variant_rule_input else " "
                variant_val = f"{prefix_part}{sep}{num}"
            else:
                original_val = sku.get("variant_value_1", "")
                variant_val = re.sub(r'[\u4e00-\u9fff]+', '', original_val).strip() or f"Color #{num}"
        else:
            original_val = sku.get("variant_value_1", "")
            variant_val = re.sub(r'[\u4e00-\u9fff]+', '', original_val).strip()
            if not variant_val:
                variant_val = f"Color #{num}"

        if len(variant_val) > 20:
            variant_val = variant_val[:20]
        new_sku["variant_value_1"] = variant_val

        updated_skus.append(new_sku)

    optimized["parent_sku"] = final_parent
    optimized["skus"] = updated_skus

    print(f"\n✅ SKU 规则已应用，共 {len(updated_skus)} 个 SKU")
    print(f"   parentSKU：{final_parent}")
    print(f"   示例 SKU：{updated_skus[0]['sku_id']} | 变种：{updated_skus[0]['variant_value_1']}")
    return optimized


# ============================================================
# Step 3: 产品描述生成（融合 Product Brief）
# ============================================================

def optimize_description(optimized: dict, prefix: str, suffix: str, brief: dict) -> dict:
    """
    将产品描述嵌入品牌标准前缀/后缀模板，并融合 Product Brief 中的卖点和套装信息。
    """
    print("\n" + "=" * 60)
    print("【Step 3】产品描述生成")
    print("=" * 60)

    current_description = optimized.get("description", "")
    series_name = brief.get("series_name", "")
    selling_points = brief.get("selling_points", [])
    package_options = brief.get("package_options", [])
    special_notes = brief.get("special_notes", "")

    # 检查是否已经有前缀
    if current_description.startswith("<<All the products"):
        print("  ℹ️  描述已包含品牌前缀，跳过重复添加")
        final_description = current_description
    else:
        # 构建动态内容部分
        dynamic_parts = []

        # 系列介绍
        if series_name:
            dynamic_parts.append(f"✨ {series_name} Series")
            dynamic_parts.append("")

        # 核心卖点
        if selling_points:
            dynamic_parts.append("Key Features:")
            for i, pt in enumerate(selling_points, 1):
                dynamic_parts.append(f"{i}. {pt}")
            dynamic_parts.append("")

        # 套装选项
        if package_options:
            dynamic_parts.append("Available Options:")
            for pkg in package_options:
                dynamic_parts.append(f"- {pkg}")
            dynamic_parts.append("")

        # 原有描述内容（使用方法、规格等）
        if current_description:
            dynamic_parts.append(current_description)

        # 特殊说明
        if special_notes:
            dynamic_parts.append("")
            dynamic_parts.append(f"Note: {special_notes}")

        dynamic_content = "\n".join(dynamic_parts)
        final_description = f"{prefix}\n\n{dynamic_content}\n\n{suffix}"

        print(f"\n  ✅ 已自动融合：品牌前缀 + 系列信息 + 卖点 + 套装选项 + 品牌后缀")
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

    # 询问汇率
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
        net_receive = final_sale_price * 0.70
        margin = net_receive - php_cost - 5

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
    parser.add_argument("--brief-output", required=True, help="输出 product_brief.json 路径")
    args = parser.parse_args()

    # 加载数据
    with open(args.input, "r", encoding="utf-8") as f:
        optimized = json.load(f)

    # 加载描述模板
    prefix, suffix = load_description_template(args.description_template)

    # 加载已有 brief（如果存在，可复用上次确认的信息）
    existing_brief = load_existing_brief(args.brief_output)

    print("\n" + "=" * 60)
    print("  产品信息交互式优化工作流")
    print(f"  产品：{optimized.get('title', 'N/A')}")
    print(f"  SKU 数：{len(optimized.get('skus', []))}")
    if existing_brief:
        print(f"  已有系列档案：{existing_brief.get('series_name', '未命名')}（可复用）")
    print("=" * 60)

    # Step 0: Product Brief 总结与确认
    brief = confirm_product_brief(optimized, existing_brief, args.brief_output)

    # Step 1: 标题（融合系列名称）
    optimized["title"] = optimize_title(optimized.get("title", ""), brief)

    # Step 2: SKU
    optimized = optimize_sku(optimized)

    # Step 3: 描述（融合 Product Brief）
    optimized = optimize_description(optimized, prefix, suffix, brief)

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
    print(f"   product_brief.json     → {args.brief_output}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
