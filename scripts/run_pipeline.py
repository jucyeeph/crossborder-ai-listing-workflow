"""
Run the stable MVP listing workflow.

This orchestrator only connects deterministic local scripts:

product.optimized.json + uploaded_image_urls.json
    -> calculate_pricing.py
    -> generate_bigseller_excel.py

It does not call 1688, BigSeller, image generation, image hosting, or any
external API.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"[ERROR] Missing {label}: {path}")


def run_step(name: str, command: list[str]) -> None:
    print(f"[RUN] {name}")
    print("      " + " ".join(command))
    subprocess.run(command, check=True)
    print(f"[OK] {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pricing and BigSeller export pipeline")
    parser.add_argument("--product-dir", required=True, help="Directory containing product.optimized.json and uploaded_image_urls.json")
    parser.add_argument("--template", required=True, help="BigSeller template xlsx path")
    parser.add_argument("--pricing-config", required=True, help="Pricing config JSON path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    product_dir = Path(args.product_dir).resolve()
    template_path = Path(args.template).resolve()
    pricing_config_path = Path(args.pricing_config).resolve()

    optimized_path = product_dir / "product.optimized.json"
    images_path = product_dir / "uploaded_image_urls.json"
    pricing_path = product_dir / "product.pricing.json"
    excel_path = product_dir / "bigseller_product_upload.xlsx"
    report_path = product_dir / "erp_upload_report.md"

    require_file(optimized_path, "product.optimized.json")
    require_file(images_path, "uploaded_image_urls.json")
    require_file(template_path, "BigSeller template")
    require_file(pricing_config_path, "pricing config")
    os.makedirs(product_dir, exist_ok=True)

    run_step(
        "calculate pricing",
        [
            sys.executable,
            str(repo_root / "scripts" / "calculate_pricing.py"),
            "--optimized",
            str(optimized_path),
            "--config",
            str(pricing_config_path),
            "--output",
            str(pricing_path),
        ],
    )

    run_step(
        "generate BigSeller Excel",
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_bigseller_excel.py"),
            "--optimized",
            str(optimized_path),
            "--images",
            str(images_path),
            "--pricing",
            str(pricing_path),
            "--template",
            str(template_path),
            "--output",
            str(excel_path),
            "--report",
            str(report_path),
        ],
    )

    print("[DONE] Pipeline completed")
    print(f"       pricing: {pricing_path}")
    print(f"       excel:   {excel_path}")
    print(f"       report:  {report_path}")


if __name__ == "__main__":
    main()
