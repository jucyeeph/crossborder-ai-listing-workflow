# 子工作流 3：电商图片生成与图床上传工作流

## 目标
根据供应商图片和产品信息，生成更适合菲律宾市场的电商图片，并上传到稳定图床，返回可用于 ERP 的图片 URL。

## 输入
- `raw_images/`
- `product.optimized.json`
- `image_style_guide.md`

## 输出
- `generated_images/`
- `uploaded_image_urls.json`
- `image_report.md`
