# BigSeller ERP 模板字段映射指南

## 1. 模板概览
模板包含 31 个列，其中带 `*` 的为必填项。

| 列号 | 字段名称 | 必填 | 说明 | 映射来源 |
|---|---|---|---|---|
| 1 | 分类ID* | 是 | 平台分类ID | 平台规则配置/默认值 |
| 2 | 产品名称* | 是 | 商品标题 | `product.optimized.json` -> `title` |
| 3 | 供应商链接 | 否 | 采购链接 | `product.raw.json` -> `supplier_info.link` |
| 4 | Parent SKU | 否 | 父SKU，用于关联变种 | 自动生成（如基于日期+商品码） |
| 5 | 产品描述* | 是 | 详情描述 | `product.optimized.json` -> `description` |
| 6 | 变种名称1 | 否 | 一级规格名称（如Color） | `product.optimized.json` -> `skus[].variant_name_1` |
| 7 | 变种选项1 | 否 | 一级规格值（如Black） | `product.optimized.json` -> `skus[].variant_value_1` |
| 8 | 变种名称2 | 否 | 二级规格名称（如Size） | `product.optimized.json` -> `skus[].variant_name_2` |
| 9 | 变种选项2 | 否 | 二级规格值（如S） | `product.optimized.json` -> `skus[].variant_value_2` |
| 10 | SKU | 否 | 子SKU编号 | `product.optimized.json` -> `skus[].sku_id` |
| 11 | 库存* | 是 | 变种库存数量 | 默认值（如100） |
| 12 | 价格* | 是 | 变种售价 | `product.pricing.json` -> `skus[].suggested_sale_price` |
| 13 | 折扣活动ID | 否 | | 留空 |
| 14 | 促销价 | 否 | | `product.pricing.json` -> `skus[].campaign_price` |
| 15 | 变种图 | 否 | 变种图片链接 | `uploaded_image_urls.json` -> `skus[{sku_id}]` |
| 16 | 产品主图* | 是 | 主图链接 | `uploaded_image_urls.json` -> `main[0]` |
| 17 | 产品附属图1 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[0]` |
| 18 | 产品附属图2 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[1]` |
| 19 | 产品附属图3 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[2]` |
| 20 | 产品附属图4 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[3]` |
| 21 | 产品附属图5 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[4]` |
| 22 | 产品附属图6 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[5]` |
| 23 | 产品附属图7 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[6]` |
| 24 | 产品附属图8 | 否 | 附属图链接 | `uploaded_image_urls.json` -> `detail[7]` |
| 25 | 尺码表ID / 尺码图 | 否 | | 留空或特定图片 |
| 26 | 重量（g）* | 是 | 包装重量 | 默认值（如200）或配置提取 |
| 27 | 长（cm） | 否 | 包装长度 | 默认值（如10） |
| 28 | 宽（cm） | 否 | 包装宽度 | 默认值（如10） |
| 29 | 高（cm） | 否 | 包装高度 | 默认值（如10） |
| 30 | 发货期（天） | 否 | 预售天数 | 留空或默认值（如2） |
| 31 | 物品状况 | 否 | 1为全新 | 默认值 `1` |

## 2. 数据映射规则

### 多SKU处理逻辑
BigSeller 模板中，如果一个商品有多个变种（SKU），其**分类ID、产品名称、产品描述、产品主图、重量**等公共字段在第一行必须填写，后续行可以留空或重复填写。
变种相关字段（变种名称、变种选项、SKU、库存、价格、变种图）则需要在每一行对应填写。

### 必填项校验
在生成 Excel 前，脚本必须校验：
1. `分类ID` 不为空
2. `产品名称` 不为空
3. `产品描述` 不为空
4. 每个变种的 `库存` 不为空
5. 每个变种的 `价格` 不为空
6. `产品主图` 不为空
7. `重量（g）` 不为空
