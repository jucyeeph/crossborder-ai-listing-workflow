"""
build_product_json.py
---------------------
PROTOTYPE ONLY / SAMPLE ONLY

此脚本仅用于一次性样例数据构建，不属于正式工作流。
正式流程不得依赖本脚本中的硬编码路径。

从1688页面markdown和HTML中提取完整产品数据，
构建 product.optimized.json 和 uploaded_image_urls.json。
"""

import re
import json
import os
from bs4 import BeautifulSoup

# ---- 配置 ----
HTML_PATH = '/home/ubuntu/browser_html/detail_1688_com_981314209286.html_1781535234517.html'
MD_PATH = '/home/ubuntu/page_texts/detail.1688.com_offer_981314209286.html.md'
OUTPUT_DIR = '/home/ubuntu/crossborder-ai-listing-workflow/outputs/YZX-CAT-EYE-001'
SUPPLIER_LINK = 'https://detail.1688.com/offer/981314209286.html'
PRODUCT_CODE = 'YZX-CAT-EYE'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- 读取数据 ----
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()
with open(MD_PATH, 'r', encoding='utf-8') as f:
    md = f.read()

soup = BeautifulSoup(html, 'html.parser')

# ---- 1. 提取SKU颜色和库存 ----
# 从markdown中提取颜色名称和库存
sku_pattern = re.compile(r'(一指星河猫眼#\d+)\n库存(\d+)瓶', re.MULTILINE)
sku_matches = sku_pattern.findall(md)
print(f"提取到 {len(sku_matches)} 个SKU")

# ---- 2. 提取SKU缩略图（从HTML img标签）----
# 从HTML中提取SKU缩略图URL（_sum.jpg格式）
sku_thumb_pattern = re.compile(r'(https://cbu01\.alicdn\.com/img/ibank/[^"\']+_sum\.jpg)')
sku_thumbs = sku_thumb_pattern.findall(html)
unique_thumbs = list(dict.fromkeys(sku_thumbs))
print(f"提取到 {len(unique_thumbs)} 个SKU缩略图")

# ---- 3. 提取主图（非缩略图，cib.jpg格式）----
main_img_pattern = re.compile(r'(https://cbu01\.alicdn\.com/img/ibank/[^"\']+cib\.jpg)(?!_)')
main_imgs = main_img_pattern.findall(html)
unique_main = list(dict.fromkeys(main_imgs))
print(f"提取到 {len(unique_main)} 个主图候选")

# 也从webp格式提取（去掉_.webp后缀还原为jpg）
webp_pattern = re.compile(r'(https://cbu01\.alicdn\.com/img/ibank/[^"\']+cib\.jpg)_\.webp')
webp_imgs = webp_pattern.findall(html)
for img in webp_imgs:
    if img not in unique_main:
        unique_main.append(img)
print(f"合并后主图数: {len(unique_main)}")

# ---- 4. 提取价格 ----
price_match = re.search(r'¥\n?(\d+\.\d+)', md)
rmb_price = float(price_match.group(1)) if price_match else 7.20
print(f"价格: ¥{rmb_price}")

# ---- 5. 构建SKU列表 ----
skus = []
for i, (color_name, stock_str) in enumerate(sku_matches):
    num = color_name.replace('一指星河猫眼#', '')
    sku_id = f"{PRODUCT_CODE}-{num.zfill(2)}"
    skus.append({
        "sku_id": sku_id,
        "sku_name": color_name,
        "variant_name_1": "Color",
        "variant_value_1": color_name,
        "stock": min(int(stock_str), 999),  # BigSeller库存上限
        "rmb_cost": rmb_price,
        "weight_g": 55
    })

print(f"构建了 {len(skus)} 个SKU")

# ---- 6. 构建 product.optimized.json ----
optimized = {
    "title": "Cat Eye Gel Nail Polish 15ml Galaxy Series UV LED Soak Off Long Lasting Professional Nail Art Color Gel",
    "parent_sku": "YZX-CAT-EYE",
    "category_id": "102029",
    "description": (
        "Features:\n"
        "1. Stunning galaxy cat eye effect with built-in magnetic particles — no black base coat needed.\n"
        "2. Long-lasting formula, stays up to 21 days without chipping or peeling.\n"
        "3. Soak-off formula, easy to remove without damaging natural nails.\n"
        "4. Compatible with all UV/LED nail lamps (60s cure time).\n"
        "5. Safe, non-toxic, odor-free formula. Certified cosmetic product.\n"
        "6. 36 stunning colors to choose from — from rose gold to midnight galaxy hues.\n\n"
        "How to Use:\n"
        "1. Prep nails: clean, file, and apply base coat, cure.\n"
        "2. Apply a thin layer of cat eye gel.\n"
        "3. While still wet, hold a cat eye magnet close to the nail for 5-10 seconds.\n"
        "4. Cure under UV/LED lamp for 60 seconds.\n"
        "5. Apply top coat and cure again.\n\n"
        "Package Includes:\n"
        "- 1 x Cat Eye Gel Nail Polish (15ml)\n\n"
        "Storage: Keep away from direct sunlight. Store in a cool, dry place.\n"
        "Shelf life: 3 years."
    ),
    "selling_points": [
        "Galaxy cat eye effect with no black base coat needed — one bottle does it all",
        "Ultra long-lasting up to 21 days, no chipping or peeling",
        "Easy soak-off removal, gentle on natural nails",
        "Works with all UV and LED nail lamps",
        "36 colors available — perfect for nail salons and home use",
        "Safe, non-toxic, odor-free certified formula"
    ],
    "brand": "BOMD",
    "weight": 55,
    "length": 5,
    "width": 5,
    "height": 8,
    "condition": 1,
    "supplier_link": SUPPLIER_LINK,
    "lead_time_days": 1,
    "skus": skus
}

opt_path = os.path.join(OUTPUT_DIR, "product.optimized.json")
with open(opt_path, 'w', encoding='utf-8') as f:
    json.dump(optimized, f, ensure_ascii=False, indent=2)
print(f"[OK] product.optimized.json 已写入: {opt_path}")

# ---- 7. 构建 uploaded_image_urls.json ----
# 主图：取前5张（去掉缩略图）
main_image_list = unique_main[:5]

# SKU图：将缩略图映射到SKU
sku_images = {}
for i, (color_name, _) in enumerate(sku_matches):
    num = color_name.replace('一指星河猫眼#', '')
    sku_id = f"{PRODUCT_CODE}-{num.zfill(2)}"
    if i < len(unique_thumbs):
        sku_images[sku_id] = unique_thumbs[i]

img_output = {
    "main": main_image_list[:1],
    "detail": main_image_list[1:],
    "skus": sku_images
}

img_path = os.path.join(OUTPUT_DIR, "uploaded_image_urls.json")
with open(img_path, 'w', encoding='utf-8') as f:
    json.dump(img_output, f, ensure_ascii=False, indent=2)
print(f"[OK] uploaded_image_urls.json 已写入: {img_path}")
print(f"  主图: {len(img_output['main'])} 张")
print(f"  详情图: {len(img_output['detail'])} 张")
print(f"  SKU图: {len(sku_images)} 个")

# ---- 8. 输出摘要 ----
print(f"\n=== 数据摘要 ===")
print(f"产品: {optimized['title']}")
print(f"SKU数: {len(skus)}")
print(f"采购价: ¥{rmb_price}")
print(f"主图URL示例: {main_image_list[0] if main_image_list else 'N/A'}")
