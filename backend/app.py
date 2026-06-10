import io
import os
import sqlite3
import uuid
import zipfile
from datetime import datetime, timedelta
from html import escape
from urllib.parse import quote
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "beer_house.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
CORS(app)

sessions = {}

INITIAL_PRODUCTS = [
    ("Corona", "Lager mexicana refrescante", 2.50, 1.45, 72, 12),
    ("Modelo", "Cerveza mexicana premium", 2.75, 1.60, 60, 12),
    ("Club Clásica", "Cerveza ecuatoriana clásica", 2.00, 1.10, 96, 18),
    ("Club Negra", "Cerveza oscura maltosa", 2.25, 1.25, 48, 10),
    ("Pilsener", "Cerveza rubia tradicional", 1.75, 0.95, 120, 24),
    ("Pilsener Light", "Cerveza ligera", 1.75, 0.95, 84, 18),
    ("Heineken", "Lager internacional", 3.00, 1.85, 50, 10),
    ("Amstel", "Lager europea balanceada", 2.80, 1.70, 44, 10),
    ("Stella Artois", "Lager belga premium", 3.25, 2.00, 36, 8),
    ("Michelada House", "Preparación especial de la casa", 4.50, 2.20, 40, 10),
    ("Margarita Palenque", "Cóctel cítrico premium", 5.75, 2.80, 32, 8),
    ("Snack Mix", "Botana salada para mesa", 3.25, 1.40, 28, 8),
]

DEFAULT_SETTINGS = {
    "business_name": "Beer House Palenque",
    "tax_id": "RUC-DEMO-0001",
    "address": "Centro de Palenque",
    "phone": "+593 99 000 0000",
    "currency": "USD",
    "daily_cash_opening": "150.00",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row is not None else None


def money(value):
    return round(float(value or 0), 2)


def beer_house_logo():
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'>"
        "<rect width='256' height='256' rx='58' fill='#0b0b0f'/>"
        "<circle cx='128' cy='122' r='82' fill='#d4af37'/>"
        "<circle cx='128' cy='122' r='62' fill='#111111'/>"
        "<path d='M95 82h50a34 34 0 0 1 0 68H95z' fill='#f7c948'/>"
        "<path d='M145 98h22a18 18 0 0 1 0 36h-22' fill='none' stroke='#f7c948' stroke-width='14'/>"
        "<rect x='90' y='70' width='58' height='96' rx='12' fill='#f7c948'/>"
        "<path d='M90 90h58' stroke='#fff3b0' stroke-width='10'/>"
        "<text x='128' y='207' text-anchor='middle' font-family='Arial' font-size='24' font-weight='900' fill='#f7c948'>BHP</text>"
        "</svg>"
    )
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def product_image(name):
    tone = {
        "Corona": "#f8d46b",
        "Modelo": "#d9a441",
        "Club Clásica": "#f3c03f",
        "Club Negra": "#3b2414",
        "Pilsener": "#f6c54c",
        "Pilsener Light": "#f7e9a3",
        "Heineken": "#07883d",
        "Amstel": "#d71920",
        "Stella Artois": "#c9a227",
    }.get(name, "#d4af37")
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 360 240'>"
        "<rect width='360' height='240' rx='28' fill='#111111'/>"
        f"<rect x='115' y='30' width='130' height='180' rx='26' fill='{tone}'/>"
        "<rect x='135' y='70' width='90' height='82' rx='14' fill='#fff7d6'/>"
        f"<text x='180' y='112' font-size='22' font-family='Arial' font-weight='700' text-anchor='middle' fill='#111111'>{name}</text>"
        "<text x='180' y='222' font-size='20' font-family='Arial' text-anchor='middle' fill='#d4af37'>Beer House Palenque</text>"
        "</svg>"
    )
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def init_db():
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'seller')),
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                price REAL NOT NULL,
                cost_price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER NOT NULL DEFAULT 5,
                image_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                total REAL NOT NULL,
                profit REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                unit_cost REAL NOT NULL,
                subtotal REAL NOT NULL,
                profit REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS business_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        user_count = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if user_count == 0:
            now = datetime.utcnow().isoformat()
            conn.executemany(
                "INSERT INTO users (name, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Administrador Beer House", "admin", generate_password_hash("admin123"), "admin", now),
                    ("Vendedor Demo", "vendedor", generate_password_hash("vendedor123"), "seller", now),
                ],
            )
        product_count = conn.execute("SELECT COUNT(*) AS total FROM products").fetchone()["total"]
        if product_count == 0:
            now = datetime.utcnow().isoformat()
            conn.executemany(
                """
                INSERT INTO products (name, description, price, cost_price, stock, min_stock, image_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(*product, product_image(product[0]), now, now) for product in INITIAL_PRODUCTS],
            )
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO business_settings (key, value) VALUES (?, ?)", (key, value))
        conn.execute("INSERT OR IGNORE INTO business_settings (key, value) VALUES (?, ?)", ("logo_url", beer_house_logo()))
        seed_demo_data(conn)


def seed_demo_data(conn):
    sale_count = conn.execute("SELECT COUNT(*) AS total FROM sales").fetchone()["total"]
    if sale_count:
        return
    now = datetime.utcnow()
    sellers = conn.execute("SELECT id FROM users WHERE role IN ('seller', 'admin') ORDER BY id").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    if not sellers or not products:
        return
    for index in range(180):
        created_at = (now - timedelta(days=index % 365, hours=(index * 3) % 12, minutes=(index * 11) % 50)).isoformat()
        seller_id = sellers[index % len(sellers)]["id"]
        selected = [products[index % len(products)], products[(index + 3) % len(products)]]
        total = profit = 0.0
        lines = []
        for offset, product in enumerate(selected):
            quantity = 1 + ((index + offset) % 4)
            subtotal = product["price"] * quantity
            item_profit = (product["price"] - product["cost_price"]) * quantity
            total += subtotal
            profit += item_profit
            lines.append((product, quantity, subtotal, item_profit))
        cursor = conn.execute("INSERT INTO sales (seller_id, total, profit, created_at) VALUES (?, ?, ?, ?)", (seller_id, total, profit, created_at))
        for product, quantity, subtotal, item_profit in lines:
            conn.execute(
                """
                INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, unit_cost, subtotal, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cursor.lastrowid, product["id"], product["name"], quantity, product["price"], product["cost_price"], subtotal, item_profit),
            )
    demo_expenses = [
        ("Hielo y vasos", "Operación", 18.50, now - timedelta(hours=4)),
        ("Publicidad redes", "Marketing", 42.00, now - timedelta(days=2)),
        ("Limpieza", "Operación", 25.00, now - timedelta(days=7)),
        ("Mantenimiento sonido", "Equipos", 70.00, now - timedelta(days=18)),
    ]
    admin_id = sellers[0]["id"]
    conn.executemany(
        "INSERT INTO expenses (concept, category, amount, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
        [(concept, category, amount, date.isoformat(), admin_id) for concept, category, amount, date in demo_expenses],
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "", 1).strip() or request.args.get("token", "").strip()
    user_id = sessions.get(token)
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute("SELECT id, name, username, role, active, created_at FROM users WHERE id = ? AND active = 1", (user_id,)).fetchone()


def require_auth(roles=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify({"message": "Sesión no válida o expirada"}), 401
            if roles and user["role"] not in roles:
                return jsonify({"message": "No tienes permisos para esta acción"}), 403
            return fn(user, *args, **kwargs)
        return wrapper
    return decorator


@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Usuario o contraseña incorrectos"}), 401
    token = uuid.uuid4().hex
    sessions[token] = user["id"]
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "username": user["username"], "role": user["role"]}})


@app.get("/api/me")
@require_auth()
def me(user):
    return jsonify({"user": row_to_dict(user)})


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.get("/api/products")
@require_auth()
def list_products(user):
    query = request.args.get("q", "").strip()
    sql = "SELECT * FROM products"
    params = []
    if query:
        sql += " WHERE name LIKE ? OR description LIKE ?"
        params = [f"%{query}%", f"%{query}%"]
    sql += " ORDER BY name"
    with get_db() as conn:
        products = [row_to_dict(row) for row in conn.execute(sql, params).fetchall()]
    return jsonify({"products": products})


@app.post("/api/products")
@require_auth(["admin"])
def create_product(user):
    data = request.get_json(force=True)
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO products (name, description, price, cost_price, stock, min_stock, image_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"].strip(), data.get("description", ""), float(data["price"]),
                float(data.get("cost_price", 0)), int(data.get("stock", 0)), int(data.get("min_stock", 5)),
                data.get("image_url") or product_image(data["name"].strip()), now, now,
            ),
        )
        product = conn.execute("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"product": row_to_dict(product)}), 201


@app.put("/api/products/<int:product_id>")
@require_auth(["admin"])
def update_product(user, product_id):
    data = request.get_json(force=True)
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, description = ?, price = ?, cost_price = ?, stock = ?, min_stock = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data["name"].strip(), data.get("description", ""), float(data["price"]),
                float(data.get("cost_price", 0)), int(data.get("stock", 0)), int(data.get("min_stock", 5)), now, product_id,
            ),
        )
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        return jsonify({"message": "Producto no encontrado"}), 404
    return jsonify({"product": row_to_dict(product)})


@app.delete("/api/products/<int:product_id>")
@require_auth(["admin"])
def delete_product(user, product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    return jsonify({"message": "Producto eliminado"})


@app.post("/api/products/<int:product_id>/image")
@require_auth(["admin"])
def upload_product_image(user, product_id):
    if "image" not in request.files:
        return jsonify({"message": "No se recibió imagen"}), 400
    image = request.files["image"]
    if image.filename == "" or not allowed_file(image.filename):
        return jsonify({"message": "Formato no permitido. Usa png, jpg, jpeg o webp"}), 400
    filename = f"product-{product_id}-{uuid.uuid4().hex[:8]}-{secure_filename(image.filename)}"
    image.save(UPLOAD_FOLDER / filename)
    image_url = f"/uploads/{filename}"
    with get_db() as conn:
        conn.execute("UPDATE products SET image_url = ?, updated_at = ? WHERE id = ?", (image_url, datetime.utcnow().isoformat(), product_id))
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return jsonify({"product": row_to_dict(product)})


@app.get("/api/users")
@require_auth(["admin"])
def list_users(user):
    with get_db() as conn:
        users = [row_to_dict(row) for row in conn.execute("SELECT id, name, username, role, active, created_at FROM users ORDER BY created_at DESC").fetchall()]
    return jsonify({"users": users})


@app.post("/api/users")
@require_auth(["admin"])
def create_user(user):
    data = request.get_json(force=True)
    role = data.get("role", "seller")
    if role not in {"admin", "seller"}:
        return jsonify({"message": "Rol inválido"}), 400
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (data["name"].strip(), data["username"].strip(), generate_password_hash(data["password"]), role, datetime.utcnow().isoformat()),
        )
        created = conn.execute("SELECT id, name, username, role, active, created_at FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"user": row_to_dict(created)}), 201


@app.post("/api/sales")
@require_auth(["admin", "seller"])
def create_sale(user):
    data = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify({"message": "Agrega productos al carrito"}), 400
    with get_db() as conn:
        try:
            conn.execute("BEGIN")
            sale_items = []
            total = 0.0
            profit = 0.0
            for item in items:
                product = conn.execute("SELECT * FROM products WHERE id = ?", (int(item["product_id"]),)).fetchone()
                quantity = int(item["quantity"])
                if product is None or quantity <= 0:
                    raise ValueError("Producto o cantidad inválida")
                if product["stock"] < quantity:
                    raise ValueError(f"Stock insuficiente para {product['name']}")
                subtotal = product["price"] * quantity
                item_profit = (product["price"] - product["cost_price"]) * quantity
                total += subtotal
                profit += item_profit
                sale_items.append((product, quantity, subtotal, item_profit))
            sale_cursor = conn.execute(
                "INSERT INTO sales (seller_id, total, profit, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], total, profit, datetime.utcnow().isoformat()),
            )
            sale_id = sale_cursor.lastrowid
            for product, quantity, subtotal, item_profit in sale_items:
                conn.execute("UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?", (quantity, datetime.utcnow().isoformat(), product["id"]))
                conn.execute(
                    """
                    INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, unit_cost, subtotal, profit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sale_id, product["id"], product["name"], quantity, product["price"], product["cost_price"], subtotal, item_profit),
                )
            conn.commit()
        except ValueError as exc:
            conn.rollback()
            return jsonify({"message": str(exc)}), 400
    return jsonify({"sale_id": sale_id, "total": round(total, 2), "seller": user["name"]}), 201


@app.get("/api/sales")
@require_auth(["admin"])
def list_sales(user):
    with get_db() as conn:
        sales = [row_to_dict(row) for row in conn.execute(
            """
            SELECT s.id, s.total, s.profit, s.created_at, u.name AS seller_name, u.username AS seller_username
            FROM sales s JOIN users u ON u.id = s.seller_id
            ORDER BY s.created_at DESC
            LIMIT 200
            """
        ).fetchall()]
        for sale in sales:
            sale["items"] = [row_to_dict(row) for row in conn.execute("SELECT product_name, quantity, unit_price, subtotal FROM sale_items WHERE sale_id = ?", (sale["id"],)).fetchall()]
    return jsonify({"sales": sales})


def period_start(period):
    now = datetime.utcnow()
    if period == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "weekly":
        return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "monthly":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "annual":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return datetime.min


@app.get("/api/reports/summary")
@require_auth(["admin"])
def reports_summary(user):
    with get_db() as conn:
        totals = {}
        for period in ["daily", "weekly", "monthly", "annual"]:
            start = period_start(period).isoformat()
            sales_row = conn.execute("SELECT COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit, COUNT(*) AS orders FROM sales WHERE created_at >= ?", (start,)).fetchone()
            expenses_row = conn.execute("SELECT COALESCE(SUM(amount), 0) AS expenses FROM expenses WHERE created_at >= ?", (start,)).fetchone()
            totals[period] = row_to_dict(sales_row)
            totals[period]["expenses"] = money(expenses_row["expenses"])
            totals[period]["net_profit"] = money(totals[period]["profit"] - totals[period]["expenses"])
        daily_start = period_start("daily").isoformat()
        daily_sales = conn.execute("SELECT COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit, COUNT(*) AS orders FROM sales WHERE created_at >= ?", (daily_start,)).fetchone()
        daily_expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) AS expenses FROM expenses WHERE created_at >= ?", (daily_start,)).fetchone()["expenses"]
        opening = float(dict(conn.execute("SELECT key, value FROM business_settings").fetchall()).get("daily_cash_opening", 0) or 0)
        cash_cut = {**row_to_dict(daily_sales), "opening_cash": opening, "expenses": money(daily_expenses), "expected_cash": money(opening + daily_sales["sales"] - daily_expenses), "net_profit": money(daily_sales["profit"] - daily_expenses)}
        low_stock = [row_to_dict(row) for row in conn.execute("SELECT * FROM products WHERE stock <= min_stock ORDER BY stock ASC, name ASC").fetchall()]
        top_products = [row_to_dict(row) for row in conn.execute(
            """
            SELECT product_name, SUM(quantity) AS quantity, SUM(subtotal) AS total, SUM(profit) AS profit
            FROM sale_items
            GROUP BY product_id, product_name
            ORDER BY quantity DESC
            LIMIT 8
            """
        ).fetchall()]
        by_seller = [row_to_dict(row) for row in conn.execute(
            """
            SELECT u.name AS seller_name, COUNT(s.id) AS sales_count, COALESCE(SUM(s.total), 0) AS total, COALESCE(SUM(s.profit), 0) AS profit
            FROM users u LEFT JOIN sales s ON s.seller_id = u.id
            WHERE u.role IN ('seller', 'admin')
            GROUP BY u.id, u.name
            ORDER BY total DESC
            LIMIT 8
            """
        ).fetchall()]
        sales_chart = [row_to_dict(row) for row in conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS label, COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit
            FROM sales
            WHERE created_at >= ?
            GROUP BY substr(created_at, 1, 10)
            ORDER BY label ASC
            """,
            ((datetime.utcnow() - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),),
        ).fetchall()]
        monthly_chart = [row_to_dict(row) for row in conn.execute(
            """
            SELECT substr(created_at, 1, 7) AS label, COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit
            FROM sales
            WHERE created_at >= ?
            GROUP BY substr(created_at, 1, 7)
            ORDER BY label ASC
            """,
            ((datetime.utcnow() - timedelta(days=365)).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),),
        ).fetchall()]
        expenses = [row_to_dict(row) for row in conn.execute("SELECT e.*, u.name AS created_by_name FROM expenses e LEFT JOIN users u ON u.id = e.created_by ORDER BY e.created_at DESC LIMIT 50").fetchall()]
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
        inventory = conn.execute("SELECT COUNT(*) AS products, COALESCE(SUM(stock), 0) AS units FROM products").fetchone()
    return jsonify({"totals": totals, "cash_cut": cash_cut, "low_stock": low_stock, "top_products": top_products, "by_seller": by_seller, "charts": {"daily": sales_chart, "monthly": monthly_chart}, "expenses": expenses, "settings": settings, "inventory": row_to_dict(inventory)})


@app.get("/api/expenses")
@require_auth(["admin"])
def list_expenses(user):
    with get_db() as conn:
        expenses = [row_to_dict(row) for row in conn.execute("SELECT e.*, u.name AS created_by_name FROM expenses e LEFT JOIN users u ON u.id = e.created_by ORDER BY e.created_at DESC LIMIT 200").fetchall()]
    return jsonify({"expenses": expenses})


@app.post("/api/expenses")
@require_auth(["admin"])
def create_expense(user):
    data = request.get_json(force=True)
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (concept, category, amount, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            (data["concept"].strip(), data.get("category", "Operación").strip(), float(data["amount"]), data.get("created_at") or datetime.utcnow().isoformat(), user["id"]),
        )
        expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"expense": row_to_dict(expense)}), 201


@app.delete("/api/expenses/<int:expense_id>")
@require_auth(["admin"])
def delete_expense(user, expense_id):
    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    return jsonify({"message": "Gasto eliminado"})


@app.get("/api/settings")
@require_auth(["admin"])
def get_settings(user):
    with get_db() as conn:
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
    return jsonify({"settings": settings})


@app.put("/api/settings")
@require_auth(["admin"])
def update_settings(user):
    data = request.get_json(force=True)
    allowed = set(DEFAULT_SETTINGS) | {"logo_url"}
    with get_db() as conn:
        for key, value in data.items():
            if key in allowed:
                conn.execute("INSERT OR REPLACE INTO business_settings (key, value) VALUES (?, ?)", (key, str(value)))
    with get_db() as conn:
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
    return jsonify({"settings": settings})


def report_rows(conn):
    return [row_to_dict(row) for row in conn.execute(
        """
        SELECT s.id, s.created_at, u.name AS seller, s.total, s.profit,
               COALESCE(GROUP_CONCAT(si.product_name || ' x' || si.quantity, ' | '), '') AS items
        FROM sales s
        JOIN users u ON u.id = s.seller_id
        LEFT JOIN sale_items si ON si.sale_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at DESC
        """
    ).fetchall()]


def make_xlsx(rows):
    headers = ["ID", "Fecha", "Vendedor", "Total", "Ganancia", "Productos"]
    data = [headers] + [[r["id"], r["created_at"], r["seller"], money(r["total"]), money(r["profit"]), r["items"]] for r in rows]
    def cell(value):
        if isinstance(value, (int, float)):
            return f"<c><v>{value}</v></c>"
        return f"<c t='inlineStr'><is><t>{escape(str(value))}</t></is></c>"
    sheet_rows = "".join(f"<row r='{i+1}'>" + "".join(cell(v) for v in row) + "</row>" for i, row in enumerate(data))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<?xml version='1.0'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/xl/workbook.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'/><Override PartName='/xl/worksheets/sheet1.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'/></Types>")
        zf.writestr("_rels/.rels", "<?xml version='1.0'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='xl/workbook.xml'/></Relationships>")
        zf.writestr("xl/workbook.xml", "<?xml version='1.0'?><workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'><sheets><sheet name='Ventas' sheetId='1' r:id='rId1'/></sheets></workbook>")
        zf.writestr("xl/_rels/workbook.xml.rels", "<?xml version='1.0'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' Target='worksheets/sheet1.xml'/></Relationships>")
        zf.writestr("xl/worksheets/sheet1.xml", f"<?xml version='1.0'?><worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><sheetData>{sheet_rows}</sheetData></worksheet>")
    output.seek(0)
    return output.read()


def make_pdf(rows):
    lines = ["Beer House Palenque - Reporte de ventas", ""]
    lines += [f"#{r['id']} {r['created_at'][:10]} {r['seller']} Total ${money(r['total']):.2f} Ganancia ${money(r['profit']):.2f}" for r in rows[:45]]
    text = "\n".join(lines).replace("(", "[").replace(")", "]")
    stream = "BT /F1 12 Tf 42 780 Td " + " T* ".join(f"({escape(line)})" for line in text.split("\n")) + " ET"
    pdf = f"%PDF-1.4\n1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n2 0 obj <</Type/Pages/Kids[3 0 R]/Count 1>> endobj\n3 0 obj <</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>> endobj\n4 0 obj <</Type/Font/Subtype/Type1/BaseFont/Helvetica>> endobj\n5 0 obj <</Length {len(stream)}>>stream\n{stream}\nendstream endobj\nxref\n0 6\n0000000000 65535 f \ntrailer <</Root 1 0 R/Size 6>>\nstartxref\n0\n%%EOF"
    return pdf.encode("latin-1", "ignore")


@app.get("/api/reports/export/<fmt>")
@require_auth(["admin"])
def export_report(user, fmt):
    with get_db() as conn:
        rows = report_rows(conn)
    if fmt == "excel":
        return Response(make_xlsx(rows), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=beer-house-reporte.xlsx"})
    if fmt == "pdf":
        return Response(make_pdf(rows), mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=beer-house-reporte.pdf"})
    return jsonify({"message": "Formato no soportado"}), 400


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


init_db()
