# Análisis arquitectónico y sugerencias de mejora — Beer House Palenque

## 1. Resumen del análisis
Beer House Palenque es una aplicación web de inventario y ventas para una tienda de cervezas. El proyecto está organizado como una SPA en React con una API REST en Flask y persistencia local en SQLite. La solución es adecuada para una demostración funcional o una operación pequeña, pero requiere refuerzos antes de considerarse lista para producción.

## 2. Seguridad

### Fortalezas actuales
- Las contraseñas se almacenan con hash mediante Werkzeug, no en texto plano.
- Los endpoints críticos usan autorización por rol mediante decorador `require_auth`.
- Las consultas principales usan parámetros SQL, lo que reduce el riesgo de inyección SQL.
- La carga de imágenes restringe extensiones permitidas y sanea nombres con `secure_filename`.

### Riesgos identificados
- Los tokens de sesión se guardan únicamente en memoria; se pierden al reiniciar el backend y no expiran automáticamente.
- No existe rate limiting en login, por lo que un atacante podría automatizar intentos de fuerza bruta.
- CORS está abierto para cualquier origen, lo cual no es recomendable en producción.
- La aplicación Flask se ejecuta con `debug=True` cuando se lanza directamente.
- No hay validación centralizada de entradas para rangos de precios, costos, stock, longitud de texto y duplicados.
- No hay límites de tamaño para imágenes subidas ni verificación del contenido real del archivo.
- Las credenciales de demostración están documentadas y se crean automáticamente.

### Recomendaciones prioritarias
1. Sustituir sesiones en memoria por JWT firmado con expiración o sesiones persistentes en base de datos/Redis.
2. Configurar `SECRET_KEY`, orígenes CORS permitidos y modo debug mediante variables de entorno.
3. Implementar rate limiting en `/api/login` y bloqueo temporal por intentos fallidos.
4. Agregar validación de payloads con Pydantic, Marshmallow o formularios validados.
5. Limitar tamaño de subida (`MAX_CONTENT_LENGTH`) y validar MIME real de imágenes.
6. Cambiar credenciales iniciales al primer despliegue y forzar rotación de contraseña.
7. Agregar cabeceras de seguridad HTTP y servir la API detrás de HTTPS.

## 3. Usabilidad

### Fortalezas actuales
- Interfaz separada por roles de administrador y vendedor.
- Flujo de venta simple basado en catálogo, buscador y carrito.
- Diseño responsive con estilo visual coherente en negro, amarillo y dorado.
- Mensajes de error y confirmación visibles en login y ventas.

### Oportunidades de mejora
- Mostrar estados de carga durante login, ventas, reportes y guardado de productos.
- Confirmar acciones destructivas, especialmente eliminación de productos.
- Agregar filtros por categoría, stock bajo y disponibilidad en el catálogo.
- Mejorar accesibilidad con etiquetas explícitas, foco visible, navegación por teclado y contraste auditado.
- Mostrar comprobante o resumen imprimible después de registrar una venta.
- Agregar paginación o búsqueda server-side para ventas y productos cuando crezca la base.
- Incorporar ayuda contextual para campos como costo, stock mínimo y ganancia.

## 4. Rendimiento

### Fortalezas actuales
- La arquitectura monolítica ligera reduce complejidad operativa.
- SQLite es suficiente para demostración y bajo volumen.
- Vite genera bundles optimizados para producción.

### Riesgos identificados
- La base de datos no tiene índices adicionales para búsquedas frecuentes por fecha, vendedor o producto.
- El endpoint de productos devuelve todos los registros, lo que puede degradarse con inventarios grandes.
- Las imágenes subidas se sirven sin procesamiento, compresión ni variantes responsivas.
- Los reportes agregan datos en tiempo real sin caché.

### Recomendaciones
1. Crear índices para `sales.created_at`, `sales.seller_id`, `sale_items.product_id` y búsquedas de productos.
2. Agregar paginación, filtros y ordenamiento server-side en productos y ventas.
3. Generar miniaturas y comprimir imágenes al subirlas.
4. Implementar caché corto para reportes del dashboard.
5. Migrar a PostgreSQL si el negocio requiere múltiples terminales, concurrencia alta o despliegue multiusuario.

## 5. Diseño y arquitectura

### Fortalezas actuales
- Separación clara entre frontend y backend.
- Modelo de datos simple y entendible.
- Decorador de autorización reutilizable.
- Componentes React reutilizables para paneles, filas y estados vacíos.

### Oportunidades de mejora arquitectónica
- Dividir `backend/app.py` en módulos: configuración, base de datos, autenticación, productos, ventas, reportes y usuarios.
- Dividir `frontend/src/main.jsx` en componentes, páginas, hooks y cliente API.
- Incorporar migraciones de base de datos con Alembic o Flask-Migrate.
- Añadir pruebas unitarias y de integración para ventas, stock y permisos.
- Agregar documentación OpenAPI/Swagger para la API REST.
- Manejar errores globales en backend y frontend con respuestas homogéneas.
- Configurar linting y formateo: Ruff/Black para Python y ESLint/Prettier para React.

## 6. Hoja de ruta sugerida

### Corto plazo
- Variables de entorno para configuración sensible.
- Validación de datos y límites de archivos.
- Confirmaciones de eliminación y estados de carga.
- Pruebas mínimas de backend para login, productos y ventas.

### Mediano plazo
- Refactor modular del backend y frontend.
- Paginación, filtros avanzados e índices SQL.
- Auditoría de acciones administrativas.
- Reportes exportables a CSV/PDF.

### Largo plazo
- PostgreSQL y despliegue con Gunicorn/Nginx.
- Gestión avanzada de usuarios, recuperación de contraseña y permisos granulares.
- Multi-sucursal, categorías, proveedores y compras.
- Integración con lector de código de barras o punto de venta físico.
