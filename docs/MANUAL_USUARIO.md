# Manual de Usuario — Beer House Palenque

## 1. Introducción
Beer House Palenque es una aplicación web para controlar inventario de cervezas, registrar ventas y revisar reportes del negocio. El sistema tiene dos perfiles:

- **Administrador:** controla inventario, usuarios y reportes.
- **Vendedor:** registra ventas de forma rápida desde un carrito.

El objetivo del sistema es reducir errores manuales, mantener stock actualizado y facilitar la consulta de ventas por periodo y por vendedor.

## 2. Requisitos mínimos

### Equipo del usuario
- Computadora, laptop, tablet o teléfono con navegador moderno.
- Resolución mínima recomendada: 360 px de ancho para móviles.
- Conexión a la red donde esté publicado el sistema.

### Navegadores recomendados
- Google Chrome actualizado.
- Microsoft Edge actualizado.
- Mozilla Firefox actualizado.
- Safari actualizado.

### Datos de acceso
Solicite a un administrador su usuario y contraseña. Para ambientes de demostración existen credenciales de prueba:

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `admin123` |
| Vendedor | `vendedor` | `vendedor123` |

## 3. Acceso al sistema

1. Abra la URL de la aplicación en el navegador.
2. En la pantalla de inicio de sesión, escriba su usuario.
3. Escriba su contraseña.
4. Presione **Entrar al sistema**.
5. El sistema abrirá automáticamente la vista correspondiente a su rol.

### Cierre de sesión
Presione el botón **Salir** ubicado en la barra superior. Esto elimina la sesión del navegador y vuelve al login.

## 4. Funciones principales

## 4.1 Funciones para administrador

### Dashboard
El dashboard muestra indicadores del negocio:
- Ventas del día.
- Ganancias semanales.
- Unidades en stock.
- Productos registrados.
- Productos con stock bajo.
- Productos más vendidos.
- Ventas agrupadas por vendedor.

### Gestión de inventario
Desde el panel de inventario puede:
1. Crear productos.
2. Editar nombre, descripción, precio, costo, stock y stock mínimo.
3. Eliminar productos.
4. Subir una imagen real del producto.

Recomendación: mantenga actualizado el costo para que las ganancias se calculen correctamente.

### Gestión de usuarios
Desde la sección de usuarios puede crear:
- Administradores.
- Vendedores.

Cada usuario debe tener nombre, usuario, contraseña y rol.

### Historial de ventas
El administrador puede revisar las ventas recientes, incluyendo:
- Fecha y hora.
- Vendedor responsable.
- Productos vendidos.
- Cantidades.
- Total de la venta.
- Ganancia.

## 4.2 Funciones para vendedor

### Buscar producto
1. Ingrese al panel de vendedor.
2. Use el campo **Buscar producto**.
3. Escriba parte del nombre de la cerveza.
4. Revise precio y stock disponible.

### Agregar productos al carrito
1. Ubique el producto.
2. Presione **Agregar**.
3. El producto aparecerá en el carrito.
4. Ajuste la cantidad si es necesario.

### Registrar venta
1. Verifique los productos en el carrito.
2. Confirme el total a cobrar.
3. Presione **Registrar venta**.
4. El sistema guardará la venta y descontará stock automáticamente.
5. Aparecerá un mensaje de confirmación con el total registrado.

## 5. Ejemplos de uso

### Ejemplo 1: registrar una venta de una cerveza
1. Inicie sesión como vendedor.
2. Busque **Corona**.
3. Presione **Agregar**.
4. Verifique que la cantidad sea `1`.
5. Revise el total a cobrar.
6. Presione **Registrar venta**.

Resultado: el sistema registra la venta con el vendedor autenticado y descuenta una unidad de Corona del inventario.

### Ejemplo 2: vender varias unidades
1. Inicie sesión como vendedor.
2. Agregue **Pilsener** al carrito.
3. Cambie la cantidad a `6`.
4. Agregue otro producto si el cliente lo solicita.
5. Revise el total.
6. Presione **Registrar venta**.

Resultado: se registra una venta con varios ítems y se descuentan las cantidades correspondientes.

### Ejemplo 3: crear un producto nuevo
1. Inicie sesión como administrador.
2. Vaya a la sección de inventario.
3. Complete nombre, descripción, precio, costo, stock y stock mínimo.
4. Guarde el producto.
5. Opcionalmente cargue una imagen real.

Resultado: el producto queda disponible para ventas.

### Ejemplo 4: revisar productos con bajo stock
1. Inicie sesión como administrador.
2. Abra el dashboard.
3. Revise la sección de stock bajo.
4. Reponga los productos cuyo stock esté cerca o por debajo del mínimo.

Resultado: el administrador identifica productos que requieren compra o reposición.

## 6. Preguntas frecuentes

### ¿Por qué no puedo entrar al sistema?
Verifique que el usuario y la contraseña sean correctos. Si el problema continúa, solicite al administrador que revise si su usuario está activo.

### ¿Por qué no puedo editar precios?
La edición de precios está reservada para administradores. Los vendedores solo pueden registrar ventas.

### ¿Qué ocurre si intento vender más unidades que el stock disponible?
El sistema rechaza la venta e indica que existe stock insuficiente para el producto.

### ¿Puedo eliminar un producto que ya fue vendido?
Sí, pero el historial conserva el nombre del producto vendido para no perder trazabilidad. Aun así, se recomienda desactivar o dejar sin stock productos históricos en lugar de eliminarlos si se requiere auditoría estricta.

### ¿Dónde se guardan las imágenes?
Las imágenes subidas desde el administrador se guardan en el servidor, dentro de la carpeta `backend/uploads`.

### ¿Qué hago si el total mostrado no coincide con el precio esperado?
Solicite al administrador revisar el precio del producto en inventario. El vendedor no puede modificar precios desde el carrito.

### ¿Cómo reinicio los datos de prueba?
Esta acción debe hacerla personal técnico eliminando la base local `backend/beer_house.db` y reiniciando el backend. Se perderán datos locales.
