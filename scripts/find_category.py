"""
find_category.py
----------------
根据关键词在 Shopee PH 分类数据中搜索对应的 Category ID。

用法:
    python scripts/find_category.py "nail polish"
"""

import argparse
import json
import os

CATEGORIES_FILE = os.path.join(
    os.path.dirname(__file__), 
    "..", "configs", "categories", "shopee_ph_categories.json"
)

def main():
    parser = argparse.ArgumentParser(description="搜索 Shopee PH 分类ID")
    parser.add_argument("keyword", help="搜索关键词 (不区分大小写)")
    args = parser.parse_args()

    if not os.path.exists(CATEGORIES_FILE):
        print(f"[ERROR] 找不到分类数据文件: {CATEGORIES_FILE}")
        exit(1)

    with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
        categories = json.load(f)

    keyword = args.keyword.lower()
    results = []

    for cat in categories:
        # 拼接完整的分类路径字符串
        path_str = " > ".join([
            cat.get("category", ""),
            cat.get("sub_category", ""),
            cat.get("level_3", ""),
            cat.get("level_4", ""),
            cat.get("level_5", "")
        ]).replace(" > -", "")
        
        if keyword in path_str.lower():
            results.append({
                "id": cat.get("category_id"),
                "path": path_str
            })

    if not results:
        print(f"未找到包含 '{args.keyword}' 的分类。")
        return

    print(f"找到 {len(results)} 个匹配的分类:\n")
    for res in results:
        print(f"ID: {res['id']:<8} | {res['path']}")

if __name__ == "__main__":
    main()
