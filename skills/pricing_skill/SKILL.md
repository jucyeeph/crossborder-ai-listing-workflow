# Pricing Skill

## When to use

Use this Skill when a product already has structured optimized data and needs repeatable Shopee PH / cross-border pricing output for downstream ERP export.

## Inputs

- `product.optimized.json`
- `configs/pricing_config.example.json` or an equivalent reviewed pricing config

## Outputs

- `product.pricing.json`

## Preconditions

- `product.optimized.json` must contain a non-empty `skus` array.
- Each SKU that should be priced must include `sku_id` and `rmb_cost`.
- The pricing config must include currency, platform, pricing, and campaign sections.

## Procedure

1. Confirm the product directory contains `product.optimized.json`.
2. Confirm the pricing config is the intended config for the target platform.
3. Run the command below.
4. Review terminal warnings, especially missing `rmb_cost` or low-margin warnings.
5. Confirm `product.pricing.json` can be consumed by BigSeller Export Skill.

## Command

```bash
python scripts/calculate_pricing.py \
  --optimized outputs/<product_code>/product.optimized.json \
  --config configs/pricing_config.example.json \
  --output outputs/<product_code>/product.pricing.json
```

## Success Criteria

- Every intended SKU has a pricing entry.
- Every priced SKU has cost, estimated PHP cost, suggested sale price, campaign price, estimated net receive, and estimated margin.
- Low-profit SKUs are surfaced with `margin_warning`.
- Output JSON is valid and can be used by `scripts/generate_bigseller_excel.py`.

## Failure Handling

- If `skus` is empty, stop and fix `product.optimized.json`.
- If a SKU is missing `rmb_cost`, add or confirm cost data before using the output.
- If many SKUs have low margin, review pricing config before export.
- Do not continue to BigSeller export with incomplete pricing.

## Do Not

- Do not invent prices manually inside the Skill.
- Do not copy a second pricing formula into another script.
- Do not skip minimum margin checks.
- Do not call real marketplace, ERP, image-hosting, or supplier APIs.

## Source of Truth

The formal pricing source of truth is `scripts/calculate_pricing.py`.
`scripts/interactive_product_optimize.py` may remain as a manual interaction helper, but it should not be treated as the long-term formal pricing authority.
