"""
generate_bigseller_excel.py
----------------------------
根据 product.optimized.json、uploaded_image_urls.json、product.pricing.json，
生成可直接导入 BigSeller ERP 的 Excel 表格，并输出 erp_upload_report.md。

用法:
    python scripts/generate_bigseller_excel.py \
        --optimized outputs/<product_code>/product.optimized.json \
        --images outputs/<product_code>/uploaded_image_urls.json \
        --pricing outputs/<product_code>/product.pricing.json \
        --template templates/bigseller_template.xlsx \
        --output outputs/<product_code>/bigseller_product_upload.xlsx \
        --report outputs/<product_code>/erp_upload_report.md
"""

import argparse
import json
import os
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


# BigSeller 模板列顺序（与模板完全一致）
# TODO: 这里仍是技术债。后续应读取 configs/bigseller_mapping.example.yaml，
# 让 target_column/source/required/default 由 YAML 控制，而不是写死在 Python 中。
COLUMNS = [
    "分类ID*",
    "产品名称*",
    "供应商链接",
    "Parent SKU",
    "产品描述*",
    "变种名称1",
    "变种选项1",
    "变种名称2",
    "变种选项2",
    "SKU",
    "库存*",
    "价格*",
    "折扣活动ID",
    "促销价",
    "变种图",
    "产品主图*",
    "产品附属图1",
    "产品附属图2",
    "产品附属图3",
    "产品附属图4",
    "产品附属图5",
    "产品附属图6",
    "产品附属图7",
    "产品附属图8",
    "尺码表ID / 尺码图",
    "重量（g）*",
    "长（cm）",
    "宽（cm）",
    "高（cm）",
    "发货期（天）",
    "物品状况",
]

REQUIRED_FIELDS = {
    "分类ID*", "产品名称*", "产品描述*", "库存*", "价格*", "产品主图*", "重量（g）*"
}


def get_safe(data: dict, *keys, default=None):
    """安全地从嵌套 dict 中取值"""
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is None:
            return default
    return cur


def validate_required(row: dict, sku_id: str, warnings: list):
    """校验必填字段"""
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            warnings.append(f"[ERROR] SKU {sku_id}: 必填字段 [{field}] 为空")


def build_rows(optimized: dict, images: dict, pricing: dict) -> tuple[list[dict], list[str]]:
    """
    构建每个 SKU 对应的行数据。
    返回: (rows, warnings)
    """
    warnings = []
    rows = []

    # 构建定价索引 {sku_id: pricing_data}
    pricing_index = {p["sku"]: p for p in pricing.get("skus", [])}

    # 公共字段
    common = {
        "分类ID*": optimized.get("category_id", ""),
        "产品名称*": optimized.get("title", ""),
        "供应商链接": get_safe(optimized, "supplier_link", default=""),
        "Parent SKU": optimized.get("parent_sku", ""),
        "产品描述*": optimized.get("description", ""),
        "产品主图*": images.get("main", [""])[0] if images.get("main") else "",
        "重量（g）*": optimized.get("weight", 200),
        "长（cm）": optimized.get("length", 10),
        "宽（cm）": optimized.get("width", 10),
        "高（cm）": optimized.get("height", 10),
        "发货期（天）": optimized.get("lead_time_days", ""),
        "物品状况": optimized.get("condition", 1),
    }

    # 附属图
    detail_images = images.get("detail", [])
    for i, img_url in enumerate(detail_images[:8]):
        col_name = f"产品附属图{i+1}"
        common[col_name] = img_url

    skus = optimized.get("skus", [])
    if not skus:
        warnings.append("[ERROR] product.optimized.json 中没有 skus，无法生成表格")
        return rows, warnings

    for sku in skus:
        sku_id = sku.get("sku_id", "")
        p = pricing_index.get(sku_id, {})

        row = dict(common)
        row["变种名称1"] = sku.get("variant_name_1", "")
        row["变种选项1"] = sku.get("variant_value_1", "")
        row["变种名称2"] = sku.get("variant_name_2", "")
        row["变种选项2"] = sku.get("variant_value_2", "")
        row["SKU"] = sku_id
        row["库存*"] = sku.get("stock", 100)
        # 价格* = 划线原价（sale_price = discount_price × 2）
        # 促销价 = 折扣活动价（discount_price）
        row["价格*"] = p.get("sale_price") or p.get("suggested_original_price", "")
        row["促销价"] = p.get("discount_price") or p.get("campaign_price", "")
        row["变种图"] = get_safe(images, "skus", sku_id, default="")

        validate_required(row, sku_id, warnings)
        rows.append(row)

    return rows, warnings


def write_excel(rows: list[dict], template_path: str, output_path: str):
    """
    将行数据写入 Excel，保留模板的表头样式。
    """
    # 读取原始模板以复用表头样式
    wb_tpl = openpyxl.load_workbook(template_path)
    ws_tpl = wb_tpl.active

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    # 复制表头（第1行）
    header_row = [cell.value for cell in ws_tpl[1]]
    ws.append(header_row)

    # 表头样式
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 写入数据行
    for row_data in rows:
        row_values = [row_data.get(col, "") for col in COLUMNS]
        ws.append(row_values)

    # 自动调整列宽（简单版）
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 60)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)


def write_report(rows: list[dict], warnings: list[str], output_path: str,
                 optimized: dict, pricing: dict):
    """生成 erp_upload_report.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_skus = len(rows)
    errors = [w for w in warnings if w.startswith("[ERROR]")]
    warns = [w for w in warnings if w.startswith("[WARN]")]

    lines = [
        "# ERP 上传报告",
        "",
        f"**生成时间**: {now}",
        f"**产品名称**: {optimized.get('title', 'N/A')}",
        f"**Parent SKU**: {optimized.get('parent_sku', 'N/A')}",
        f"**SKU 总数**: {total_skus}",
        "",
        "## 字段填充状态",
        "",
        "| 字段 | 状态 |",
        "|---|---|",
    ]

    # 检查每个字段的填充情况
    all_fields = COLUMNS
    for field in all_fields:
        filled = all(row.get(field) not in (None, "") for row in rows)
        required = field in REQUIRED_FIELDS
        if filled:
            status = "✅ 已填充"
        elif required:
            status = "❌ 必填但为空"
        else:
            status = "⬜ 可选，未填充"
        lines.append(f"| {field} | {status} |")

    lines += [
        "",
        "## SKU 定价摘要",
        "",
        "| SKU | 售价 (PHP) | 活动价 (PHP) | 利润 (PHP) | 利润警告 |",
        "|---|---|---|---|---|",
    ]
    for p in pricing.get("skus", []):
        warning_flag = "⚠️" if p.get("margin_warning") else "✅"
        lines.append(
            f"| {p['sku']} | {p.get('suggested_sale_price', '-')} "
            f"| {p.get('campaign_price', '-')} "
            f"| {p.get('estimated_margin', '-')} "
            f"| {warning_flag} |"
        )

    if errors or warns:
        lines += ["", "## 错误与警告", ""]
        for w in errors + warns:
            lines.append(f"- {w}")

    lines += [
        "",
        "## 下一步操作",
        "",
        "1. 检查上方标记为 ❌ 的必填字段，补充后重新生成。",
        "2. 检查利润警告的 SKU，确认定价策略。",
        "3. 确认图片 URL 可正常访问。",
        "4. 将 `bigseller_product_upload.xlsx` 导入 BigSeller ERP。",
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="生成 BigSeller ERP 导入表格")
    parser.add_argument("--optimized", required=True)
    parser.add_argument("--images", required=True)
    parser.add_argument("--pricing", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    with open(args.optimized, "r", encoding="utf-8") as f:
        optimized = json.load(f)
    with open(args.images, "r", encoding="utf-8") as f:
        images = json.load(f)
    with open(args.pricing, "r", encoding="utf-8") as f:
        pricing = json.load(f)

    rows, warnings = build_rows(optimized, images, pricing)

    if not rows:
        print("[ERROR] 没有可生成的行，请检查输入数据")
        for w in warnings:
            print(w)
        exit(1)

    write_excel(rows, args.template, args.output)
    write_report(rows, warnings, args.report, optimized, pricing)

    print(f"[OK] Excel 已生成: {args.output}")
    print(f"[OK] 报告已生成: {args.report}")
    for w in warnings:
        print(w)


if __name__ == "__main__":
    main()
