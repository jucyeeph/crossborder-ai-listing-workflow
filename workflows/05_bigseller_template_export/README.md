# 子工作流 5：BigSeller ERP 模板化上传工作流

## 目标
根据 BigSeller 创建产品模板，把前面生成的产品信息、图片 URL、价格、SKU 等内容填入模板，生成可直接导入 ERP 的表格。

## 输入
- `product.optimized.json`
- `uploaded_image_urls.json`
- `product.pricing.json`
- `bigseller_template.xlsx`
- `bigseller_mapping.yaml`

## 输出
- `bigseller_product_upload.xlsx`
- `erp_upload_report.md`
