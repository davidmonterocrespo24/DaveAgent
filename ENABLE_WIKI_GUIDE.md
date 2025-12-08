# 🚀 Guía Rápida: Habilitar y Subir Wiki a GitHub

## ⚠️ Problema Actual
El script `upload_wiki.py` falló porque la wiki no está habilitada en tu repositorio de GitHub.

Error: `remote: Repository not found`

## ✅ Solución: Habilitar la Wiki (3 Pasos)

### Paso 1: Ve a la Configuración de tu Repositorio

1. Abre tu navegador
2. Ve a: https://github.com/davidmonterocrespo24/DaveAgent
3. Haz clic en **Settings** (Configuración) - es la pestaña con el ícono de engranaje ⚙️

### Paso 2: Habilita la Wiki

1. En el menú lateral izquierdo, busca la sección **Features**
2. Marca el checkbox ✅ de **Wikis**
3. La página se recargará automáticamente

### Paso 3: Crea la Primera Página (Importante)

GitHub requiere que crees al menos una página antes de que el repositorio wiki exista:

1. Ve a la pestaña **Wiki** que ahora aparece en tu repositorio
2. Haz clic en **Create the first page**
3. En el campo de título escribe: `Home`
4. En el contenido, copia cualquier texto temporal (ej: "Wiki en construcción")
5. Haz clic en **Save Page**

### Paso 4: Ejecuta el Script Nuevamente

Ahora sí puedes ejecutar:

```bash
python upload_wiki.py
```

El script automáticamente:
- Clonará el repositorio wiki (que ahora existe)
- Copiará todos los archivos .md traducidos
- Sobrescribirá la página Home temporal con la versión completa
- Agregará todas las demás páginas
- Hará commit y push

---

## 📝 Alternativa: Subir Manualmente (Opción Web)

Si prefieres no usar el script, puedes subir las páginas manualmente:

### Para cada archivo .md en `wiki/`:

1. Ve a https://github.com/davidmonterocrespo24/DaveAgent/wiki
2. Haz clic en **New Page**
3. Título: usa el nombre del archivo sin .md (ej: `Installation`, `Quick-Start`)
4. Contenido: copia el contenido del archivo correspondiente
5. Haz clic en **Save Page**

### Orden recomendado:
1. Home (primero, sobrescribe la temporal)
2. Installation
3. Quick-Start
4. Architecture
5. Tools-and-Features
6. Configuration
7. Troubleshooting

**Nota**: NO subas README.md como página wiki - ese es solo para instrucciones.

---

## 🔗 URLs Importantes

- **Tu Repositorio**: https://github.com/davidmonterocrespo24/DaveAgent
- **Configuración**: https://github.com/davidmonterocrespo24/DaveAgent/settings
- **Wiki** (después de habilitar): https://github.com/davidmonterocrespo24/DaveAgent/wiki

---

## ❓ ¿Necesitas Ayuda?

Si tienes problemas para habilitar la wiki:
- Verifica que eres el propietario del repositorio
- Asegúrate de tener permisos de administrador
- El repositorio debe ser público o tener un plan que permita wikis en repos privados

---

## ✅ Checklist

- [ ] Ir a Settings del repositorio
- [ ] Habilitar Wikis en Features
- [ ] Crear primera página "Home" temporal
- [ ] Ejecutar `python upload_wiki.py`
- [ ] Verificar en https://github.com/davidmonterocrespo24/DaveAgent/wiki

---

**Última actualización**: 2024-12-08
