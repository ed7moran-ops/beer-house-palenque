# Product Requirements Document (PRD) — Beer House Palenque

## 1. Resumen ejecutivo
Beer House Palenque necesita una aplicación web profesional para administrar inventario de cervezas, registrar ventas por vendedor y consultar reportes operativos. El sistema debe separar claramente los permisos del Administrador y del Vendedor, automatizar el descuento de stock y mantener un historial completo de ventas con fecha, hora, productos, cantidades, totales y responsable.

## 2. Objetivos del producto
- Centralizar productos, precios, costos, stock e imágenes reales de cervezas.
- Permitir ventas rápidas desde un carrito simple para vendedores.
- Registrar automáticamente el vendedor responsable de cada venta.
- Proteger acciones críticas como cambios de precio, eliminación de productos y reportes de ganancias.
- Mostrar alertas de stock bajo y métricas de ventas diarias, semanales y mensuales.
- Entregar una base inicial lista para demostración y operación básica.

## 3. Usuarios y permisos

### Administrador
- Puede ver todo el sistema.
- Puede agregar, editar y eliminar productos.
- Puede subir fotos reales de cervezas.
- Puede cambiar precios, costos, stock y stock mínimo.
- Puede ver inventario completo.
- Puede ver reportes diarios, semanales y mensuales.
- Puede crear usuarios vendedores y administradores.
- Puede revisar qué vendedor realizó cada venta.
- Puede ver ganancias, stock bajo y productos más vendidos.

### Vendedor
- Solo puede registrar ventas.
- Puede buscar productos disponibles.
- Puede seleccionar cantidad vendida.
- Puede generar una venta desde un carrito.
- Puede ver el total a cobrar.
- No puede modificar precios.
- No puede eliminar productos.
- No puede ver ganancias generales.
- Cada venta queda registrada con su nombre de vendedor.

## 4. Módulos funcionales

### Login
- Autenticación con usuario y contraseña.
- Redirección automática por rol.
- Sesión mediante token de API.

### Dashboard de administrador
- Métricas de ventas del día, ganancias semanales, unidades en stock y productos registrados.
- Alertas de stock bajo.
- Productos más vendidos.
- Ventas agrupadas por vendedor.

### Panel de vendedor
- Buscador de productos.
- Catálogo visual con foto, precio y stock disponible.
- Carrito con cantidades editables.
- Total a cobrar.
- Registro de venta con descuento automático de inventario.

### Gestión de inventario
- Crear, editar y eliminar productos.
- Campos: nombre, descripción, precio, costo, stock, stock mínimo e imagen.
- Subida de imágenes reales en formato PNG, JPG, JPEG o WEBP.

### Registro e historial de ventas
- Venta compuesta por uno o más productos.
- Guarda fecha, hora, vendedor, producto, cantidad, precio unitario, subtotal, total y ganancia.
- Controla stock insuficiente antes de confirmar la venta.

### Reportes
- Ventas y ganancias diarias, semanales y mensuales.
- Reporte por vendedor.
- Productos más vendidos.
- Stock bajo.

## 5. Requisitos no funcionales
- Diseño moderno, profesional y responsive para celular y computadora.
- Paleta visual amarillo, negro y dorado.
- Interfaz simple para reducir errores de venta.
- Base SQLite local para instalación sencilla.
- API REST con autorización por roles.

## 6. Stack técnico
- Frontend: React con Vite.
- Estilos: Tailwind CSS.
- Backend: Python Flask.
- Base de datos: SQLite.
- Carga de archivos: almacenamiento local en `backend/uploads`.

## 7. Productos iniciales
- Corona
- Modelo
- Club Clásica
- Club Negra
- Pilsener
- Pilsener Light
- Heineken
- Amstel
- Stella Artois

## 8. Criterios de aceptación
- Un administrador puede iniciar sesión y acceder al dashboard, inventario, historial y usuarios.
- Un vendedor puede iniciar sesión y solo registrar ventas desde el carrito.
- El vendedor no ve ganancias ni formularios para modificar productos.
- Cada venta descuenta stock y queda asociada al vendedor autenticado.
- El administrador puede subir una imagen real por producto.
- El sistema inicia con usuarios de prueba y productos iniciales.
- La aplicación puede ejecutarse localmente siguiendo la documentación.
