"""
extract_1688_data.py
--------------------
从已保存的1688产品页面HTML中提取产品数据，使用多种策略。
"""

import json
import re
import os
from bs4 import BeautifulSoup

HTML_PATH = '/home/ubuntu/browser_html/detail_1688_com_981314209286.html_1781535049307.html'
OUTPUT_DIR = '/home/ubuntu/crossborder-ai-listing-workflow/outputs/YZX-CAT-EYE-001'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 提取标题
title = soup.title.string.replace(' - 阿里巴巴', '').strip() if soup.title else ''
print(f"标题: {title}")

# 找到包含产品数据的脚本
all_scripts = soup.find_all('script')
target_script = None
for s in all_scripts:
    if s.string and 'offerDetail' in s.string and 'skuModel' in s.string:
        target_script = s.string
        break

if not target_script:
    print("[ERROR] 未找到产品数据脚本")
    exit(1)

print(f"脚本长度: {len(target_script)}")

# 策略1: 提取 skuModel 部分
sku_match = re.search(r'"skuModel"\s*:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', target_script)
if sku_match:
    print("找到 skuModel")
    try:
        sku_data = json.loads(sku_match.group(1))
        print(json.dumps(sku_data, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"skuModel 解析失败: {e}")

# 策略2: 提取 pieceWeightScale 重量信息
weight_match = re.search(r'"pieceWeightScaleInfo"\s*:\s*(\[.*?\])', target_script, re.DOTALL)
if weight_match:
    print("\n找到重量数据:")
    try:
        weight_data = json.loads(weight_match.group(1))
        for item in weight_data[:5]:
            print(f"  SKU: {item.get('sku1','')}, 重量: {item.get('weight',0)}g")
        print(f"  ...共 {len(weight_data)} 条")
    except Exception as e:
        print(f"重量数据解析失败: {e}")

# 策略3: 提取 imgList 图片
img_match = re.search(r'"imgList"\s*:\s*(\[.*?\])', target_script, re.DOTALL)
if img_match:
    print("\n找到图片列表:")
    try:
        img_data = json.loads(img_match.group(1))
        for url in img_data[:5]:
            print(f"  {url}")
        print(f"  ...共 {len(img_data)} 张")
    except Exception as e:
        print(f"图片列表解析失败: {e}")

# 策略4: 提取 priceRange
price_match = re.search(r'"priceRange"\s*:\s*(\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*\})', target_script)
if price_match:
    print("\n找到价格范围:")
    try:
        price_data = json.loads(price_match.group(1))
        print(json.dumps(price_data, ensure_ascii=False, indent=2)[:500])
    except Exception as e:
        print(f"价格解析失败: {e}")

# 策略5: 直接用正则提取所有颜色SKU
print("\n\n=== 提取SKU颜色列表 ===")
# 找 skuMap 中的键
sku_keys = re.findall(r'"(一指星河猫眼#\d+[^"]*)"', target_script)
print(f"找到 {len(sku_keys)} 个颜色SKU:")
for k in sku_keys[:20]:
    print(f"  {k}")

# 策略6: 提取 skuProps
props_match = re.search(r'"skuProps"\s*:\s*(\[.*?\])\s*,\s*"skuMap"', target_script, re.DOTALL)
if props_match:
    print("\n找到 skuProps:")
    try:
        props_data = json.loads(props_match.group(1))
        print(json.dumps(props_data, ensure_ascii=False, indent=2)[:1000])
    except Exception as e:
        print(f"skuProps 解析失败: {e}")
        print("原始内容前500字:", props_match.group(1)[:500])
