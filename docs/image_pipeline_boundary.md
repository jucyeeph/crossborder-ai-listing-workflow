# Image Pipeline Boundary

## Current State

The project may currently use 1688 or supplier image URLs directly during sample generation.

## Problem

Supplier URLs are not stable hosted image URLs controlled by this workflow. They can expire, change, block hotlinking, or fail later during ERP import.

## Correct Data Layers

- `raw_image_urls.json`
- `downloaded_images/`
- `processed_images/`
- `uploaded_image_urls.json`

## Rule

Only URLs uploaded to a stable image host controlled by this workflow may be written to `uploaded_image_urls.json`.

## Future Work

- Cloudflare R2 upload support
- Custom image domain
- Batch upload script
- URL reachability checks
- Distinct reports for raw, processed, and uploaded image assets
