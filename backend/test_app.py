import tempfile
import unittest
from pathlib import Path

import app as beer_app


class BeerHouseAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        beer_app.DB_PATH = base / "test.db"
        beer_app.UPLOAD_FOLDER = base / "uploads"
        beer_app.BACKUP_FOLDER = base / "backups"
        beer_app.app.config["UPLOAD_FOLDER"] = str(beer_app.UPLOAD_FOLDER)
        beer_app.sessions.clear()
        beer_app.init_db()
        self.client = beer_app.app.test_client()

    def tearDown(self):
        beer_app.sessions.clear()
        self.tmp.cleanup()

    def login(self, username, password):
        response = self.client.post("/api/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.get_json()["token"]

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_admin_and_seller_login_inventory_dashboard_exports(self):
        admin = self.login("admin", "admin123")
        seller = self.login("vendedor", "vendedor123")

        products = self.client.get("/api/products", headers=self.auth(seller))
        self.assertEqual(products.status_code, 200)
        self.assertGreater(len(products.get_json()["products"]), 0)

        summary = self.client.get("/api/reports/summary", headers=self.auth(admin))
        self.assertEqual(summary.status_code, 200)
        summary_json = summary.get_json()
        self.assertIn("net_profit", summary_json["cash_cut"])
        self.assertIn("expenses", summary_json["totals"]["monthly"])

        excel = self.client.get("/api/reports/export/excel", headers=self.auth(admin))
        self.assertEqual(excel.status_code, 200)
        self.assertTrue(excel.data.startswith(b"PK"))

        pdf = self.client.get("/api/reports/export/pdf", headers=self.auth(admin))
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.data.startswith(b"%PDF"))

    def test_sale_discounts_stock_once_for_repeated_cart_lines(self):
        seller = self.login("vendedor", "vendedor123")
        headers = self.auth(seller)
        product = self.client.get("/api/products", headers=headers).get_json()["products"][0]

        opened = self.client.post("/api/cash-session/open", headers=headers, json={"opening_amount": 25})
        self.assertEqual(opened.status_code, 201, opened.get_data(as_text=True))

        sale = self.client.post(
            "/api/sales",
            headers=headers,
            json={
                "discount": 0.25,
                "items": [
                    {"product_id": product["id"], "quantity": 1},
                    {"product_id": product["id"], "quantity": 2},
                ],
            },
        )
        self.assertEqual(sale.status_code, 201, sale.get_data(as_text=True))
        products = self.client.get("/api/products", headers=headers).get_json()["products"]
        refreshed = next(item for item in products if item["id"] == product["id"])
        self.assertEqual(refreshed["stock"], product["stock"] - 3)

        excessive = self.client.post(
            "/api/sales",
            headers=headers,
            json={"items": [{"product_id": product["id"], "quantity": refreshed["stock"] + 1}]},
        )
        self.assertEqual(excessive.status_code, 400)
        self.assertIn("Stock insuficiente", excessive.get_json()["message"])

    def test_negative_discount_is_rejected(self):
        seller = self.login("vendedor", "vendedor123")
        headers = self.auth(seller)
        product = self.client.get("/api/products", headers=headers).get_json()["products"][0]
        self.client.post("/api/cash-session/open", headers=headers, json={"opening_amount": 25})
        response = self.client.post(
            "/api/sales",
            headers=headers,
            json={"discount": -5, "items": [{"product_id": product["id"], "quantity": 1}]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Descuento no puede ser negativo", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
