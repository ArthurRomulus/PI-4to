# Cambios de Base de Datos - Adaptación al Nuevo Esquema SQL

## Resumen de Cambios

El proyecto ha sido adaptado para utilizar un nuevo esquema de base de datos más robusto y escalable. Los cambios principales son:

### Tablas Anteriores (antiguas):
- `usuarios` (id, nombre, embedding, fecha_registro)
- `accesos` (id, id_usuario, nombre, status, fecha)

### Nuevas Tablas:
1. **ROLES** - Gestión de roles del sistema
2. **USERS** - Usuarios principales del sistema
3. **ADMINS** - Administradores con autenticación PIN
4. **STAFF** - Personal del sistema
5. **FACIAL_RECORDS** - Registros de embeddings faciales
6. **ACCESS_LOG** - Historial completo de accesos

## Archivos Modificados

### 1. `database/conexion.py`
- **Cambio**: Actualización completa de MySQL a SQLite con nuevo esquema
- **Mejoras**:
  - Cambio de `mysql.connector` a `sqlite3`
  - Implementación de todas las 6 nuevas tablas
  - Habilitación de foreign_keys con `PRAGMA foreign_keys = ON`
  - Creación automática de estructura en el archivo `crear_tablas()`

### 2. `database/consultas.py`
- **Cambio**: Refactorización completa de funciones
- **Nuevas funciones**:
  - `crear_rol(role_name)` - Crear nuevos roles
  - `obtener_rol_por_nombre(role_name)` - Buscar roles
  - `obtener_usuario_por_id(id_user)` - Buscar usuario por ID
  - `crear_admin(email, pin_hash, id_role)` - Crear administradores
  - `obtener_admin_por_email(email)` - Buscar admin
  - `crear_staff(name, position, id_role)` - Crear personal
  - `eliminar_usuario_por_id(id_user)` - Eliminar por ID

- **Funciones Actualizadas** (mantienen compatibilidad):
  - `guardar_usuario()` - Ahora guarda en USERS + FACIAL_RECORDS
  - `obtener_usuarios()` - Lee de USERS + FACIAL_RECORDS
  - `obtener_lista_usuarios()` - Devuelve lista compatible
  - `obtener_usuario_por_nombre()` - Busca en USERS
  - `registrar_acceso()` - Registra en ACCESS_LOG
  - `obtener_historial_accesos()` - Lee de ACCESS_LOG

- **Funciones Mejoradas**:
  - `limpiar_embeddings_invalidos()` - Funciona con nuevas tablas
  - `eliminar_usuario_por_nombre()` - Elimina en cascada

### 3. `verificar.py`
- **Cambio**: Adaptación para usar las nuevas funciones de BD
- **Mejora**: Usa `obtener_usuarios()` de `consultas` directamente

### 4. `test_integration.py`
- **Cambio**: Agregado test para creación de roles
- **Mejora**: Verifica que el rol 'usuario' exista antes de guardar

### 5. `database/guardar_usuario.py`
- **Cambio**: Ahora es un wrapper de `guardar_usuario()` de consultas
- **Mejora**: Acepta parámetro opcional `account_number`

### 6. `database/schema.sql` (NUEVO)
- **Contenido**: Esquema SQL completo para referencia
- **Uso**: Documentación y/o inicialización alternativa

## Cambios en el Flujo de Datos

### Guardar Usuario (antes vs ahora):
```
ANTES:
usuarios (nombre, embedding) 

AHORA:
USERS (id_user, id_role, name, account_number)
  ↓
FACIAL_RECORDS (id_record, id_user, face_encoding)
```

### Registrar Acceso (antes vs ahora):
```
ANTES:
accesos (id_usuario, nombre, status)

AHORA:
ACCESS_LOG (id_user, id_role, status)
```

## Compatibilidad Backward

❌ **ADVERTENCIA**: La migración NO es automática. 

Si tienes datos en la BD anterior, necesitas hacer una migración manual:

```python
from database.conexion import obtener_conexion
from database.consultas import guardar_usuario, crear_rol
import pickle

# 1. Crear roles
crear_rol("usuario")

# 2. Migrar usuarios (si tienes BD antigua):
conn = obtener_conexion()
cursor = conn.cursor()
# Lógica de migración personalizada según tus datos
```

## Nueva API de Base de Datos

### Usuarios:
```python
from database.consultas import (
    guardar_usuario,          # Guardar nuevo usuario
    obtener_usuarios,         # Obtener todos con embeddings
    obtener_usuario_por_nombre,  # Buscar por nombre
    obtener_usuario_por_id,   # Buscar por ID
    obtener_lista_usuarios,   # Lista para UI
    eliminar_usuario_por_nombre,  # Eliminar por nombre
    eliminar_usuario_por_id   # Eliminar por ID
)
```

### Roles:
```python
from database.consultas import (
    crear_rol,                # Crear nuevo rol
    obtener_rol_por_nombre    # Buscar rol
)
```

### Administradores:
```python
from database.consultas import (
    crear_admin,              # Crear admin
    obtener_admin_por_email   # Buscar admin
)
```

### Personal:
```python
from database.consultas import (
    crear_staff               # Crear staff
)
```

### Accesos:
```python
from database.consultas import (
    registrar_acceso,         # Registrar acceso
    obtener_historial_accesos # Obtener historial
)
```

## Validación de Cambios

✅ **Todos los tests pasaron correctamente**:
- Creación de tablas
- Inserción de usuarios
- Lectura de usuarios
- Comparación de embeddings
- Creación de roles

## Próximos Pasos Recomendados

1. **Migración de Datos**: Si tienes usuarios anteriores, ejecuta un script de migración
2. **Actualizar UI**: Asegúrate de que todos los componentes UI usen las nuevas funciones
3. **Desplegar**: Borra la BD antigua (`database/usuarios.db`) antes de desplegar
4. **Backup**: Mantén un backup de la BD antigua antes de eliminarla
