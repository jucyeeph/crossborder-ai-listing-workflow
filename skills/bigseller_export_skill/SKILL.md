# BigSeller Export Skill

## When to use

Use this Skill after optimized product data, image URLs, and pricing data are ready and the user needs a BigSeller import workbook plus an ERP upload report.

## Inputs

- `product.optimized.json`
- `uploaded_image_urls.json`
- `product.pricing.json`
- `templates/bigseller_template.xlsx`
- `configs/bigseller_mapping.example.yaml`

## Outputs

- `bigseller_product_upload.xlsx`
- `erp_upload_report.md`

## Preconditions

- `product.optimized.json` contains title, category, description, dimensions or defaults, and SKUs.
- `uploaded_image_urls.json` contains stable product image URLs, including at least one main image.
- `product.pricing.json` contains pricing for each SKU.
- The BigSeller template file exists and opens successfully.

## Procedure

1. Confirm all inputs exist in the same product working directory or at the supplied paths.
2. Confirm `uploaded_image_urls.json` contains stable hosted URLs, not raw supplier URLs.
3. Run the command below.
4. Open or inspect the generated workbook.
5. Read `erp_upload_report.md` and fix any errors before importing into BigSeller.

## Command

```bash
python scripts/generate_bigseller_excel.py \
  --optimized outputs/<product_code>/product.optimized.json \
  --images outputs/<product_code>/uploaded_image_urls.json \
  --pricing outputs/<product_code>/product.pricing.json \
  --template templates/bigseller_template.xlsx \
  --output outputs/<product_code>/bigseller_product_upload.xlsx \
  --report outputs/<product_code>/erp_upload_report.md
```

## Success Criteria

- Excel file opens.
- Header row matches the BigSeller template.
- Required fields are non-empty.
- SKU row count matches `product.optimized.json`.
- Price fields are numeric.
- Main image URL is non-empty and starts with `http`.
- ERP upload report is generated and lists errors or warnings.

## Failure Handling

- If required fields are empty, fix the source JSON and rerun export.
- If SKU rows do not match, compare optimized SKUs against pricing SKUs.
- If image URLs are missing or unstable supplier URLs, stop and fix the image pipeline boundary first.
- If the template changes, inspect field mapping before changing script behavior.

## Do Not

- Do not log in to BigSeller.
- Do not auto-publish products.
- Do not silently ignore missing required fields.
- Do not modify the original template file.
- Do not use example outputs as the formal data source.

## Technical Debt

`scripts/generate_bigseller_excel.py` still hardcodes part of the BigSeller field columns in Python. Future work should make the export YAML-driven through `configs/bigseller_mapping.example.yaml`, so BigSeller template changes require mapping updates instead of Python logic changes.
