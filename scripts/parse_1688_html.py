"""
parse_1688_html.py
------------------
从已保存的1688产品页面HTML中提取产品数据，
输出 product.raw.json（原始数据）和 uploaded_image_urls.json（图片URL列表）。

用法:
    python scripts/parse_1688_html.py \
        --html /path/to/1688_page.html \
        --output_dir outputs/<product_code>/
"""

import argparse
import json
import re
import os
from bs4 import BeautifulSoup


def extract_context_data(html: str) -> dict:
    """从页面脚本中提取 window.context 数据"""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script'):
        if script.string and 'offerDetail' in script.string:
            # 提取 JSON 对象
            match = re.search(r'window\.context=\(function\(.*?\)\s*\(.*?,\s*(\{.*\})\s*\)\s*;', 
                              script.string, re.DOTALL)
            if not match:
                # 备用方式
                match = re.search(r'window\.context\s*=.*?(\{\"result\".*?\});?\s*$', 
                                  script.string, re.DOTALL | re.MULTILINE)
            if match:
                try:
                    # 找到最后一个参数（完整JSON对象）
                    text = script.string
                    # 找到 (function(b,d){...})(window.contextPath, {...}) 的第二个参数
                    brace_start = text.rfind(',({"result"')
                    if brace_start == -1:
                        brace_start = text.rfind(',{"result"')
                    if brace_start != -1:
                        json_str = text[brace_start+1:]
                        # 找到匹配的结束括号
                        depth = 0
                        end_pos = 0
                        for i, ch in enumerate(json_str):
                            if ch == '{':
                                depth += 1
                            elif ch == '}':
                                depth -= 1
                                if depth == 0:
                                    end_pos = i + 1
                                    break
                        json_str = json_str[:end_pos]
                        return json.loads(json_str)
                except Exception as e:
                    print(f"[WARN] JSON解析失败: {e}")
    return {}


def extract_sku_info(data: dict) -> list:
    """提取SKU规格和价格"""
    skus = []
    try:
        # 尝试从 skuModel 提取
        sku_model = data.get('result', {}).get('data', {}).get('skuModel', {})
        sku_props = sku_model.get('skuProps', [])
        sku_map = sku_model.get('skuMap', {})
        price_range = sku_model.get('priceRange', {})
        
        # 获取重量信息
        piece_weight_info = []
        try:
            pack_info = data['result']['data']['productPackInfo']['fields']['pieceWeightScale']['pieceWeightScaleInfo']
            piece_weight_info = pack_info
        except (KeyError, TypeError):
            pass
        weight_map = {p.get('sku1', ''): p.get('weight', 0) for p in piece_weight_info}
        
        if sku_props:
            # 有规格属性
            prop1 = sku_props[0] if len(sku_props) > 0 else {}
            prop2 = sku_props[1] if len(sku_props) > 1 else {}
            
            for sku_key, sku_val in sku_map.items():
                parts = sku_key.split('||')
                val1 = parts[0] if len(parts) > 0 else ''
                val2 = parts[1] if len(parts) > 1 else ''
                
                price = sku_val.get('price', '')
                if isinstance(price, dict):
                    price = price.get('priceText', price.get('price', ''))
                
                sku_id_raw = sku_val.get('skuId', '')
                weight = weight_map.get(val1, 55)
                
                skus.append({
                    'sku_id_raw': str(sku_id_raw),
                    'variant_name_1': prop1.get('prop', '颜色'),
                    'variant_value_1': val1,
                    'variant_name_2': prop2.get('prop', '') if val2 else '',
                    'variant_value_2': val2,
                    'rmb_price': str(price),
                    'weight_g': weight,
                })
        else:
            # 无规格，单SKU
            min_price = price_range.get('minPrice', {}).get('priceText', '')
            skus.append({
                'sku_id_raw': '',
                'variant_name_1': '',
                'variant_value_1': '',
                'variant_name_2': '',
                'variant_value_2': '',
                'rmb_price': str(min_price),
                'weight_g': 55,
            })
    except Exception as e:
        print(f"[WARN] SKU提取失败: {e}")
    
    return skus


def extract_images(data: dict, soup: BeautifulSoup) -> dict:
    """提取主图和详情图"""
    images = {'main': [], 'detail': []}
    
    try:
        # 主图从 offerDetail 提取
        offer_detail = data.get('result', {}).get('data', {}).get('offerDetail', {})
        img_list = offer_detail.get('imgList', [])
        for img in img_list:
            url = img if isinstance(img, str) else img.get('url', '')
            if url:
                if not url.startswith('http'):
                    url = 'https:' + url
                images['main'].append(url)
    except Exception as e:
        print(f"[WARN] 主图提取失败: {e}")
    
    # 如果主图没提取到，从HTML img标签提取
    if not images['main']:
        for img in soup.find_all('img'):
            src = img.get('src', '') or img.get('data-src', '')
            if src and ('img.alicdn.com' in src or 'cbu01.alicdn.com' in src):
                if not src.startswith('http'):
                    src = 'https:' + src
                if src not in images['main']:
                    images['main'].append(src)
    
    return images


def extract_title_and_desc(data: dict, soup: BeautifulSoup) -> tuple:
    """提取标题和描述"""
    title = ''
    description = ''
    
    try:
        offer_detail = data.get('result', {}).get('data', {}).get('offerDetail', {})
        title = offer_detail.get('subject', '')
        if not title:
            title = soup.title.string.replace(' - 阿里巴巴', '').strip() if soup.title else ''
    except Exception:
        title = soup.title.string.replace(' - 阿里巴巴', '').strip() if soup.title else ''
    
    return title, description


def main():
    parser = argparse.ArgumentParser(description="解析1688产品页面HTML")
    parser.add_argument("--html", required=True, help="已保存的HTML文件路径")
    parser.add_argument("--output_dir", required=True, help="输出目录")
    parser.add_argument("--supplier_link", default="", help="供应商链接")
    args = parser.parse_args()

    with open(args.html, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    data = extract_context_data(html)
    
    if not data:
        print("[ERROR] 无法从HTML中提取产品数据，页面可能未完全加载")
        exit(1)

    title, description = extract_title_and_desc(data, soup)
    skus = extract_sku_info(data)
    images = extract_images(data, soup)

    print(f"[INFO] 标题: {title}")
    print(f"[INFO] SKU数量: {len(skus)}")
    print(f"[INFO] 主图数量: {len(images['main'])}")

    # 输出原始数据
    raw = {
        "title_cn": title,
        "supplier_link": args.supplier_link,
        "skus_raw": skus,
        "images": images,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    raw_path = os.path.join(args.output_dir, "product.raw.json")
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"[OK] 原始数据已写入: {raw_path}")

    # 输出图片URL
    img_path = os.path.join(args.output_dir, "uploaded_image_urls.json")
    img_output = {
        "main": images['main'][:1],
        "detail": images['main'][1:9],
        "skus": {}
    }
    with open(img_path, 'w', encoding='utf-8') as f:
        json.dump(img_output, f, ensure_ascii=False, indent=2)
    print(f"[OK] 图片URL已写入: {img_path}")


if __name__ == "__main__":
    main()
