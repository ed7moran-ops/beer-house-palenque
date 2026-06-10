# Documentación técnica — Beer House Palenque

## 1. Descripción general
Beer House Palenque es un sistema web para administrar inventario, registrar ventas y consultar reportes de una tienda de cervezas. La aplicación contempla dos roles principales:

- **Administrador:** gestiona productos, usuarios, reportes, ganancias e inventario.
- **Vendedor:** registra ventas desde un catálogo con carrito y consulta el total a cobrar.

El sistema descuenta stock automáticamente cuando se confirma una venta y conserva el historial de productos vendidos, cantidades, subtotales, vendedor y ganancias.

## 2. Arquitectura

### 2.1 Vista lógica
La solución está compuesta por tres capas:

1. **Frontend web:** SPA desarrollada con React y Vite. Presenta el login, dashboard administrativo, inventario, usuarios y panel de vendedor.
2. **API backend:** servicio Flask que expone endpoints REST para autenticación, productos, usuarios, ventas, reportes, salud y archivos subidos.
3. **Persistencia:** base SQLite local creada automáticamente al iniciar la aplicación.

### 2.2 Flujo principal
1. El usuario ingresa credenciales en la pantalla de login.
2. El backend valida usuario y contraseña contra SQLite.
3. Si las credenciales son correctas, se genera un token de sesión en memoria.
4. El frontend guarda el token y lo envía como `Authorization: Bearer <token>`.
5. Según el rol, el usuario accede al panel administrativo o al panel de vendedor.
6. Al registrar una venta, el backend valida stock, crea la venta, registra sus ítems y descuenta inventario dentro de una transacción.

### 2.3 Control de acceso
- `admin`: acceso a productos, usuarios, ventas, reportes y creación/edición/eliminación.
- `seller`: acceso a productos y creación de ventas.

## 3. Tecnologías utilizadas

### Backend
- **Python 3** como lenguaje de servidor.
- **Flask 3.0.3** para API HTTP.
- **Flask-CORS 4.0.1** para permitir comunicación desde el frontend.
- **Werkzeug 3.0.3** para hash de contraseñas y utilidades de carga de archivos.
- **SQLite** mediante `sqlite3` de la biblioteca estándar.

### Frontend
- **React** para la interfaz de usuario.
- **Vite** como herramienta de desarrollo y empaquetado.
- **Tailwind CSS** para estilos utilitarios.
- **lucide-react** para iconografía.

### Persistencia y archivos
- **SQLite:** archivo local `backend/beer_house.db` generado al iniciar.
- **Uploads:** imágenes de productos guardadas en `backend/uploads`.

## 4. Estructura de carpetas

```text
beer-house-palenque/
├── backend/
│   ├── app.py                 # API Flask, inicialización de BD, autenticación y endpoints
│   ├── requirements.txt       # Dependencias Python
│   └── uploads/               # Imágenes cargadas de productos
│       └── .gitkeep
├── docs/
│   ├── ANALISIS_MEJORAS.md
│   ├── BITACORA_DESARROLLO.md
│   ├── DOCUMENTACION_TECNICA.md
│   └── MANUAL_USUARIO.md
├── frontend/
│   ├── index.html             # HTML base de Vite
│   ├── package.json           # Scripts y dependencias frontend
│   ├── package-lock.json      # Versiones bloqueadas de npm
│   ├── postcss.config.js      # Configuración PostCSS
│   ├── tailwind.config.js     # Configuración Tailwind
│   └── src/
│       ├── index.css          # Tailwind y estilos globales
│       └── main.jsx           # Aplicación React y componentes principales
├── PRD.md                     # Documento de requisitos del producto
└── README.md                  # Guía rápida del proyecto
```

## 5. Funciones principales

### 5.1 Autenticación
- Endpoint: `POST /api/login`.
- Recibe `username` y `password`.
- Valida hash de contraseña.
- Devuelve token y datos básicos del usuario.

### 5.2 Sesión actual
- Endpoint: `GET /api/me`.
- Requiere token.
- Devuelve usuario autenticado activo.

### 5.3 Productos
- `GET /api/products`: lista productos; admite búsqueda por `q`.
- `POST /api/products`: crea producto; solo administrador.
- `PUT /api/products/<id>`: actualiza producto; solo administrador.
- `DELETE /api/products/<id>`: elimina producto; solo administrador.
- `POST /api/products/<id>/image`: carga imagen de producto; solo administrador.

Campos principales de producto:
- `name`
- `description`
- `price`
- `cost_price`
- `stock`
- `min_stock`
- `image_url`
- `created_at`
- `updated_at`

### 5.4 Usuarios
- `GET /api/users`: lista usuarios; solo administrador.
- `POST /api/users`: crea usuario administrador o vendedor; solo administrador.

### 5.5 Ventas
- `POST /api/sales`: registra una venta; administrador o vendedor.
- `GET /api/sales`: lista ventas recientes; solo administrador.

El registro de venta:
1. Valida que existan ítems en el carrito.
2. Busca cada producto.
3. Valida cantidad positiva y stock suficiente.
4. Calcula subtotal y ganancia.
5. Crea la venta.
6. Registra los ítems vendidos.
7. Descuenta stock.
8. Confirma la transacción.

### 5.6 Reportes
- Endpoint: `GET /api/reports/summary`.
- Disponible para administrador.
- Devuelve totales diarios, semanales y mensuales; stock bajo; productos más vendidos; resumen por vendedor; y conteo de productos/unidades.

### 5.7 Salud del servicio
- Endpoint: `GET /api/health`.
- Devuelve estado operativo básico.

## 6. Base de datos

### 6.1 Motor
La aplicación usa SQLite. La base se crea automáticamente en:

```text
backend/beer_house.db
```

### 6.2 Tablas

#### `users`
Almacena usuarios del sistema.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | INTEGER | Identificador primario |
| `name` | TEXT | Nombre visible |
| `username` | TEXT | Usuario único |
| `password_hash` | TEXT | Hash de contraseña |
| `role` | TEXT | `admin` o `seller` |
| `active` | INTEGER | Estado activo/inactivo |
| `created_at` | TEXT | Fecha de creación |

#### `products`
Almacena inventario.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | INTEGER | Identificador primario |
| `name` | TEXT | Nombre único del producto |
| `description` | TEXT | Descripción comercial |
| `price` | REAL | Precio de venta |
| `cost_price` | REAL | Costo del producto |
| `stock` | INTEGER | Unidades disponibles |
| `min_stock` | INTEGER | Umbral de alerta |
| `image_url` | TEXT | Ruta o data URI de imagen |
| `created_at` | TEXT | Fecha de creación |
| `updated_at` | TEXT | Fecha de última actualización |

#### `sales`
Cabecera de ventas.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | INTEGER | Identificador primario |
| `seller_id` | INTEGER | Usuario que realizó la venta |
| `total` | REAL | Total vendido |
| `profit` | REAL | Ganancia calculada |
| `created_at` | TEXT | Fecha y hora de venta |

#### `sale_items`
Detalle de productos vendidos.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | INTEGER | Identificador primario |
| `sale_id` | INTEGER | Venta asociada |
| `product_id` | INTEGER | Producto asociado, nullable si se elimina |
| `product_name` | TEXT | Nombre congelado al momento de la venta |
| `quantity` | INTEGER | Cantidad vendida |
| `unit_price` | REAL | Precio unitario |
| `unit_cost` | REAL | Costo unitario |
| `subtotal` | REAL | Precio por cantidad |
| `profit` | REAL | Ganancia por ítem |

### 6.3 Datos iniciales
Si no existen usuarios, se crean:

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `admin123` |
| Vendedor | `vendedor` | `vendedor123` |

Si no existen productos, se cargan productos de demostración como Corona, Modelo, Club Clásica, Club Negra, Pilsener, Heineken, Amstel y Stella Artois.

## 7. Instalación

### 7.1 Requisitos previos
- Python 3.10 o superior recomendado.
- Node.js 18 o superior recomendado.
- npm.

### 7.2 Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

La API queda disponible en:

```text
http://localhost:5000
```

### 7.3 Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda disponible en:

```text
http://localhost:5173
```

## 8. Configuración

### 8.1 Variables de entorno actuales
- `PORT`: puerto del backend Flask. Valor por defecto: `5000`.
- `VITE_API_URL`: URL base de la API consumida por el frontend. Valor por defecto en frontend: `http://localhost:5000`.

Ejemplo:

```bash
PORT=5000 python app.py
VITE_API_URL=http://localhost:5000 npm run dev
```

### 8.2 Archivos generados en ejecución
- `backend/beer_house.db`: base de datos SQLite.
- `backend/uploads/*`: imágenes subidas desde el panel administrativo.

### 8.3 Reinicio de datos de demostración
Para regenerar la base inicial:

```bash
rm backend/beer_house.db
cd backend
python app.py
```

> Nota: al eliminar la base se pierden productos editados, ventas y usuarios creados localmente.

## 9. Comandos de verificación

### Backend
```bash
cd backend
python -m py_compile app.py
```

### Frontend
```bash
cd frontend
npm run build
```
