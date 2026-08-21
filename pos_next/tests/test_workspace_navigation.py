import csv
import json
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


class TestPOSWorkspaceNavigation(unittest.TestCase):
	def test_sidebar_is_app_owned_grouped_and_uses_pos_icon(self):
		sidebar = json.loads((APP_ROOT / "workspace_sidebar/pos.json").read_text(encoding="utf-8"))
		items = sidebar["items"]

		self.assertEqual(sidebar["app"], "pos_next")
		self.assertEqual(sidebar["header_icon"], "shopping-cart")
		self.assertEqual(sidebar["standard"], 1)
		self.assertEqual(items[0]["link_to"], "POS")
		self.assertEqual(items[1]["url"], "/pos/")
		self.assertEqual(
			[item["label"] for item in items if item["type"] == "Section Break"],
			[
				"Daily Operations",
				"Catalog & Inventory",
				"Operational Reports",
				"Financial Overview",
				"POS Configuration",
				"Offers & Coupons",
			],
		)

	def test_desktop_icon_and_workspace_use_the_same_pos_icon(self):
		desktop_icon = json.loads((APP_ROOT / "desktop_icon/pos.json").read_text(encoding="utf-8"))
		workspace = json.loads((APP_ROOT / "pos_next/workspace/pos/pos.json").read_text(encoding="utf-8"))

		self.assertEqual(desktop_icon["icon"], "shopping-cart")
		self.assertEqual(desktop_icon["link_type"], "Workspace Sidebar")
		self.assertEqual(desktop_icon["link_to"], "POS")
		self.assertEqual(len(desktop_icon["roles"]), 9)
		self.assertEqual(workspace["icon"], "shopping-cart")
		content = json.loads(workspace["content"])
		self.assertEqual(content[0]["type"], "header")
		self.assertTrue(any(block["type"] == "card" for block in content))
		self.assertTrue(any(block["data"].get("shortcut_name") == "Start Selling" for block in content))

	def test_sidebar_sections_have_arabic_translations(self):
		with (APP_ROOT / "translations/ar.csv").open(newline="", encoding="utf-8") as translations_file:
			translations = {row[0]: row[1] for row in csv.reader(translations_file) if len(row) >= 2}

		for label in (
			"Home",
			"Start Selling",
			"Daily Operations",
			"Catalog & Inventory",
			"Operational Reports",
			"Financial Overview",
			"POS Configuration",
			"Offers & Coupons",
		):
			self.assertTrue(translations.get(label), label)


if __name__ == "__main__":
	unittest.main()
