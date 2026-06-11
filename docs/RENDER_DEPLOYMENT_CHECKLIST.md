# Checklist de despliegue en Render - Beer House Palenque

Use esta lista para publicar Beer House Palenque con **Render**, **GitHub** y el `Dockerfile` incluido en este repositorio. Al finalizar tendrá un URL HTTPS público para abrir la app desde computadora, tablet y teléfono.

## 0. Antes de empezar

- [ ] Tener una cuenta de correo disponible para Render.
- [ ] Tener una cuenta de GitHub.
- [ ] Subir este repositorio a GitHub, por ejemplo como `beer-house-palenque`.
- [ ] Confirmar que el repositorio contiene estos archivos en la raíz:
  - `Dockerfile`
  - `render.yaml`
  - `backend/app.py`
  - `frontend/package.json`
- [ ] Tener a mano dos contraseñas privadas y fuertes:
  - Una para el usuario administrador `admin`.
  - Una para el usuario vendedor `vendedor`.

> Importante: no use `admin123` ni `vendedor123` en producción. Esos valores son solo para pruebas locales.

## 1. Crear la cuenta de Render

- [ ] Entrar a <https://render.com/>.
- [ ] Hacer clic en **Get Started** o **Sign Up**.
- [ ] Registrarse con GitHub, Google o correo electrónico.
- [ ] Verificar el correo si Render lo solicita.
- [ ] Entrar al **Dashboard** de Render.
- [ ] Crear o seleccionar un workspace personal para el negocio.

## 2. Conectar GitHub con Render

- [ ] En Render, abrir el **Dashboard**.
- [ ] Hacer clic en **New +**.
- [ ] Elegir **Web Service** si hará el despliegue manual con Docker, o **Blueprint** si quiere que Render lea `render.yaml` automáticamente.
- [ ] Cuando Render pida conectar un proveedor Git, elegir **GitHub**.
- [ ] Autorizar Render en GitHub.
- [ ] En la autorización, dar acceso al repositorio `beer-house-palenque`.
  - Recomendado: elegir **Only select repositories** y seleccionar solo este repositorio.
- [ ] Volver a Render y verificar que el repositorio aparece en la lista.

## 3. Desplegar usando el Dockerfile

Beer House Palenque ya incluye un `Dockerfile` de producción. Ese contenedor compila React, instala Flask/Gunicorn y arranca la aplicación con `scripts/start_production.sh`.

### Opción A: Blueprint recomendado con `render.yaml`

- [ ] En Render, hacer clic en **New + > Blueprint**.
- [ ] Seleccionar el repositorio `beer-house-palenque`.
- [ ] Confirmar que Render detecta el archivo `render.yaml`.
- [ ] Revisar que el servicio se llama `beer-house-palenque`.
- [ ] Confirmar que el runtime sea **Docker**.
- [ ] Revisar que el Dockerfile sea `./Dockerfile` y el contexto sea `.`.
- [ ] Configurar las variables secretas que Render solicite antes de crear el servicio:
  - `ADMIN_PASSWORD`
  - `SELLER_PASSWORD`
  - `CORS_ORIGINS`
- [ ] Crear el Blueprint y esperar el primer deploy.

### Opción B: Web Service manual con Docker

- [ ] En Render, hacer clic en **New + > Web Service**.
- [ ] Seleccionar el repositorio `beer-house-palenque`.
- [ ] En **Language** o **Runtime**, elegir **Docker**.
- [ ] En **Name**, escribir `beer-house-palenque` o un nombre similar.
- [ ] En **Branch**, elegir la rama principal, por ejemplo `main`.
- [ ] En **Root Directory**, dejar vacío si el repositorio completo está en la raíz.
- [ ] En **Dockerfile Path**, usar `./Dockerfile`.
- [ ] En **Docker Build Context Directory**, usar `.`.
- [ ] En **Plan**, elegir el plan que vaya a usar. Para pruebas puede ser Free si está disponible para su cuenta.
- [ ] En **Advanced > Environment Variables**, agregar las variables de la sección 4.
- [ ] Hacer clic en **Create Web Service**.
- [ ] Esperar a que el log muestre que la imagen Docker se construyó y que Gunicorn inició correctamente.

## 4. Variables de entorno a configurar

Configure estas variables en Render en **Service > Environment**. Si usa el Blueprint, varias ya quedan definidas en `render.yaml`; las marcadas como secretas se deben escribir manualmente.

| Variable | Valor recomendado en Render Docker | ¿Secreta? | Para qué sirve |
| --- | --- | --- | --- |
| `APP_ENV` | `production` | No | Activa comportamiento de producción. |
| `FLASK_ENV` | `production` | No | Desactiva modo debug de Flask. |
| `SECRET_KEY` | Generado por Render o valor aleatorio largo | Sí | Firma sesiones y cookies. |
| `ADMIN_PASSWORD` | Contraseña fuerte privada | Sí | Contraseña inicial del usuario `admin`. |
| `SELLER_PASSWORD` | Contraseña fuerte privada | Sí | Contraseña inicial del usuario `vendedor`. |
| `CORS_ORIGINS` | URL pública exacta de Render | No | Permite que el navegador use la API desde ese dominio. |
| `DB_PATH` | `/app/data/beer_house.db` | No | Archivo SQLite dentro del contenedor. |
| `UPLOAD_FOLDER` | `/app/data/uploads` | No | Fotos de productos cargadas desde la app. |
| `BACKUP_FOLDER` | `/app/data/backups` | No | Respaldos SQLite generados por la app. |
| `FRONTEND_DIST` | `/app/frontend/dist` | No | Build de React servido por Flask. |
| `SEED_DEMO_DATA` | `0` | No | Evita cargar ventas demo en producción. |
| `WEB_CONCURRENCY` | `1` | No | Mantiene un worker Gunicorn para proteger SQLite. |
| `MAX_CONTENT_LENGTH` | `8388608` | No | Limita uploads a 8 MB. |

Notas importantes:

- [ ] `SECRET_KEY` debe ser largo y aleatorio. Si usa Blueprint, `render.yaml` pide a Render generarlo automáticamente.
- [ ] `CORS_ORIGINS` debe ser el URL final, por ejemplo `https://beer-house-palenque.onrender.com`.
- [ ] Si todavía no conoce el URL final, puede hacer el primer deploy con `CORS_ORIGINS=*`, copiar el URL público y luego cambiar `CORS_ORIGINS` al URL exacto.
- [ ] En el plan gratuito, los archivos SQLite, uploads y backups dentro del contenedor pueden perderse en redeploys o recreaciones. Descargue respaldos con frecuencia o agregue almacenamiento persistente si Render lo ofrece en su plan.

## 5. Configurar `ADMIN_PASSWORD` y `SELLER_PASSWORD`

- [ ] Crear dos contraseñas distintas.
- [ ] Usar mínimo 12 caracteres.
- [ ] Combinar mayúsculas, minúsculas, números y símbolos.
- [ ] No usar nombres del negocio, fechas, teléfonos ni contraseñas repetidas.
- [ ] En Render, abrir el servicio `beer-house-palenque`.
- [ ] Ir a **Environment**.
- [ ] Agregar o editar:
  - `ADMIN_PASSWORD` = contraseña privada para iniciar sesión como `admin`.
  - `SELLER_PASSWORD` = contraseña privada para iniciar sesión como `vendedor`.
- [ ] Guardar los cambios.
- [ ] Si Render pregunta si desea redeploy, aceptar o hacer **Manual Deploy > Deploy latest commit**.
- [ ] Guardar las contraseñas en un gestor seguro o en un lugar físico protegido.

Credenciales iniciales después del deploy:

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | Valor configurado en `ADMIN_PASSWORD` |
| Vendedor | `vendedor` | Valor configurado en `SELLER_PASSWORD` |

## 6. Crear y confirmar el URL público

Render crea automáticamente un URL HTTPS para cada Web Service.

- [ ] Entrar al servicio `beer-house-palenque` en Render.
- [ ] Abrir la pestaña **Overview** o **Settings**.
- [ ] Copiar el URL público con formato parecido a:

```text
https://beer-house-palenque.onrender.com
```

- [ ] Abrir ese URL en el navegador de la computadora.
- [ ] Si usó `CORS_ORIGINS=*` durante el primer deploy, volver a **Environment** y cambiarlo por el URL exacto.
- [ ] Guardar cambios y redeployar.
- [ ] Si desea un dominio propio, ir a **Settings > Custom Domains**, agregar el dominio y seguir las instrucciones DNS que Render muestre.

## 7. Probar la app desplegada desde una computadora

- [ ] Abrir el URL público en Chrome, Edge, Firefox o Safari.
- [ ] Confirmar que carga la pantalla de login.
- [ ] Entrar como administrador:
  - Usuario: `admin`
  - Contraseña: valor de `ADMIN_PASSWORD`
- [ ] Confirmar que se ve el dashboard administrativo.
- [ ] Crear o editar un producto de prueba.
- [ ] Subir una foto pequeña de producto en formato `png`, `jpg`, `jpeg` o `webp`.
- [ ] Cerrar sesión.
- [ ] Entrar como vendedor:
  - Usuario: `vendedor`
  - Contraseña: valor de `SELLER_PASSWORD`
- [ ] Buscar un producto.
- [ ] Agregarlo al carrito.
- [ ] Registrar una venta de prueba.
- [ ] Volver a entrar como administrador y confirmar que la venta aparece en reportes.
- [ ] Probar el endpoint de salud abriendo:

```text
https://beer-house-palenque.onrender.com/api/health
```

Debe responder con estado correcto de la API.

## 8. Probar la app desplegada desde un teléfono

- [ ] Conectar el teléfono a datos móviles o Wi-Fi.
- [ ] Abrir Chrome en Android o Safari/Chrome en iPhone.
- [ ] Escribir el URL público de Render.
- [ ] Confirmar que la pantalla se adapta al tamaño del teléfono.
- [ ] Iniciar sesión como vendedor.
- [ ] Buscar productos y agregar uno al carrito.
- [ ] Confirmar que botones, cantidades y totales se ven correctamente.
- [ ] Registrar una venta pequeña de prueba.
- [ ] Cerrar sesión.
- [ ] Iniciar sesión como administrador.
- [ ] Confirmar que los reportes se pueden consultar desde el teléfono.
- [ ] Si el teléfono no carga la app, probar:
  - Abrir una pestaña incógnita.
  - Revisar que el URL empieza con `https://`.
  - Confirmar en Render que el deploy terminó en estado **Live**.
  - Revisar que `CORS_ORIGINS` sea el URL público exacto.

## 9. Instalar la PWA en Android

Beer House Palenque incluye manifiesto PWA y service worker, por lo que Chrome en Android puede instalarla como app.

- [ ] En Android, abrir **Chrome**.
- [ ] Entrar al URL público de Render.
- [ ] Esperar a que cargue completamente la pantalla de login.
- [ ] Tocar el menú de Chrome de tres puntos `⋮`.
- [ ] Tocar **Agregar a la pantalla principal** o **Instalar app**.
- [ ] Confirmar el nombre, por ejemplo `Beer House Palenque`.
- [ ] Tocar **Instalar** o **Agregar**.
- [ ] Volver a la pantalla principal del teléfono.
- [ ] Abrir el ícono de Beer House Palenque.
- [ ] Confirmar que abre en una ventana tipo app y muestra el login.
- [ ] Iniciar sesión como vendedor y hacer una prueba rápida de navegación.

Si Android no muestra la opción de instalar:

- [ ] Confirmar que está usando Chrome actualizado.
- [ ] Confirmar que el sitio abre con HTTPS.
- [ ] Recargar la página una vez.
- [ ] Esperar unos segundos en la pantalla de login.
- [ ] Revisar que no esté navegando en modo incógnito.

## 10. Checklist final de salida a producción

- [ ] Render muestra el servicio en estado **Live**.
- [ ] El URL público abre desde computadora.
- [ ] El URL público abre desde teléfono.
- [ ] `ADMIN_PASSWORD` y `SELLER_PASSWORD` son fuertes y diferentes.
- [ ] `CORS_ORIGINS` contiene el URL HTTPS final, no `*`.
- [ ] Se puede iniciar sesión como `admin`.
- [ ] Se puede iniciar sesión como `vendedor`.
- [ ] Se registró una venta de prueba correctamente.
- [ ] Se verificó el reporte de ventas.
- [ ] Se probó la instalación PWA en Android.
- [ ] Se creó el primer respaldo desde el panel de administrador o con `scripts/backup_sqlite.sh`.
