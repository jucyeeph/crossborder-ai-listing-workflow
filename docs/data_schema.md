# 数据结构设计 (Data Schema)

本系统使用统一的 JSON 数据结构串联各个子工作流。

## 1. product.raw.json
原始产品数据，由“资料解析层”生成。

```json
{
  "source_type": "1688_link_or_image_zip",
  "raw_title": "原始商品标题",
  "raw_images": ["image_path_1", "image_path_2"],
  "raw_sku_images": ["sku_image_path_1"],
  "raw_attributes": {
    "brand": "品牌名",
    "material": "材质"
  },
  "raw_price": {
    "min": 10.5,
    "max": 15.0
  },
  "raw_description": "原始商品描述文本",
  "supplier_info": {
    "name": "供应商名称",
    "link": "供应商链接"
  }
}
```

## 2. product.optimized.json
优化后的产品数据，适合目标市场（如菲律宾）。

```json
{
  "title": "英文商品标题",
  "selling_points": [
    "卖点1",
    "卖点2"
  ],
  "description": "详细英文描述",
  "skus": [
    {
      "sku_id": "SKU_01",
      "sku_name": "优化后的SKU名称",
      "original_sku_name": "原始SKU名称"
    }
  ],
  "keywords": {
    "primary": ["关键词1"],
    "secondary": ["关键词2"]
  }
}
```

## 3. uploaded_image_urls.json
图片上传到图床后的直链。

```json
{
  "main": ["https://cdn.example.com/main_01.jpg"],
  "detail": ["https://cdn.example.com/detail_01.jpg"],
  "skus": {
    "SKU_01": "https://cdn.example.com/sku_01.jpg"
  }
}
```

## 4. product.pricing.json
包含各SKU定价信息的数据。

```json
{
  "skus": [
    {
      "sku": "SKU_01",
      "rmb_cost": 5.2,
      "estimated_php_cost": 42.64,
      "suggested_original_price": 109,
      "suggested_sale_price": 89,
      "campaign_price": 79,
      "estimated_net_receive": 57.3,
      "estimated_margin": 14.66,
      "margin_warning": false
    }
  ]
}
```
