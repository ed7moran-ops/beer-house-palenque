import io
import os
import shutil
import sqlite3
import uuid
import zipfile
from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote
from functools import wraps

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def env_path(name, default):
    return Path(os.environ.get(name, default)).expanduser().resolve()


DB_PATH = env_path("DB_PATH", BASE_DIR / "beer_house.db")
UPLOAD_FOLDER = env_path("UPLOAD_FOLDER", BASE_DIR / "uploads")
BACKUP_FOLDER = env_path("BACKUP_FOLDER", BASE_DIR / "backups")
FRONTEND_DIST = env_path("FRONTEND_DIST", PROJECT_ROOT / "frontend" / "dist")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
PRODUCTION = os.environ.get("FLASK_ENV") == "production" or os.environ.get("APP_ENV") == "production"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")
app.config.update(
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    SECRET_KEY=os.environ.get("SECRET_KEY", uuid.uuid4().hex),
    MAX_CONTENT_LENGTH=int(os.environ.get("MAX_CONTENT_LENGTH", 8 * 1024 * 1024)),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=PRODUCTION,
)

cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "*").split(",") if origin.strip()]
CORS(app, resources={r"/api/*": {"origins": cors_origins}, r"/uploads/*": {"origins": cors_origins}})
sessions = {}

INITIAL_PRODUCTS = [
    ("Corona", "7501000123456", "Lager mexicana refrescante", 2.50, 1.45, 72, 12),
    ("Modelo", "7501000123457", "Cerveza mexicana premium", 2.75, 1.60, 60, 12),
    ("Club Clásica", "7861000123458", "Cerveza ecuatoriana clásica", 2.00, 1.10, 96, 18),
    ("Club Negra", "7861000123459", "Cerveza oscura maltosa", 2.25, 1.25, 48, 10),
    ("Pilsener", "7861000123460", "Cerveza rubia tradicional", 1.75, 0.95, 120, 24),
    ("Pilsener Light", "7861000123461", "Cerveza ligera", 1.75, 0.95, 84, 18),
    ("Heineken", "8712000123462", "Lager internacional", 3.00, 1.85, 50, 10),
    ("Amstel", "8712000123463", "Lager europea balanceada", 2.80, 1.70, 44, 10),
    ("Stella Artois", "5410000123464", "Lager belga premium", 3.25, 2.00, 36, 8),
    ("Michelada House", "BHP-MICHELADA", "Preparación especial de la casa", 4.50, 2.20, 40, 10),
    ("Margarita Palenque", "BHP-MARGARITA", "Cóctel cítrico premium", 5.75, 2.80, 32, 8),
    ("Snack Mix", "BHP-SNACK", "Botana salada para mesa", 3.25, 1.40, 28, 8),
]

DEFAULT_SETTINGS = {
    "business_name": "Beer House Palenque",
    "tax_id": "RUC-DEMO-0001",
    "address": "Centro de Palenque",
    "phone": "+593 99 000 0000",
    "currency": "USD",
    "daily_cash_opening": "150.00",
    "auto_backup_enabled": "1",
}


def now_iso():
    return datetime.now(UTC).isoformat()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row is not None else None


def money(value):
    return round(float(value or 0), 2)


def as_positive_int(value, field_name, allow_zero=False):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} debe ser un número entero")
    if allow_zero and number < 0:
        raise ValueError(f"{field_name} no puede ser negativo")
    if not allow_zero and number <= 0:
        raise ValueError(f"{field_name} debe ser mayor a cero")
    return number


def as_non_negative_money(value, field_name):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} debe ser un número válido")
    if number < 0:
        raise ValueError(f"{field_name} no puede ser negativo")
    return number


def add_column(conn, table, column, definition):
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def beer_house_logo():
    svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'><rect width='256' height='256' rx='58' fill='#0b0b0f'/><circle cx='128' cy='122' r='82' fill='#d4af37'/><circle cx='128' cy='122' r='62' fill='#111111'/><rect x='90' y='70' width='58' height='96' rx='12' fill='#f7c948'/><path d='M145 98h22a18 18 0 0 1 0 36h-22' fill='none' stroke='#f7c948' stroke-width='14'/><path d='M90 90h58' stroke='#fff3b0' stroke-width='10'/><text x='128' y='207' text-anchor='middle' font-family='Arial' font-size='24' font-weight='900' fill='#f7c948'>BHP</text></svg>"
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def product_image(name):
    tone = {"Corona": "#f8d46b", "Modelo": "#d9a441", "Club Clásica": "#f3c03f", "Club Negra": "#3b2414", "Pilsener": "#f6c54c", "Pilsener Light": "#f7e9a3", "Heineken": "#07883d", "Amstel": "#d71920", "Stella Artois": "#c9a227"}.get(name, "#d4af37")
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 360 240'><rect width='360' height='240' rx='28' fill='#111111'/><rect x='115' y='30' width='130' height='180' rx='26' fill='{tone}'/><rect x='135' y='70' width='90' height='82' rx='14' fill='#fff7d6'/><text x='180' y='112' font-size='22' font-family='Arial' font-weight='700' text-anchor='middle' fill='#111111'>{escape(name)}</text><text x='180' y='222' font-size='20' font-family='Arial' text-anchor='middle' fill='#d4af37'>Beer House Palenque</text></svg>"
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def log_audit(conn, user, action, entity, entity_id=None, details=None):
    user_id = user["id"] if user is not None else None
    role = user["role"] if user is not None else "system"
    conn.execute(
        "INSERT INTO audit_logs (user_id, user_role, action, entity, entity_id, details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, role, action, entity, str(entity_id or ""), details or "", now_iso()),
    )


def init_db():
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    BACKUP_FOLDER.mkdir(exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','seller')), active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS branches (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, address TEXT, phone TEXT, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT, price REAL NOT NULL, cost_price REAL NOT NULL, stock INTEGER NOT NULL DEFAULT 0, min_stock INTEGER NOT NULL DEFAULT 5, image_url TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER NOT NULL, total REAL NOT NULL, profit REAL NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY (seller_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS sale_items (id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER NOT NULL, product_id INTEGER, product_name TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL, unit_cost REAL NOT NULL, subtotal REAL NOT NULL, profit REAL NOT NULL, FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL);
            CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, concept TEXT NOT NULL, category TEXT NOT NULL, amount REAL NOT NULL, created_at TEXT NOT NULL, created_by INTEGER, FOREIGN KEY (created_by) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS business_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS cash_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, branch_id INTEGER NOT NULL, user_id INTEGER NOT NULL, opening_amount REAL NOT NULL, closing_amount REAL, expected_amount REAL, difference REAL, status TEXT NOT NULL CHECK(status IN ('open','closed')), opened_at TEXT NOT NULL, closed_at TEXT, notes TEXT, FOREIGN KEY(branch_id) REFERENCES branches(id), FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS inventory_movements (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, branch_id INTEGER, user_id INTEGER, movement_type TEXT NOT NULL, quantity INTEGER NOT NULL, before_stock INTEGER NOT NULL, after_stock INTEGER NOT NULL, reference TEXT, notes TEXT, created_at TEXT NOT NULL, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL);
            CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, user_id INTEGER, old_price REAL NOT NULL, new_price REAL NOT NULL, reason TEXT, created_at TEXT NOT NULL, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL);
            CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT, email TEXT, points INTEGER NOT NULL DEFAULT 0, total_spent REAL NOT NULL DEFAULT 0, visits INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS promotions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL CHECK(type IN ('percent','fixed')), value REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1, starts_at TEXT, ends_at TEXT, min_total REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, size_bytes INTEGER NOT NULL, kind TEXT NOT NULL, created_by INTEGER, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, user_role TEXT, action TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT, details TEXT, created_at TEXT NOT NULL);
        """)
        for table, cols in {
            "products": [("barcode", "TEXT"), ("branch_id", "INTEGER DEFAULT 1")],
            "sales": [("branch_id", "INTEGER DEFAULT 1"), ("cash_session_id", "INTEGER"), ("customer_id", "INTEGER"), ("subtotal", "REAL DEFAULT 0"), ("discount", "REAL DEFAULT 0"), ("payment_method", "TEXT DEFAULT 'cash'"), ("promotion_id", "INTEGER")],
            "sale_items": [("barcode", "TEXT"), ("discount", "REAL DEFAULT 0")],
            "expenses": [("branch_id", "INTEGER DEFAULT 1")],
            "users": [("branch_id", "INTEGER DEFAULT 1")],
        }.items():
            for column, definition in cols:
                add_column(conn, table, column, definition)
        conn.execute("INSERT OR IGNORE INTO branches (id, name, address, phone, active, created_at) VALUES (1, 'Matriz Palenque', 'Centro de Palenque', '+593 99 000 0000', 1, ?)", (now_iso(),))
        if conn.execute("SELECT COUNT(*) total FROM users").fetchone()["total"] == 0:
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            seller_password = os.environ.get("SELLER_PASSWORD", "vendedor123")
            conn.executemany("INSERT INTO users (name, username, password_hash, role, created_at, branch_id) VALUES (?, ?, ?, ?, ?, 1)", [("Administrador Beer House", "admin", generate_password_hash(admin_password), "admin", now_iso()), ("Vendedor Demo", "vendedor", generate_password_hash(seller_password), "seller", now_iso())])
        if conn.execute("SELECT COUNT(*) total FROM products").fetchone()["total"] == 0:
            rows = [(*p[:2], p[2], p[3], p[4], p[5], p[6], product_image(p[0]), now_iso(), now_iso(), 1) for p in INITIAL_PRODUCTS]
            conn.executemany("INSERT INTO products (name, barcode, description, price, cost_price, stock, min_stock, image_url, created_at, updated_at, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        else:
            for name, barcode, *_ in INITIAL_PRODUCTS:
                conn.execute("UPDATE products SET barcode = COALESCE(barcode, ?) WHERE name = ?", (barcode, name))
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO business_settings (key, value) VALUES (?, ?)", (key, value))
        conn.execute("INSERT OR IGNORE INTO business_settings (key, value) VALUES (?, ?)", ("logo_url", beer_house_logo()))
        if conn.execute("SELECT COUNT(*) total FROM promotions").fetchone()["total"] == 0:
            conn.execute("INSERT INTO promotions (name, type, value, active, min_total, created_at) VALUES ('Happy Hour 10%', 'percent', 10, 1, 20, ?)", (now_iso(),))
        if os.environ.get("SEED_DEMO_DATA", "1") == "1":
            seed_demo_data(conn)


def seed_demo_data(conn):
    if conn.execute("SELECT COUNT(*) AS total FROM sales").fetchone()["total"]:
        return
    sellers = conn.execute("SELECT id FROM users WHERE role IN ('seller','admin') ORDER BY id").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    if not sellers or not products:
        return
    base = datetime.now(UTC)
    for index in range(90):
        created_at = (base - timedelta(days=index % 120, hours=(index * 3) % 12)).isoformat()
        seller_id = sellers[index % len(sellers)]["id"]
        selected = [products[index % len(products)], products[(index + 3) % len(products)]]
        subtotal = profit = 0.0
        cursor = conn.execute("INSERT INTO sales (seller_id, branch_id, total, subtotal, discount, profit, created_at) VALUES (?, 1, 0, 0, 0, 0, ?)", (seller_id, created_at))
        for offset, product in enumerate(selected):
            quantity = 1 + ((index + offset) % 3)
            line_subtotal = product["price"] * quantity
            line_profit = (product["price"] - product["cost_price"]) * quantity
            subtotal += line_subtotal
            profit += line_profit
            conn.execute("INSERT INTO sale_items (sale_id, product_id, product_name, barcode, quantity, unit_price, unit_cost, subtotal, profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (cursor.lastrowid, product["id"], product["name"], product["barcode"], quantity, product["price"], product["cost_price"], line_subtotal, line_profit))
        conn.execute("UPDATE sales SET total = ?, subtotal = ?, profit = ? WHERE id = ?", (subtotal, subtotal, profit, cursor.lastrowid))
    admin_id = sellers[0]["id"]
    conn.executemany("INSERT INTO expenses (concept, category, amount, created_at, created_by, branch_id) VALUES (?, ?, ?, ?, ?, 1)", [("Hielo y vasos", "Operación", 18.50, (base - timedelta(hours=4)).isoformat(), admin_id), ("Publicidad redes", "Marketing", 42.00, (base - timedelta(days=2)).isoformat(), admin_id)])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1).strip() or request.args.get("token", "").strip()
    user_id = sessions.get(token)
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute("SELECT id, name, username, role, active, created_at, branch_id FROM users WHERE id = ? AND active = 1", (user_id,)).fetchone()


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


def active_cash_session(conn, user_id, branch_id):
    return conn.execute("SELECT * FROM cash_sessions WHERE user_id = ? AND branch_id = ? AND status = 'open' ORDER BY opened_at DESC LIMIT 1", (user_id, branch_id)).fetchone()


def ensure_auto_backup():
    with get_db() as conn:
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
        today = datetime.now(UTC).date().isoformat()
        exists = conn.execute("SELECT 1 FROM backups WHERE kind = 'auto' AND substr(created_at, 1, 10) = ? LIMIT 1", (today,)).fetchone()
    if settings.get("auto_backup_enabled", "1") == "1" and not exists and DB_PATH.exists():
        create_backup("auto", None)


def create_backup(kind="auto", user=None):
    BACKUP_FOLDER.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"beer-house-{kind}-{stamp}.db"
    target = BACKUP_FOLDER / filename
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, target)
    with get_db() as conn:
        conn.execute("INSERT INTO backups (filename, size_bytes, kind, created_by, created_at) VALUES (?, ?, ?, ?, ?)", (filename, target.stat().st_size if target.exists() else 0, kind, user["id"] if user is not None else None, now_iso()))
        log_audit(conn, user, "backup_created", "backup", filename, kind)
    return filename


@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ? AND active = 1", (data.get("username", "").strip(),)).fetchone()
        if not user or not check_password_hash(user["password_hash"], data.get("password", "")):
            return jsonify({"message": "Usuario o contraseña incorrectos"}), 401
        token = uuid.uuid4().hex
        sessions[token] = user["id"]
        log_audit(conn, user, "login", "session", user["id"], "Inicio de sesión")
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "username": user["username"], "role": user["role"], "branch_id": user["branch_id"]}})


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
    branch_id = request.args.get("branch_id", "").strip()
    sql = "SELECT p.*, b.name AS branch_name FROM products p LEFT JOIN branches b ON b.id = p.branch_id"
    clauses, params = [], []
    if query:
        clauses.append("(p.name LIKE ? OR p.description LIKE ? OR p.barcode LIKE ?)")
        params += [f"%{query}%", f"%{query}%", f"%{query}%"]
    if branch_id:
        clauses.append("p.branch_id = ?")
        params.append(int(branch_id))
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY p.name"
    with get_db() as conn:
        products = [row_to_dict(row) for row in conn.execute(sql, params).fetchall()]
    return jsonify({"products": products})


@app.post("/api/products")
@require_auth(["admin"])
def create_product(user):
    data = request.get_json(force=True)
    stock = int(data.get("stock", 0))
    branch_id = int(data.get("branch_id") or user["branch_id"] or 1)
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO products (name, barcode, description, price, cost_price, stock, min_stock, image_url, created_at, updated_at, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data["name"].strip(), data.get("barcode", "").strip(), data.get("description", ""), float(data["price"]), float(data.get("cost_price", 0)), stock, int(data.get("min_stock", 5)), data.get("image_url") or product_image(data["name"].strip()), now_iso(), now_iso(), branch_id))
        product = conn.execute("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)).fetchone()
        conn.execute("INSERT INTO inventory_movements (product_id, branch_id, user_id, movement_type, quantity, before_stock, after_stock, reference, notes, created_at) VALUES (?, ?, ?, 'initial', ?, 0, ?, 'product', 'Alta de producto', ?)", (cursor.lastrowid, branch_id, user["id"], stock, stock, now_iso()))
        log_audit(conn, user, "product_created", "product", cursor.lastrowid, data["name"].strip())
    return jsonify({"product": row_to_dict(product)}), 201


@app.put("/api/products/<int:product_id>")
@require_auth(["admin"])
def update_product(user, product_id):
    data = request.get_json(force=True)
    with get_db() as conn:
        old = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if old is None:
            return jsonify({"message": "Producto no encontrado"}), 404
        new_stock = int(data.get("stock", old["stock"]))
        new_price = float(data.get("price", old["price"]))
        conn.execute("UPDATE products SET name = ?, barcode = ?, description = ?, price = ?, cost_price = ?, stock = ?, min_stock = ?, branch_id = ?, updated_at = ? WHERE id = ?", (data["name"].strip(), data.get("barcode", old["barcode"] or "").strip(), data.get("description", ""), new_price, float(data.get("cost_price", 0)), new_stock, int(data.get("min_stock", 5)), int(data.get("branch_id") or old["branch_id"] or 1), now_iso(), product_id))
        if money(old["price"]) != money(new_price):
            conn.execute("INSERT INTO price_history (product_id, user_id, old_price, new_price, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)", (product_id, user["id"], old["price"], new_price, data.get("price_reason", "Actualización de precio"), now_iso()))
        if old["stock"] != new_stock:
            conn.execute("INSERT INTO inventory_movements (product_id, branch_id, user_id, movement_type, quantity, before_stock, after_stock, reference, notes, created_at) VALUES (?, ?, ?, 'adjustment', ?, ?, ?, 'manual', ?, ?)", (product_id, int(data.get("branch_id") or old["branch_id"] or 1), user["id"], new_stock - old["stock"], old["stock"], new_stock, data.get("stock_notes", "Ajuste manual"), now_iso()))
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        log_audit(conn, user, "product_updated", "product", product_id, data["name"].strip())
    return jsonify({"product": row_to_dict(product)})


@app.delete("/api/products/<int:product_id>")
@require_auth(["admin"])
def delete_product(user, product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        log_audit(conn, user, "product_deleted", "product", product_id, "Eliminación de producto")
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
    with get_db() as conn:
        conn.execute("UPDATE products SET image_url = ?, updated_at = ? WHERE id = ?", (f"/uploads/{filename}", now_iso(), product_id))
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        log_audit(conn, user, "product_image_updated", "product", product_id, filename)
    return jsonify({"product": row_to_dict(product)})


@app.get("/api/users")
@require_auth(["admin"])
def list_users(user):
    with get_db() as conn:
        users = [row_to_dict(row) for row in conn.execute("SELECT u.id, u.name, u.username, u.role, u.active, u.created_at, u.branch_id, b.name AS branch_name FROM users u LEFT JOIN branches b ON b.id = u.branch_id ORDER BY u.created_at DESC").fetchall()]
    return jsonify({"users": users})


@app.post("/api/users")
@require_auth(["admin"])
def create_user(user):
    data = request.get_json(force=True)
    role = data.get("role", "seller")
    if role not in {"admin", "seller"}:
        return jsonify({"message": "Rol inválido"}), 400
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO users (name, username, password_hash, role, created_at, branch_id) VALUES (?, ?, ?, ?, ?, ?)", (data["name"].strip(), data["username"].strip(), generate_password_hash(data["password"]), role, now_iso(), int(data.get("branch_id") or 1)))
        created = conn.execute("SELECT id, name, username, role, active, created_at, branch_id FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "user_created", "user", cursor.lastrowid, data["username"].strip())
    return jsonify({"user": row_to_dict(created)}), 201


@app.get("/api/branches")
@require_auth()
def list_branches(user):
    with get_db() as conn:
        branches = [row_to_dict(row) for row in conn.execute("SELECT * FROM branches ORDER BY active DESC, name").fetchall()]
    return jsonify({"branches": branches})


@app.post("/api/branches")
@require_auth(["admin"])
def create_branch(user):
    data = request.get_json(force=True)
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO branches (name, address, phone, active, created_at) VALUES (?, ?, ?, 1, ?)", (data["name"].strip(), data.get("address", ""), data.get("phone", ""), now_iso()))
        branch = conn.execute("SELECT * FROM branches WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "branch_created", "branch", cursor.lastrowid, data["name"].strip())
    return jsonify({"branch": row_to_dict(branch)}), 201


@app.get("/api/cash-session/current")
@require_auth(["admin", "seller"])
def get_cash_session(user):
    branch_id = int(request.args.get("branch_id") or user["branch_id"] or 1)
    with get_db() as conn:
        session = active_cash_session(conn, user["id"], branch_id)
    return jsonify({"session": row_to_dict(session)})


@app.post("/api/cash-session/open")
@require_auth(["admin", "seller"])
def open_cash_session(user):
    data = request.get_json(force=True)
    branch_id = int(data.get("branch_id") or user["branch_id"] or 1)
    with get_db() as conn:
        if active_cash_session(conn, user["id"], branch_id):
            return jsonify({"message": "Ya tienes una caja abierta en esta sucursal"}), 400
        cursor = conn.execute("INSERT INTO cash_sessions (branch_id, user_id, opening_amount, status, opened_at, notes) VALUES (?, ?, ?, 'open', ?, ?)", (branch_id, user["id"], float(data.get("opening_amount", 0)), now_iso(), data.get("notes", "")))
        session = conn.execute("SELECT * FROM cash_sessions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "cash_opened", "cash_session", cursor.lastrowid, f"Apertura ${session['opening_amount']}")
    return jsonify({"session": row_to_dict(session)}), 201


@app.post("/api/cash-session/<int:session_id>/close")
@require_auth(["admin", "seller"])
def close_cash_session(user, session_id):
    data = request.get_json(force=True)
    closing_amount = float(data.get("closing_amount", 0))
    with get_db() as conn:
        session = conn.execute("SELECT * FROM cash_sessions WHERE id = ? AND status = 'open'", (session_id,)).fetchone()
        if not session:
            return jsonify({"message": "Caja no encontrada o ya cerrada"}), 404
        if user["role"] != "admin" and session["user_id"] != user["id"]:
            return jsonify({"message": "Solo puedes cerrar tu propia caja"}), 403
        sales = conn.execute("SELECT COALESCE(SUM(total),0) total FROM sales WHERE cash_session_id = ?", (session_id,)).fetchone()["total"]
        expenses = conn.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE branch_id = ? AND created_at >= ?", (session["branch_id"], session["opened_at"])).fetchone()["total"]
        expected = money(session["opening_amount"] + sales - expenses)
        diff = money(closing_amount - expected)
        conn.execute("UPDATE cash_sessions SET closing_amount = ?, expected_amount = ?, difference = ?, status = 'closed', closed_at = ?, notes = ? WHERE id = ?", (closing_amount, expected, diff, now_iso(), data.get("notes", session["notes"] or ""), session_id))
        closed = conn.execute("SELECT * FROM cash_sessions WHERE id = ?", (session_id,)).fetchone()
        log_audit(conn, user, "cash_closed", "cash_session", session_id, f"Esperado ${expected} real ${closing_amount}")
    return jsonify({"session": row_to_dict(closed)})


@app.get("/api/cash-sessions")
@require_auth(["admin"])
def list_cash_sessions(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT c.*, u.name AS user_name, b.name AS branch_name FROM cash_sessions c JOIN users u ON u.id = c.user_id JOIN branches b ON b.id = c.branch_id ORDER BY c.opened_at DESC LIMIT 100").fetchall()]
    return jsonify({"sessions": rows})


@app.post("/api/sales")
@require_auth(["admin", "seller"])
def create_sale(user):
    data = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify({"message": "Agrega productos al carrito"}), 400
    branch_id = int(data.get("branch_id") or user["branch_id"] or 1)
    with get_db() as conn:
        try:
            conn.execute("BEGIN")
            cash = active_cash_session(conn, user["id"], branch_id)
            if not cash:
                raise ValueError("Abre caja antes de vender")

            requested = {}
            for item in items:
                quantity = as_positive_int(item.get("quantity", 1), "Cantidad")
                product_id = item.get("product_id")
                barcode = str(item.get("barcode", "")).strip()
                if product_id:
                    key = ("id", int(product_id))
                elif barcode:
                    key = ("barcode", barcode)
                else:
                    raise ValueError("Producto o cantidad inválida")
                requested[key] = requested.get(key, 0) + quantity

            sale_items, subtotal, profit = [], 0.0, 0.0
            for (lookup_type, lookup_value), quantity in requested.items():
                if lookup_type == "id":
                    product = conn.execute("SELECT * FROM products WHERE id = ? AND branch_id = ?", (lookup_value, branch_id)).fetchone()
                else:
                    product = conn.execute("SELECT * FROM products WHERE barcode = ? AND branch_id = ?", (lookup_value, branch_id)).fetchone()
                if product is None:
                    raise ValueError("Producto no encontrado en la sucursal seleccionada")
                if product["stock"] < quantity:
                    raise ValueError(f"Stock insuficiente para {product['name']}: disponible {product['stock']}, solicitado {quantity}")
                line_subtotal = product["price"] * quantity
                line_profit = (product["price"] - product["cost_price"]) * quantity
                subtotal += line_subtotal
                profit += line_profit
                sale_items.append((product, quantity, line_subtotal, line_profit))

            promotion_id = data.get("promotion_id")
            discount = as_non_negative_money(data.get("discount", 0), "Descuento")
            if promotion_id:
                promo = conn.execute("SELECT * FROM promotions WHERE id = ? AND active = 1", (int(promotion_id),)).fetchone()
                if promo and subtotal >= promo["min_total"]:
                    discount += subtotal * promo["value"] / 100 if promo["type"] == "percent" else promo["value"]
            discount = min(discount, subtotal)
            total = money(subtotal - discount)
            profit = money(profit - discount)
            sale_cursor = conn.execute("INSERT INTO sales (seller_id, branch_id, cash_session_id, customer_id, subtotal, discount, total, profit, payment_method, promotion_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user["id"], branch_id, cash["id"], data.get("customer_id"), subtotal, discount, total, profit, data.get("payment_method", "cash"), promotion_id, now_iso()))
            sale_id = sale_cursor.lastrowid
            for product, quantity, line_subtotal, line_profit in sale_items:
                before = product["stock"]
                after = before - quantity
                updated = conn.execute("UPDATE products SET stock = ?, updated_at = ? WHERE id = ? AND stock >= ?", (after, now_iso(), product["id"], quantity))
                if updated.rowcount != 1:
                    raise ValueError(f"Stock insuficiente para {product['name']}")
                conn.execute("INSERT INTO sale_items (sale_id, product_id, product_name, barcode, quantity, unit_price, unit_cost, subtotal, profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (sale_id, product["id"], product["name"], product["barcode"], quantity, product["price"], product["cost_price"], line_subtotal, line_profit))
                conn.execute("INSERT INTO inventory_movements (product_id, branch_id, user_id, movement_type, quantity, before_stock, after_stock, reference, notes, created_at) VALUES (?, ?, ?, 'sale', ?, ?, ?, ?, 'Venta POS', ?)", (product["id"], branch_id, user["id"], -quantity, before, after, f"sale:{sale_id}", now_iso()))
            if data.get("customer_id"):
                conn.execute("UPDATE customers SET points = points + ?, total_spent = total_spent + ?, visits = visits + 1, updated_at = ? WHERE id = ?", (int(total), total, now_iso(), int(data["customer_id"])))
            log_audit(conn, user, "sale_created", "sale", sale_id, f"Venta ${total}")
            conn.commit()
        except ValueError as exc:
            conn.rollback()
            return jsonify({"message": str(exc)}), 400
    return jsonify({"sale_id": sale_id, "total": total, "subtotal": money(subtotal), "discount": money(discount), "seller": user["name"], "ticket_url": f"/api/sales/{sale_id}/ticket"}), 201

@app.get("/api/sales")
@require_auth(["admin"])
def list_sales(user):
    with get_db() as conn:
        sales = [row_to_dict(row) for row in conn.execute("SELECT s.*, u.name AS seller_name, u.username AS seller_username, b.name AS branch_name, c.name AS customer_name FROM sales s JOIN users u ON u.id = s.seller_id LEFT JOIN branches b ON b.id = s.branch_id LEFT JOIN customers c ON c.id = s.customer_id ORDER BY s.created_at DESC LIMIT 200").fetchall()]
        for sale in sales:
            sale["items"] = [row_to_dict(row) for row in conn.execute("SELECT product_name, barcode, quantity, unit_price, subtotal FROM sale_items WHERE sale_id = ?", (sale["id"],)).fetchall()]
    return jsonify({"sales": sales})


@app.get("/api/sales/<int:sale_id>/ticket")
@require_auth(["admin", "seller"])
def sale_ticket(user, sale_id):
    fmt = request.args.get("format", "html")
    with get_db() as conn:
        sale = conn.execute("SELECT s.*, u.name AS seller_name, b.name AS branch_name, c.name AS customer_name FROM sales s JOIN users u ON u.id=s.seller_id LEFT JOIN branches b ON b.id=s.branch_id LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id = ?", (sale_id,)).fetchone()
        if sale is None:
            return jsonify({"message": "Venta no encontrada"}), 404
        items = [row_to_dict(row) for row in conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()]
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
    lines = [settings.get("business_name", "Beer House Palenque"), settings.get("tax_id", ""), settings.get("address", ""), f"Ticket #{sale_id}  {sale['created_at'][:19]}", f"Sucursal: {sale['branch_name'] or 'Matriz'}", f"Vendedor: {sale['seller_name']}"]
    if sale["customer_name"]:
        lines.append(f"Cliente: {sale['customer_name']}")
    lines.append("-" * 32)
    for item in items:
        lines.append(f"{item['quantity']} x {item['product_name'][:18]} ${money(item['subtotal']):.2f}")
    lines += ["-" * 32, f"Subtotal: ${money(sale['subtotal'] or sale['total']):.2f}", f"Descuento: ${money(sale['discount']):.2f}", f"TOTAL: ${money(sale['total']):.2f}", "Gracias por su compra"]
    text = "\n".join(lines)
    if fmt == "text":
        return Response(text, mimetype="text/plain")
    html = f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Ticket #{sale_id}</title><style>body{{font-family:monospace;margin:0;background:#eee}}.ticket{{width:300px;margin:16px auto;background:white;padding:18px}}pre{{white-space:pre-wrap}}button{{width:100%;padding:12px;background:#111;color:#f7c948;border:0;border-radius:8px;font-weight:900}}@media print{{button{{display:none}}body{{background:white}}.ticket{{margin:0;width:280px}}}}</style></head><body><div class='ticket'><pre>{escape(text)}</pre><button onclick='window.print()'>Imprimir ticket</button></div></body></html>"
    return Response(html, mimetype="text/html")


@app.get("/api/inventory-movements")
@require_auth(["admin"])
def inventory_movements(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT m.*, p.name AS product_name, b.name AS branch_name, u.name AS user_name FROM inventory_movements m LEFT JOIN products p ON p.id=m.product_id LEFT JOIN branches b ON b.id=m.branch_id LEFT JOIN users u ON u.id=m.user_id ORDER BY m.created_at DESC LIMIT 250").fetchall()]
    return jsonify({"movements": rows})


@app.get("/api/price-history")
@require_auth(["admin"])
def price_history(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT h.*, p.name AS product_name, u.name AS user_name FROM price_history h LEFT JOIN products p ON p.id=h.product_id LEFT JOIN users u ON u.id=h.user_id ORDER BY h.created_at DESC LIMIT 250").fetchall()]
    return jsonify({"history": rows})


@app.get("/api/customers")
@require_auth(["admin", "seller"])
def list_customers(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT * FROM customers WHERE active = 1 ORDER BY visits DESC, name LIMIT 300").fetchall()]
    return jsonify({"customers": rows})


@app.post("/api/customers")
@require_auth(["admin", "seller"])
def create_customer(user):
    data = request.get_json(force=True)
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO customers (name, phone, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (data["name"].strip(), data.get("phone", ""), data.get("email", ""), now_iso(), now_iso()))
        customer = conn.execute("SELECT * FROM customers WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "customer_created", "customer", cursor.lastrowid, data["name"].strip())
    return jsonify({"customer": row_to_dict(customer)}), 201


@app.get("/api/promotions")
@require_auth(["admin", "seller"])
def list_promotions(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT * FROM promotions ORDER BY active DESC, created_at DESC").fetchall()]
    return jsonify({"promotions": rows})


@app.post("/api/promotions")
@require_auth(["admin"])
def create_promotion(user):
    data = request.get_json(force=True)
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO promotions (name, type, value, active, starts_at, ends_at, min_total, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data["name"].strip(), data.get("type", "percent"), float(data.get("value", 0)), int(data.get("active", 1)), data.get("starts_at"), data.get("ends_at"), float(data.get("min_total", 0)), now_iso()))
        promo = conn.execute("SELECT * FROM promotions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "promotion_created", "promotion", cursor.lastrowid, data["name"].strip())
    return jsonify({"promotion": row_to_dict(promo)}), 201


@app.get("/api/audit-logs")
@require_auth(["admin"])
def audit_logs(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT a.*, u.name AS user_name FROM audit_logs a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.created_at DESC LIMIT 300").fetchall()]
    return jsonify({"logs": rows})


@app.get("/api/backups")
@require_auth(["admin"])
def list_backups(user):
    with get_db() as conn:
        rows = [row_to_dict(row) for row in conn.execute("SELECT b.*, u.name AS created_by_name FROM backups b LEFT JOIN users u ON u.id=b.created_by ORDER BY b.created_at DESC LIMIT 100").fetchall()]
    return jsonify({"backups": rows})


@app.post("/api/backups")
@require_auth(["admin"])
def manual_backup(user):
    filename = create_backup("manual", user)
    return jsonify({"message": "Respaldo creado", "filename": filename}), 201


@app.get("/api/backups/<path:filename>")
@require_auth(["admin"])
def download_backup(user, filename):
    return send_from_directory(BACKUP_FOLDER, secure_filename(filename), as_attachment=True)


@app.post("/api/backups/restore")
@require_auth(["admin"])
def restore_backup(user):
    filename = request.form.get("filename", "")
    uploaded = request.files.get("backup")
    source = None
    if uploaded and uploaded.filename.endswith(".db"):
        source = BACKUP_FOLDER / f"upload-{uuid.uuid4().hex}.db"
        uploaded.save(source)
    elif filename:
        source = BACKUP_FOLDER / secure_filename(filename)
    if not source or not source.exists():
        return jsonify({"message": "Respaldo no encontrado"}), 404
    pre_restore = create_backup("pre-restore", user)
    shutil.copy2(source, DB_PATH)
    sessions.clear()
    init_db()
    return jsonify({"message": "Base recuperada; vuelve a iniciar sesión", "pre_restore_backup": pre_restore})


def period_start(period):
    now = datetime.now(UTC)
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
        top_products = [row_to_dict(row) for row in conn.execute("SELECT product_name, SUM(quantity) AS quantity, SUM(subtotal) AS total, SUM(profit) AS profit FROM sale_items GROUP BY product_id, product_name ORDER BY quantity DESC LIMIT 8").fetchall()]
        by_seller = [row_to_dict(row) for row in conn.execute("SELECT u.name AS seller_name, COUNT(s.id) AS sales_count, COALESCE(SUM(s.total), 0) AS total, COALESCE(SUM(s.profit), 0) AS profit FROM users u LEFT JOIN sales s ON s.seller_id = u.id WHERE u.role IN ('seller', 'admin') GROUP BY u.id, u.name ORDER BY total DESC LIMIT 8").fetchall()]
        sales_chart = [row_to_dict(row) for row in conn.execute("SELECT substr(created_at, 1, 10) AS label, COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit FROM sales WHERE created_at >= ? GROUP BY substr(created_at, 1, 10) ORDER BY label ASC", ((datetime.now(UTC) - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),)).fetchall()]
        monthly_chart = [row_to_dict(row) for row in conn.execute("SELECT substr(created_at, 1, 7) AS label, COALESCE(SUM(total), 0) AS sales, COALESCE(SUM(profit), 0) AS profit FROM sales WHERE created_at >= ? GROUP BY substr(created_at, 1, 7) ORDER BY label ASC", ((datetime.now(UTC) - timedelta(days=365)).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),)).fetchall()]
        expenses = [row_to_dict(row) for row in conn.execute("SELECT e.*, u.name AS created_by_name FROM expenses e LEFT JOIN users u ON u.id = e.created_by ORDER BY e.created_at DESC LIMIT 50").fetchall()]
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
        inventory = conn.execute("SELECT COUNT(*) AS products, COALESCE(SUM(stock), 0) AS units FROM products").fetchone()
        branch_sales = [row_to_dict(row) for row in conn.execute("SELECT b.name AS branch_name, COALESCE(SUM(s.total),0) AS total, COUNT(s.id) AS sales_count FROM branches b LEFT JOIN sales s ON s.branch_id=b.id GROUP BY b.id ORDER BY total DESC").fetchall()]
        cash_open = [row_to_dict(row) for row in conn.execute("SELECT c.*, u.name AS user_name, b.name AS branch_name FROM cash_sessions c JOIN users u ON u.id=c.user_id JOIN branches b ON b.id=c.branch_id WHERE c.status='open'").fetchall()]
    return jsonify({"totals": totals, "cash_cut": cash_cut, "low_stock": low_stock, "top_products": top_products, "by_seller": by_seller, "charts": {"daily": sales_chart, "monthly": monthly_chart}, "expenses": expenses, "settings": settings, "inventory": row_to_dict(inventory), "branch_sales": branch_sales, "open_cash_sessions": cash_open})


@app.get("/api/expenses")
@require_auth(["admin"])
def list_expenses(user):
    with get_db() as conn:
        expenses = [row_to_dict(row) for row in conn.execute("SELECT e.*, u.name AS created_by_name, b.name AS branch_name FROM expenses e LEFT JOIN users u ON u.id = e.created_by LEFT JOIN branches b ON b.id=e.branch_id ORDER BY e.created_at DESC LIMIT 200").fetchall()]
    return jsonify({"expenses": expenses})


@app.post("/api/expenses")
@require_auth(["admin"])
def create_expense(user):
    data = request.get_json(force=True)
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO expenses (concept, category, amount, created_at, created_by, branch_id) VALUES (?, ?, ?, ?, ?, ?)", (data["concept"].strip(), data.get("category", "Operación").strip(), float(data["amount"]), data.get("created_at") or now_iso(), user["id"], int(data.get("branch_id") or user["branch_id"] or 1)))
        expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)).fetchone()
        log_audit(conn, user, "expense_created", "expense", cursor.lastrowid, data["concept"].strip())
    return jsonify({"expense": row_to_dict(expense)}), 201


@app.delete("/api/expenses/<int:expense_id>")
@require_auth(["admin"])
def delete_expense(user, expense_id):
    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        log_audit(conn, user, "expense_deleted", "expense", expense_id, "Eliminación de gasto")
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
        log_audit(conn, user, "settings_updated", "settings", "business", ", ".join(data.keys()))
        settings = dict(conn.execute("SELECT key, value FROM business_settings").fetchall())
    return jsonify({"settings": settings})


def report_rows(conn):
    return [row_to_dict(row) for row in conn.execute("SELECT s.id, s.created_at, u.name AS seller, b.name AS branch, s.total, s.discount, s.profit, COALESCE(GROUP_CONCAT(si.product_name || ' x' || si.quantity, ' | '), '') AS items FROM sales s JOIN users u ON u.id = s.seller_id LEFT JOIN branches b ON b.id=s.branch_id LEFT JOIN sale_items si ON si.sale_id = s.id GROUP BY s.id ORDER BY s.created_at DESC").fetchall()]


def make_xlsx(rows):
    headers = ["ID", "Fecha", "Sucursal", "Vendedor", "Total", "Descuento", "Ganancia", "Productos"]
    data = [headers] + [[r["id"], r["created_at"], r["branch"], r["seller"], money(r["total"]), money(r["discount"]), money(r["profit"]), r["items"]] for r in rows]
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
    lines += [f"#{r['id']} {r['created_at'][:10]} {r['branch'] or ''} {r['seller']} Total ${money(r['total']):.2f} Desc ${money(r['discount']):.2f}" for r in rows[:45]]
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
    return jsonify({"status": "ok", "database": DB_PATH.exists(), "frontend": FRONTEND_DIST.exists()})


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if PRODUCTION:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.get("/")
def serve_frontend_index():
    if FRONTEND_DIST.exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "Frontend build not found. Run scripts/build_production.sh."}), 404


@app.get("/<path:path>")
def serve_frontend_asset(path):
    target = FRONTEND_DIST / path
    if FRONTEND_DIST.exists() and target.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    if FRONTEND_DIST.exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "Frontend build not found. Run scripts/build_production.sh."}), 404


init_db()
ensure_auto_backup()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
