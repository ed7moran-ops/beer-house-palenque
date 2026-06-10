import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
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
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row is not None else None


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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "", 1).strip()
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
    return datetime.min


@app.get("/api/reports/summary")
@require_auth(["admin"])
def reports_summary(user):
    with get_db() as conn:
        totals = {}
        for period in ["daily", "weekly", "monthly"]:
            start = period_start(period).isoformat()
            row = conn.execute("SELECT COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit, COUNT(*) AS orders FROM sales WHERE created_at >= ?", (start,)).fetchone()
            totals[period] = row_to_dict(row)
        low_stock = [row_to_dict(row) for row in conn.execute("SELECT * FROM products WHERE stock <= min_stock ORDER BY stock ASC, name ASC").fetchall()]
        top_products = [row_to_dict(row) for row in conn.execute(
            """
            SELECT product_name, SUM(quantity) AS quantity, SUM(subtotal) AS total
            FROM sale_items
            GROUP BY product_id, product_name
            ORDER BY quantity DESC
            LIMIT 5
            """
        ).fetchall()]
        by_seller = [row_to_dict(row) for row in conn.execute(
            """
            SELECT u.name AS seller_name, COUNT(s.id) AS sales_count, COALESCE(SUM(s.total), 0) AS total, COALESCE(SUM(s.profit), 0) AS profit
            FROM users u LEFT JOIN sales s ON s.seller_id = u.id
            WHERE u.role = 'seller'
            GROUP BY u.id, u.name
            ORDER BY total DESC
            """
        ).fetchall()]
        inventory = conn.execute("SELECT COUNT(*) AS products, COALESCE(SUM(stock), 0) AS units FROM products").fetchone()
    return jsonify({"totals": totals, "low_stock": low_stock, "top_products": top_products, "by_seller": by_seller, "inventory": row_to_dict(inventory)})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


init_db()
