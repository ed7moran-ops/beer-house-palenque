# Beer House Palenque

Sistema web de inventario, ventas y reportes para Beer House Palenque con roles de **Administrador** y **Vendedor**.

## Funcionalidades principales

- Login con usuario y contraseña.
- Dashboard administrativo con ventas, ganancias, stock bajo y productos más vendidos.
- Gestión de inventario con creación, edición, eliminación y carga de fotos reales.
- Panel sencillo para vendedores con buscador, carrito, cantidades y total a cobrar.
- Registro de ventas con fecha, hora, producto, cantidad, total y vendedor.
- Descuento automático de stock al confirmar ventas.
- Reportes por vendedor y periodos diario, semanal y mensual.
- Diseño responsive en amarillo, negro y dorado.

## Tecnologías

- Frontend: React + Vite.
- Estilos: Tailwind CSS.
- Backend: Python Flask.
- Base de datos: SQLite.

## Estructura

```text
backend/
  app.py              API Flask, SQLite, seed inicial y carga de imágenes
  requirements.txt    Dependencias Python
  uploads/            Fotos reales de productos cargadas desde el sistema
frontend/
  src/main.jsx        Aplicación React por roles
  src/index.css       Tailwind y estilos globales
  package.json        Scripts de Vite
PRD.md                Product Requirements Document
```

## Usuarios de prueba

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `admin123` |
| Vendedor | `vendedor` | `vendedor123` |

## Base de datos inicial

La base SQLite se crea automáticamente en `backend/beer_house.db` al iniciar Flask. Incluye los usuarios de prueba y estos productos iniciales:

- Corona
- Modelo
- Club Clásica
- Club Negra
- Pilsener
- Pilsener Light
- Heineken
- Amstel
- Stella Artois

## Instalación y ejecución local

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

La API queda disponible en `http://localhost:5000`.

### 2. Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`.

Si el backend está en otra URL, define la variable:

```bash
VITE_API_URL=http://localhost:5000 npm run dev
```

## Scripts útiles

### Backend

```bash
cd backend
python -m py_compile app.py
python app.py
```

### Frontend

```bash
cd frontend
npm run build
npm run dev
```

## Notas de operación

- El administrador puede ver costos y ganancias; el vendedor no recibe esas pantallas.
- Las ventas se validan contra el stock disponible antes de guardarse.
- Las fotos cargadas se guardan en `backend/uploads` y se exponen desde `/uploads/<archivo>`.
- Para reiniciar datos de demostración, detén el backend y elimina `backend/beer_house.db`; se recreará al volver a iniciar.
