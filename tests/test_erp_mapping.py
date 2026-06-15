"""
test_erp_mapping.py
--------------------
验证从 product.optimized.json + uploaded_image_urls.json + product.pricing.json
生成的 bigseller_product_upload.xlsx 是否符合 BigSeller 模板要求。

运行:
    python tests/test_erp_mapping.py
"""

import json
import os
import sys
import openpyxl

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "HMT-CAT-EYE-001")

EXCEL_PATH = os.path.join(OUTPUT_DIR, "bigseller_product_upload.xlsx")
PRICING_PATH = os.path.join(OUTPUT_DIR, "product.pricing.json")
OPTIMIZED_PATH = os.path.join(FIXTURES_DIR, "product.optimized.json")

REQUIRED_COLS = {"分类ID*", "产品名称*", "产品描述*", "库存*", "价格*", "产品主图*", "重量（g）*"}

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    print(f"{status}  {name}" + (f"  ({detail})" if detail else ""))


def run_tests():
    # 1. 文件存在性检查
    check("Excel 文件已生成", os.path.exists(EXCEL_PATH), EXCEL_PATH)
    check("定价文件已生成", os.path.exists(PRICING_PATH), PRICING_PATH)

    if not os.path.exists(EXCEL_PATH):
        print("\n[ABORT] Excel 文件不存在，终止测试")
        return

    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active

    # 2. 表头检查
    headers = [cell.value for cell in ws[1]]
    check("表头行存在", len(headers) > 0, f"列数: {len(headers)}")
    check("必填列均存在", all(col in headers for col in REQUIRED_COLS),
          str([c for c in REQUIRED_COLS if c not in headers]))

    # 3. 数据行数检查
    with open(OPTIMIZED_PATH, "r", encoding="utf-8") as f:
        optimized = json.load(f)
    expected_sku_count = len(optimized.get("skus", []))
    data_rows = list(ws.iter_rows(min_row=2, values_only=True))
    check("数据行数与SKU数一致", len(data_rows) == expected_sku_count,
          f"期望 {expected_sku_count} 行，实际 {len(data_rows)} 行")

    # 4. 必填字段非空检查
    header_index = {h: i for i, h in enumerate(headers)}
    for col in REQUIRED_COLS:
        if col not in header_index:
            continue
        idx = header_index[col]
        all_filled = all(row[idx] not in (None, "") for row in data_rows)
        check(f"必填字段 [{col}] 全部非空", all_filled)

    # 5. 价格为数字检查
    price_idx = header_index.get("价格*")
    if price_idx is not None:
        all_numeric = all(isinstance(row[price_idx], (int, float)) for row in data_rows)
        check("价格字段均为数字", all_numeric)

    # 6. 定价利润检查
    with open(PRICING_PATH, "r", encoding="utf-8") as f:
        pricing = json.load(f)
    any_margin_warning = any(p.get("margin_warning") for p in pricing.get("skus", []))
    check("所有SKU利润均达标（无利润警告）", not any_margin_warning)

    # 7. 主图URL格式检查
    main_img_idx = header_index.get("产品主图*")
    if main_img_idx is not None:
        first_row = data_rows[0] if data_rows else []
        main_img = first_row[main_img_idx] if len(first_row) > main_img_idx else None
        check("产品主图URL格式正确", isinstance(main_img, str) and main_img.startswith("http"),
              str(main_img))

    # 汇总
    total = len(results)
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = total - passed
    print(f"\n{'='*40}")
    print(f"测试结果: {passed}/{total} 通过, {failed} 失败")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
