from __future__ import annotations

import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SQL = {
    "sql/00_source_profiling/01_table_inventory.sql",
    "sql/00_source_profiling/02_source_quality_and_keys.sql",
    "sql/01_staging/01_stg_orders.sql",
    "sql/01_staging/02_stg_order_items.sql",
    "sql/01_staging/03_stg_order_payments.sql",
    "sql/01_staging/04_stg_marketing_funnel.sql",
    "sql/02_marts/01_mart_orders.sql",
    "sql/02_marts/02_mart_order_seller.sql",
    "sql/02_marts/03_mart_marketing_funnel.sql",
    "sql/02_marts/04_mart_seller_lifecycle.sql",
    "sql/03_analysis/01_acquisition_channel_quality.sql",
    "sql/03_analysis/02_seller_activation_performance.sql",
    "sql/03_analysis/03_delivery_review_analysis.sql",
    "sql/04_quality_checks/01_join_fanout_reconciliation.sql",
    "sql/04_quality_checks/02_final_kpi_validation.sql",
}

EXPECTED_PAGES = {
    "01 Executive Overview": 10,
    "02 Acquisition Funnel": 12,
    "03 Seller Performance": 12,
    "04 Fulfilment and CX": 11,
    "05 Seller Detail": 9,
}


class RepositoryStructureTests(unittest.TestCase):
    def test_expected_sql_files(self) -> None:
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "sql").rglob("*.sql")
        }
        self.assertEqual(EXPECTED_SQL, actual)

    def test_sql_targets_expected_bigquery_project(self) -> None:
        for relative in EXPECTED_SQL:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("olist-marketplace-analytics", text, relative)
            self.assertNotIn("company.raw.employees", text, relative)

    def test_required_public_documentation(self) -> None:
        required = [
            ROOT / "README.md",
            ROOT / "docs" / "data_inventory.md",
            ROOT / "powerbi" / "README.md",
        ]
        for path in required:
            self.assertTrue(path.is_file(), path)

    def test_repository_excludes_internal_artifacts(self) -> None:
        forbidden_suffixes = {".docx", ".pdf"}
        forbidden = [
            path
            for path in ROOT.rglob("*")
            if ".git" not in path.parts
            and (
                path.name == ".gitkeep"
                or (path.is_file() and path.suffix.lower() in forbidden_suffixes)
            )
        ]
        self.assertEqual([], forbidden)


class PowerBIArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pbix = ROOT / "powerbi" / "Olist_Marketplace_Analytics_Portfolio.pbix"

    def test_pbix_is_within_github_file_limit(self) -> None:
        self.assertTrue(self.pbix.is_file())
        self.assertLess(self.pbix.stat().st_size, 100 * 1024 * 1024)

    def test_pbix_container_and_report_structure(self) -> None:
        self.assertTrue(zipfile.is_zipfile(self.pbix))
        with zipfile.ZipFile(self.pbix, "r") as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn("DataModel", archive.namelist())
            self.assertIn("Report/Layout", archive.namelist())
            layout = json.loads(archive.read("Report/Layout").decode("utf-16le"))
            pages = {
                page["displayName"]: len(page.get("visualContainers", []))
                for page in layout["sections"]
            }
            self.assertEqual(EXPECTED_PAGES, pages)
            self.assertEqual(54, sum(pages.values()))

            theme_member = next(
                name
                for name in archive.namelist()
                if "BaseThemes" in name and name.endswith(".json")
            )
            theme = json.loads(archive.read(theme_member).decode("utf-8-sig"))
            self.assertEqual("Olist Portfolio Theme", theme.get("name"))


if __name__ == "__main__":
    unittest.main()
