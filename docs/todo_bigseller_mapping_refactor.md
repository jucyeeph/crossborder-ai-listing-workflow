# TODO: BigSeller Mapping Refactor

## Current State

`scripts/generate_bigseller_excel.py` currently still hardcodes part of the BigSeller field columns.

## Problem

When the BigSeller template changes, Python code must be edited and retested.

## Target

Field mapping should be controlled by `configs/bigseller_mapping.example.yaml`.

## Future Behavior

The Python script should read YAML fields:

- `target_column`
- `source`
- `required`
- `default`

## Benefit

Template changes can be handled by editing YAML mapping, without changing the main Python export logic.
