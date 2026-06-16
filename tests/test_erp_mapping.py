"""
Validate repeatable BigSeller export behavior from fixtures.

Run:
    python tests/test_erp_mapping.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
TEMPLATE_PATH = REPO_ROOT / "templates" / "bigseller_template.xlsx"
PRICING_CONFIG_PATH = REPO_ROOT / "configs" / "pricing_config.example.json"
REQUIRED_COLS = {"分类ID*", "产品名称*", "产品描述*", "库存*", "价格*", "产品主图*", "重量（g）*"}


def run_command(args):
    return subprocess.run(args, cwd=REPO_ROOT, check=True, text=True, capture_output=True)


class BigSellerExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.product_dir = Path(self.tmp.name)
        shutil.copy(FIXTURES_DIR / "product.optimized.json", self.product_dir / "product.optimized.json")
        shutil.copy(FIXTURES_DIR / "uploaded_image_urls.json", self.product_dir / "uploaded_image_urls.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_generate_bigseller_excel_from_fixtures(self):
        pricing_path = self.product_dir / "product.pricing.json"
        excel_path = self.product_dir / "bigseller_product_upload.xlsx"
        report_path = self.product_dir / "erp_upload_report.md"

        run_command([
            sys.executable,
            "scripts/calculate_pricing.py",
            "--optimized",
            str(self.product_dir / "product.optimized.json"),
            "--config",
            str(PRICING_CONFIG_PATH),
            "--output",
            str(pricing_path),
        ])
        run_command([
            sys.executable,
            "scripts/generate_bigseller_excel.py",
            "--optimized",
            str(self.product_dir / "product.optimized.json"),
            "--images",
            str(self.product_dir / "uploaded_image_urls.json"),
            "--pricing",
            str(pricing_path),
            "--template",
            str(TEMPLATE_PATH),
            "--output",
            str(excel_path),
            "--report",
            str(report_path),
        ])

        self.assert_export_outputs(excel_path, pricing_path, report_path)

    def test_run_pipeline_generates_pricing_excel_and_report(self):
        pricing_path = self.product_dir / "product.pricing.json"
        excel_path = self.product_dir / "bigseller_product_upload.xlsx"
        report_path = self.product_dir / "erp_upload_report.md"

        run_command([
            sys.executable,
            "scripts/run_pipeline.py",
            "--product-dir",
            str(self.product_dir),
            "--template",
            str(TEMPLATE_PATH),
            "--pricing-config",
            str(PRICING_CONFIG_PATH),
        ])

        self.assert_export_outputs(excel_path, pricing_path, report_path)

    def assert_export_outputs(self, excel_path, pricing_path, report_path):
        self.assertTrue(pricing_path.exists(), "pricing JSON should be generated")
        self.assertTrue(excel_path.exists(), "Excel file should be generated")
        self.assertTrue(report_path.exists(), "ERP report should be generated")

        with open(FIXTURES_DIR / "product.optimized.json", "r", encoding="utf-8") as f:
            optimized = json.load(f)
        with open(pricing_path, "r", encoding="utf-8") as f:
            pricing = json.load(f)

        workbook = openpyxl.load_workbook(excel_path)
        worksheet = workbook.active
        headers = [cell.value for cell in worksheet[1]]
        header_index = {header: index for index, header in enumerate(headers)}
        data_rows = list(worksheet.iter_rows(min_row=2, values_only=True))

        self.assertTrue(REQUIRED_COLS.issubset(set(headers)))
        self.assertEqual(len(optimized["skus"]), len(data_rows))

        for col in REQUIRED_COLS:
            idx = header_index[col]
            self.assertTrue(all(row[idx] not in (None, "") for row in data_rows), col)

        price_idx = header_index["价格*"]
        self.assertTrue(all(isinstance(row[price_idx], (int, float)) for row in data_rows))

        main_img_idx = header_index["产品主图*"]
        self.assertTrue(all(str(row[main_img_idx]).startswith("http") for row in data_rows))

        self.assertEqual(len(optimized["skus"]), len(pricing.get("skus", [])))
        self.assertIn("ERP 上传报告", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
