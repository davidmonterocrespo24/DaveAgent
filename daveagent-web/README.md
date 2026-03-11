# DaveAgent Web Interface

Frontend web para DaveAgent - Terminal interactiva en el navegador usando React + TypeScript + xterm.js

## 🚀 Quick Start

### 1. Instalar Dependencias

```bash
npm install
```

### 2. Iniciar Servidor Backend

En una terminal aparte:

```bash
cd ..
daveagent --server
```

### 3. Iniciar Frontend

```bash
npm run dev
```

Abre tu navegador en: **http://localhost:5173**

## 📋 Requisitos

- Node.js 18+
- npm 9+
- Backend DaveAgent corriendo en `localhost:8000`

## 🎨 Features

- ✅ Terminal completa con xterm.js
- ✅ Soporte completo de colores ANSI
- ✅ Mismo look & feel que el CLI
- ✅ Historial de comandos (↑↓ arrows)
- ✅ Copy/paste support
- ✅ Links clickeables
- ✅ Reconexión automática
- ✅ Estado de conexión visual

## 🛠️ Comandos Disponibles

```bash
# Desarrollo (con hot-reload)
npm run dev

# Build para producción
npm run build

# Preview del build de producción
npm run preview

# Lint del código
npm run lint
```

## 📚 Documentación Completa

Ver el README completo con:
- Arquitectura detallada
- Configuración avanzada
- Troubleshooting
- Build para producción
- Variables de entorno

Ejecuta: `cat README_FULL.md` (después de crear el archivo)

## 🐛 Troubleshooting

**No se puede conectar al backend:**

```bash
# Verifica que el backend esté corriendo
daveagent --server

# Debería mostrar:
# 📡 WebSocket endpoint: ws://0.0.0.0:8000/ws/agent
```

**Puerto 5173 en uso:**

```bash
npm run dev -- --port 3000
```

## 📖 Referencias

- [Backend API](../src/api/README.md)
- [Migration Guide](../MIGRATION_PHASE1_SUMMARY.md)
- [xterm.js Docs](https://xtermjs.org/)
- [React Docs](https://react.dev/)

