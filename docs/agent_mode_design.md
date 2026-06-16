# Agent Mode Design

## Current State

`scripts/interactive_product_optimize.py` depends on `input()` and is suitable for manual product-field confirmation.

## Problem

Agent use of stdin interaction is unstable. It can block, provide the wrong response to a prompt, or overwrite product fields without a structured decision record.

## Target Modes

### interactive

The user manually confirms each product field and pricing decision.

### agent

The script reads `review_decisions.json` or `product_brief.json` and runs without stdin prompts.

### dry-run

The script generates suggestions and warnings without overwriting existing product files.

## Future Input Files

- `review_decisions.json`
- `product_brief.json`

## Future Output Files

- `product.optimized.json`
- `product_copywriting.md`
- `warnings.md`

## Pricing Boundary

Formal pricing source of truth is `scripts/calculate_pricing.py`. The pricing step inside `interactive_product_optimize.py` is a temporary manual confirmation helper and should not remain the formal pricing implementation.
