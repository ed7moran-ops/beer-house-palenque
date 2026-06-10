# Guía de despliegue y ejecución — Beer House Palenque

Esta guía explica cómo preparar, ejecutar, inicializar, probar y diagnosticar el sistema web de inventario, ventas, reportes y dashboard de Beer House Palenque.

> Alcance: esta documentación no cambia funcionalidades de la aplicación. Solo describe instalación, ejecución, datos iniciales, pruebas manuales, pruebas automatizadas y solución de problemas.

## 1. Resumen de la aplicación

Beer House Palenque está compuesto por dos servicios locales:

| Componente | Tecnología | Carpeta | Puerto local por defecto | URL |
| --- | --- | --- | --- | --- |
| Backend/API | Python + Flask + SQLite | `backend/` | `5000` | `http://localhost:5000` |
| Frontend/POS | React + Vite + Tailwind CSS | `frontend/` | `5173` | `http://localhost:5173` |

El backend expone la API REST, administra sesiones, crea la base SQLite, sirve imágenes cargadas y genera reportes/exportaciones. El frontend consume esa API mediante `VITE_API_URL` y presenta interfaces diferentes para administrador y vendedor.

## 2. Dependencias requeridas

### 2.1 Sistema operativo

Puede ejecutarse en Linux, macOS o Windows. En Windows se recomienda usar PowerShell, Git Bash o WSL para comandos similares a los de esta guía.

### 2.2 Backend

- Python 3.10 o superior recomendado.
- `pip`.
- Módulo estándar `venv` de Python.
- Dependencias Python declaradas en `backend/requirements.txt`:
  - `Flask`
  - `flask-cors`
  - `Werkzeug`

### 2.3 Frontend

- Node.js 18 o superior recomendado.
- npm.
- Dependencias declaradas en `frontend/package.json`:
  - `react`
  - `react-dom`
  - `vite`
  - `@vitejs/plugin-react`
  - `lucide-react`
  - `tailwindcss`
  - `postcss`
  - `autoprefixer`

### 2.4 Base de datos

- SQLite no requiere un servidor independiente.
- La base se guarda como archivo local en `backend/beer_house.db`.
- El archivo se crea automáticamente al importar/iniciar `backend/app.py` si no existe.

## 3. Variables de entorno

### 3.1 Backend

| Variable | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `PORT` | No | `5000` | Puerto donde Flask escucha cuando se ejecuta `python app.py`. |

Ejemplo:

```bash
cd backend
PORT=8000 python app.py
```

Con ese ejemplo, la API quedará en `http://localhost:8000`.

### 3.2 Frontend

| Variable | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `VITE_API_URL` | No | `http://localhost:5000` | URL base de la API Flask que consumirá React. |

Ejemplo si el backend usa el puerto `8000`:

```bash
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev
```

También puede crear un archivo local `frontend/.env.local` para desarrollo:

```env
VITE_API_URL=http://localhost:5000
```

No guarde secretos reales dentro del repositorio. Actualmente la aplicación no requiere variables secretas para ejecutarse localmente.

## 4. Inicialización de la base de datos

### 4.1 Creación automática

No hay migración manual obligatoria para un entorno local nuevo. Al iniciar o importar el backend, se ejecuta la inicialización de base de datos y se crean automáticamente:

- Carpeta `backend/uploads/` para imágenes de productos.
- Carpeta `backend/backups/` para respaldos SQLite.
- Archivo SQLite `backend/beer_house.db`.
- Tablas principales:
  - `users`
  - `branches`
  - `products`
  - `sales`
  - `sale_items`
  - `expenses`
  - `business_settings`
  - `cash_sessions`
  - `inventory_movements`
  - `price_history`
  - `customers`
  - `promotions`
  - `backups`
  - `audit_logs`

### 4.2 Datos iniciales

En una base nueva, el sistema inserta:

- Sucursal inicial: `Matriz Palenque`.
- Usuarios de demostración para administrador y vendedor.
- Productos iniciales como Corona, Modelo, Club Clásica, Club Negra, Pilsener, Pilsener Light, Heineken, Amstel, Stella Artois, Michelada House, Margarita Palenque y Snack Mix.
- Configuración del negocio, moneda y caja inicial.
- Promoción demo `Happy Hour 10%`.
- Ventas y gastos demo para poblar dashboard/reportes.

### 4.3 Reiniciar la base local de demostración

Para reconstruir los datos locales desde cero:

```bash
# Detenga primero el backend si está en ejecución.
rm backend/beer_house.db
cd backend
python app.py
```

Advertencia: este procedimiento elimina ventas, productos editados, usuarios agregados y cualquier dato local almacenado en esa base.

### 4.4 Verificar salud de la API y base

Con el backend iniciado:

```bash
curl http://localhost:5000/api/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

## 5. Usuarios predeterminados

| Rol | Nombre mostrado | Usuario | Contraseña | Acceso principal |
| --- | --- | --- | --- | --- |
| Administrador | `Administrador Beer House` | `admin` | `admin123` | Dashboard, inventario, caja, clientes, historial, reportes, respaldos y configuración operativa. |
| Vendedor | `Vendedor Demo` | `vendedor` | `vendedor123` | Panel de venta, búsqueda de productos, carrito, apertura/cierre de caja y emisión de ticket. |

Cambie estas credenciales antes de usar datos reales o exponer la aplicación fuera de una red local controlada.

## 6. Cómo ejecutar el backend localmente

Desde una terminal en la raíz del repositorio:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

En Windows PowerShell, la activación del entorno virtual suele ser:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Salida esperada aproximada:

```text
* Running on http://127.0.0.1:5000
* Running on http://<IP-local>:5000
```

URLs útiles del backend:

| URL | Uso |
| --- | --- |
| `http://localhost:5000/api/health` | Verificar que la API responde. |
| `http://localhost:5000/uploads/<archivo>` | Acceder a imágenes cargadas desde inventario. |
| `http://localhost:5000/api/reports/export/excel` | Exportación Excel, requiere sesión admin. |
| `http://localhost:5000/api/reports/export/pdf` | Exportación PDF, requiere sesión admin. |

## 7. Cómo ejecutar el frontend localmente

En otra terminal, desde la raíz del repositorio:

```bash
cd frontend
npm install
npm run dev
```

Salida esperada aproximada:

```text
VITE ready
Local:   http://localhost:5173/
```

Abra:

```text
http://localhost:5173
```

Si el backend no está en `http://localhost:5000`, ejecute:

```bash
cd frontend
VITE_API_URL=http://localhost:<PUERTO_BACKEND> npm run dev
```

## 8. URLs de acceso a la aplicación

| Servicio/Pantalla | URL |
| --- | --- |
| Aplicación web/POS | `http://localhost:5173` |
| API Flask | `http://localhost:5000` |
| Health check API | `http://localhost:5000/api/health` |
| Vista principal administrador | `http://localhost:5173` después de iniciar sesión como `admin` |
| Vista principal vendedor | `http://localhost:5173` después de iniciar sesión como `vendedor` |

La navegación del administrador usa secciones internas en la misma página, por ejemplo:

- `http://localhost:5173/#dashboard`
- `http://localhost:5173/#products`
- `http://localhost:5173/#cash`
- `http://localhost:5173/#history`
- `http://localhost:5173/#reports`
- `http://localhost:5173/#backups`

## 9. Pruebas manuales funcionales

Antes de probar, confirme que backend y frontend están activos:

```bash
curl http://localhost:5000/api/health
```

Luego abra `http://localhost:5173`.

### 9.1 Probar login y dashboard administrativo

1. Inicie sesión con:
   - Usuario: `admin`
   - Contraseña: `admin123`
2. Verifique que se muestre el centro de control/POS administrativo.
3. Revise métricas como ventas de hoy, caja esperada, gastos, utilidad neta, productos e inventario.
4. Entre a la sección `dashboard` o use el enlace `#dashboard`.
5. Confirme que existan datos demo en gráficos, productos más vendidos, bajo stock o resumen por vendedor.

Resultado esperado: el dashboard carga indicadores sin errores y muestra información calculada desde la API `/api/reports/summary`.

### 9.2 Probar inventario

Con sesión de administrador:

1. Abra la sección `products` o navegue a `http://localhost:5173/#products`.
2. Busque un producto existente, por ejemplo `Corona` o `Pilsener`.
3. Verifique nombre, precio, costo, stock, stock mínimo, código de barras y sucursal.
4. Cree un producto de prueba con precio, costo, stock y stock mínimo.
5. Edite el stock del producto de prueba.
6. Verifique que el ajuste aparezca en movimientos de inventario.
7. Si prueba carga de imagen, seleccione un archivo `png`, `jpg`, `jpeg` o `webp`.

Resultado esperado: el producto se guarda en SQLite, aparece en la lista y los cambios de stock generan trazabilidad en movimientos.

> Nota: si no desea conservar datos de prueba, reinicie la base local eliminando `backend/beer_house.db` con el backend detenido.

### 9.3 Probar ventas como vendedor

1. Cierre sesión si está como administrador.
2. Inicie sesión con:
   - Usuario: `vendedor`
   - Contraseña: `vendedor123`
3. Abra una caja si la interfaz solicita apertura de caja.
4. Busque un producto por nombre o código.
5. Agregue uno o más productos al carrito.
6. Cambie cantidades y verifique el total a cobrar.
7. Confirme la venta.
8. Abra o imprima el ticket generado.
9. Cierre sesión y vuelva a entrar como administrador.
10. Verifique que la venta aparezca en historial/reportes y que el stock del producto vendido haya disminuido.

Resultado esperado: la API crea la venta, descuenta stock, asocia el vendedor autenticado, registra movimientos de inventario y genera ticket.

### 9.4 Probar validación de stock

1. Inicie sesión como vendedor.
2. Intente vender una cantidad mayor al stock disponible de un producto.

Resultado esperado: la aplicación rechaza la venta con un mensaje de stock insuficiente y no descuenta inventario.

### 9.5 Probar reportes

Con sesión de administrador:

1. Abra `http://localhost:5173/#reports`.
2. Revise ventas por día, semana o mes según las tarjetas disponibles.
3. Revise ventas agrupadas por vendedor.
4. Ejecute exportación Excel desde la interfaz si está disponible.
5. Ejecute exportación PDF desde la interfaz si está disponible.
6. Verifique que las descargas se generen correctamente.

También puede validar las exportaciones desde API con token de administrador. Ejemplo:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -L -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/reports/export/excel \
  -o beer-house-reporte.xlsx

curl -L -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/reports/export/pdf \
  -o beer-house-reporte.pdf
```

Resultado esperado: se descargan archivos `beer-house-reporte.xlsx` y `beer-house-reporte.pdf`.

### 9.6 Probar dashboard después de una venta

1. Registre una venta como vendedor.
2. Inicie sesión como administrador.
3. Vaya a `#dashboard`.
4. Verifique que las métricas de ventas, caja esperada, productos más vendidos o ventas por vendedor reflejen la operación reciente.

Resultado esperado: el dashboard se actualiza con información proveniente de ventas e inventario.

## 10. Pruebas automatizadas

### 10.1 Backend

Las pruebas automatizadas actuales están en `backend/test_app.py` y usan `unittest` con una base SQLite temporal, por lo que no deberían modificar `backend/beer_house.db`.

Ejecute:

```bash
cd backend
python -m unittest test_app.py
```

Las pruebas cubren, entre otros puntos:

- Login de administrador y vendedor.
- Consulta de inventario.
- Resumen de reportes.
- Exportación Excel y PDF.
- Creación de ventas.
- Descuento de stock.
- Rechazo de ventas con stock insuficiente.
- Rechazo de descuentos negativos.

### 10.2 Validación de sintaxis backend

```bash
cd backend
python -m py_compile app.py test_app.py
```

### 10.3 Frontend

El proyecto no define actualmente un script automatizado de pruebas frontend. Los scripts disponibles son:

```bash
cd frontend
npm run build
npm run dev
npm run preview
```

Para validar compilación de producción:

```bash
cd frontend
npm run build
```

Para previsualizar el build:

```bash
cd frontend
npm run preview
```

## 11. Despliegue básico en servidor o red local

Esta sección describe una forma simple de ejecutar la aplicación fuera de la máquina de desarrollo sin modificar código.

### 11.1 Backend

1. Instale Python y dependencias.
2. Cree un entorno virtual.
3. Instale `backend/requirements.txt`.
4. Defina `PORT` si no desea usar `5000`.
5. Ejecute `python app.py`.
6. Asegure que el puerto esté permitido por firewall.

Ejemplo:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=5000 python app.py
```

Para producción real, se recomienda ejecutar Flask detrás de un servidor WSGI y un proxy inverso. Esta guía documenta la ejecución local/simple existente del proyecto.

### 11.2 Frontend

Para servir el frontend compilado:

```bash
cd frontend
VITE_API_URL=http://<HOST_BACKEND>:5000 npm run build
npm run preview
```

`npm run preview` sirve una previsualización del build. Para producción real, puede publicar el contenido generado en `frontend/dist/` con Nginx, Apache, Caddy u otro servidor estático.

### 11.3 Acceso desde otro equipo de la red

1. Identifique la IP local del equipo servidor, por ejemplo `192.168.1.50`.
2. Inicie el backend en `0.0.0.0`; el código ya usa ese host al ejecutar `python app.py`.
3. Inicie Vite; el script `dev` ya usa `--host 0.0.0.0`.
4. Desde otro equipo, abra:
   - Frontend: `http://192.168.1.50:5173`
   - API: `http://192.168.1.50:5000/api/health`
5. Si el navegador muestra errores de conexión a API, inicie el frontend con:

```bash
cd frontend
VITE_API_URL=http://192.168.1.50:5000 npm run dev
```

## 12. Respaldos y archivos generados

| Ruta | Descripción |
| --- | --- |
| `backend/beer_house.db` | Base de datos SQLite local. |
| `backend/uploads/` | Fotos de productos cargadas desde el sistema. |
| `backend/backups/` | Copias de respaldo generadas por el backend. |
| `frontend/dist/` | Build de producción generado por `npm run build`. |
| `frontend/node_modules/` | Dependencias instaladas por npm. |
| `backend/.venv/` | Entorno virtual Python local si se crea dentro de `backend/`. |

Se recomienda respaldar `backend/beer_house.db`, `backend/uploads/` y `backend/backups/` antes de actualizar, mover o reiniciar un entorno con datos reales.

## 13. Solución de problemas

### 13.1 El frontend abre, pero no inicia sesión

Posibles causas:

- Backend apagado.
- `VITE_API_URL` apunta a una URL incorrecta.
- Puerto backend bloqueado.
- Error CORS por usar un host distinto al configurado.

Acciones:

```bash
curl http://localhost:5000/api/health
```

Si no responde, inicie el backend. Si el backend usa otro host o puerto, reinicie el frontend con `VITE_API_URL` correcto.

### 13.2 `Address already in use` o puerto ocupado

Backend:

```bash
cd backend
PORT=8000 python app.py
```

Frontend:

```bash
cd frontend
npm run dev -- --port 5174
```

Si cambia el puerto del backend, recuerde actualizar `VITE_API_URL`.

### 13.3 Error `ModuleNotFoundError: No module named 'flask'`

No se instalaron dependencias Python o no está activo el entorno virtual.

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

En Windows use `\.venv\Scripts\Activate.ps1`.

### 13.4 Error `npm: command not found`

Instale Node.js y npm. Después valide:

```bash
node --version
npm --version
```

Luego ejecute:

```bash
cd frontend
npm install
npm run dev
```

### 13.5 Error en `npm install`

Acciones sugeridas:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

Si está en Windows PowerShell:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

### 13.6 La base de datos parece corrupta o con datos no deseados

Si es un entorno de demostración y puede perder datos:

```bash
# Detenga backend primero.
rm backend/beer_house.db
cd backend
python app.py
```

Si son datos reales, haga copia del archivo antes de cualquier acción:

```bash
cp backend/beer_house.db backend/beer_house.db.backup
```

### 13.7 No se ven imágenes de productos

Verifique:

- Que exista `backend/uploads/`.
- Que el backend esté corriendo.
- Que la URL de imagen apunte a `http://localhost:5000/uploads/<archivo>` o a la URL correcta del backend.
- Que el archivo tenga extensión permitida: `png`, `jpg`, `jpeg` o `webp`.

### 13.8 Una venta no se confirma

Revise:

- Si hay una sesión de caja abierta para el vendedor.
- Si el producto pertenece a la sucursal correcta.
- Si el stock es suficiente.
- Si la cantidad enviada es mayor que cero.
- Si el backend muestra mensajes de validación en la terminal.

### 13.9 Reportes o exportaciones no descargan

Revise:

- Debe iniciar sesión como administrador.
- El token de sesión debe estar vigente en la sesión del navegador.
- La API debe responder en `/api/reports/summary`.
- Para exportaciones directas, use el encabezado `Authorization: Bearer <token>`.

### 13.10 Cambié `PORT`, pero el frontend sigue llamando a `5000`

El frontend lee la URL de API desde `VITE_API_URL` al iniciar Vite. Detenga y reinicie el frontend:

```bash
cd frontend
VITE_API_URL=http://localhost:<NUEVO_PUERTO> npm run dev
```

### 13.11 Los tests fallan por dependencias faltantes

Instale dependencias backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest test_app.py
```

### 13.12 El build frontend falla

Acciones:

```bash
cd frontend
npm install
npm run build
```

Si persiste, revise la salida completa de Vite para identificar el archivo y línea del error.

## 14. Checklist de arranque rápido

Use esta lista para validar un entorno local nuevo:

1. Backend instalado:

   ```bash
   cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
   ```

2. Backend ejecutando:

   ```bash
   cd backend && source .venv/bin/activate && python app.py
   ```

3. API saludable:

   ```bash
   curl http://localhost:5000/api/health
   ```

4. Frontend instalado:

   ```bash
   cd frontend && npm install
   ```

5. Frontend ejecutando:

   ```bash
   cd frontend && npm run dev
   ```

6. Aplicación abierta:

   ```text
   http://localhost:5173
   ```

7. Login admin validado:

   ```text
   admin / admin123
   ```

8. Login vendedor validado:

   ```text
   vendedor / vendedor123
   ```

9. Tests backend ejecutados:

   ```bash
   cd backend && python -m unittest test_app.py
   ```

10. Build frontend validado:

   ```bash
   cd frontend && npm run build
   ```
