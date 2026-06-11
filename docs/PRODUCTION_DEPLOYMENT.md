# Despliegue de producción - Beer House Palenque

Esta guía deja la aplicación disponible en internet para computadoras, tablets y celulares con un solo URL público. La opción recomendada usa **Render Free Web Service** con runtime **Docker** porque permite desplegar Flask + React desde el `Dockerfile` incluido, sin servidores propios.

## Arquitectura de producción

- **Frontend React/Vite**: el `Dockerfile` lo compila con `npm run build` y Flask sirve los archivos estáticos desde `frontend/dist`.
- **Backend Flask**: corre con Gunicorn mediante `scripts/start_production.sh`.
- **Base de datos SQLite**: se guarda en `DB_PATH` y se respalda desde el panel de administrador o con `scripts/backup_sqlite.sh`.
- **URL público**: Render asigna un dominio HTTPS como `https://beer-house-palenque.onrender.com`.
- **PWA móvil**: el navegador móvil puede abrir el URL o instalarlo desde el manifiesto existente.

> Nota importante: el plan gratuito de Render no garantiza almacenamiento persistente después de redeploys o recreaciones del servicio. Para producción real, ejecute respaldos frecuentes y descargue cada respaldo fuera del servidor. Si el negocio requiere retención garantizada en el servidor, agregue un disco persistente de pago o migre SQLite a un servicio gestionado.

## Variables de entorno

Copie `.env.production.example` al panel de Render o úselo como referencia local. Variables mínimas:

| Variable | Propósito | Ejemplo |
| --- | --- | --- |
| `APP_ENV` / `FLASK_ENV` | Activa modo producción y headers HTTPS | `production` |
| `SECRET_KEY` | Firma segura de Flask | generado por Render |
| `ADMIN_PASSWORD` | Contraseña inicial del usuario `admin` | valor privado fuerte |
| `SELLER_PASSWORD` | Contraseña inicial del usuario `vendedor` | valor privado fuerte |
| `CORS_ORIGINS` | Orígenes permitidos para API y uploads | `https://beer-house-palenque.onrender.com` |
| `DB_PATH` | Ruta del archivo SQLite en el contenedor Docker | `/app/data/beer_house.db` |
| `UPLOAD_FOLDER` | Carpeta de imágenes cargadas en el contenedor Docker | `/app/data/uploads` |
| `BACKUP_FOLDER` | Carpeta de respaldos SQLite en el contenedor Docker | `/app/data/backups` |
| `FRONTEND_DIST` | Carpeta de build React en el contenedor Docker | `/app/frontend/dist` |
| `SEED_DEMO_DATA` | Carga ventas demo. En producción use `0` | `0` |
| `WEB_CONCURRENCY` | Workers Gunicorn. SQLite debe usar 1 | `1` |

## Despliegue en Render Free

1. Suba este repositorio a GitHub.
2. Cree una cuenta en Render y seleccione **New + > Blueprint**.
3. Conecte el repositorio y Render detectará `render.yaml` con `runtime: docker`.
4. Configure estos secretos en Render antes de crear el servicio:
   - `ADMIN_PASSWORD`: contraseña fuerte para el administrador.
   - `SELLER_PASSWORD`: contraseña fuerte para vendedor.
   - `CORS_ORIGINS`: use el dominio final de Render. Si aún no lo conoce, primero use `*`, despliegue, copie el URL público y cámbielo a ese URL exacto.
5. Espere a que Render construya la imagen desde `./Dockerfile`; al iniciar el contenedor usará el `CMD` del Dockerfile, que ejecuta `./scripts/start_production.sh`.
6. Abra el URL público `https://<servicio>.onrender.com` desde una computadora y desde un celular.
7. Entre con:
   - Usuario administrador: `admin` + el valor de `ADMIN_PASSWORD`.
   - Usuario vendedor: `vendedor` + el valor de `SELLER_PASSWORD`.
8. Cambie o cree usuarios desde el panel de administrador y no comparta las credenciales iniciales.

## Checklist detallado para Render con Docker

Para una lista operativa completa de creación de cuenta, conexión con GitHub, despliegue por Dockerfile, variables, contraseñas, URL público, pruebas desde computadora/teléfono e instalación PWA en Android, use [`docs/RENDER_DEPLOYMENT_CHECKLIST.md`](RENDER_DEPLOYMENT_CHECKLIST.md).

## Despliegue manual con Docker

También puede ejecutar el contenedor localmente o en cualquier nube que acepte Docker:

```bash
docker build -t beer-house-palenque .
docker run --rm -p 5000:5000 \
  -e SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  -e ADMIN_PASSWORD="cambie-esto" \
  -e SELLER_PASSWORD="cambie-esto" \
  -e CORS_ORIGINS="https://su-dominio-publico" \
  -e SEED_DEMO_DATA=0 \
  -v "$PWD/data:/app/data" \
  beer-house-palenque
```

## Configuración de URL público

- Render entrega HTTPS automáticamente en `https://<servicio>.onrender.com`.
- Para dominio propio, abra el servicio en Render, vaya a **Settings > Custom Domains**, agregue su dominio y cree el registro DNS indicado por Render.
- Después de fijar el dominio final, actualice `CORS_ORIGINS` con el dominio exacto para evitar uso abierto de CORS.
- Si el frontend se sirve desde otro dominio, compile con `VITE_API_URL=https://api.su-dominio`.

## Estrategia de respaldos SQLite

### Dentro de la aplicación

- El sistema crea un respaldo automático diario si `auto_backup_enabled` está activo.
- El administrador puede crear y descargar respaldos desde **Respaldos y recuperación**.
- Los respaldos quedan registrados en la tabla `backups` y se guardan en `BACKUP_FOLDER`.

### Fuera del servidor

Ejecute el script desde su computadora, una laptop del negocio o un cron externo:

```bash
APP_URL="https://beer-house-palenque.onrender.com" \
ADMIN_PASSWORD="contraseña-admin-producción" \
BACKUP_DIR="$HOME/beer-house-backups" \
./scripts/backup_sqlite.sh
```

Recomendación operativa:

- Descargar un respaldo al cierre de cada día.
- Mantener al menos 30 respaldos diarios y 12 respaldos mensuales.
- Guardar una copia adicional en Google Drive, OneDrive, Dropbox o un disco externo.
- Probar restauración una vez al mes en un entorno local antes de confiar en el respaldo.

## Endurecimiento de seguridad incluido

- Flask corre con Gunicorn y `debug=False` en producción.
- CORS se restringe con `CORS_ORIGINS`.
- Las contraseñas iniciales se toman de variables de entorno, no quedan fijas en producción.
- Se agregan headers `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y HSTS en producción.
- Las cookies quedan marcadas `HttpOnly`, `SameSite=Lax` y `Secure` bajo HTTPS.
- El tamaño máximo de carga se limita con `MAX_CONTENT_LENGTH`.
- Las cargas de producto aceptan únicamente `png`, `jpg`, `jpeg` y `webp`.
- SQLite se ejecuta con `WEB_CONCURRENCY=1` para evitar escrituras concurrentes peligrosas.

## Verificación después del despliegue

```bash
curl -fsS https://beer-house-palenque.onrender.com/api/health
```

Debe responder `status: ok`. Luego pruebe desde un celular con datos móviles para confirmar que no depende de la red local del negocio.
