@echo off
echo ========================================================================
echo Instalando herramientas necesarias para publicar en PyPI
echo ========================================================================
echo.

echo [1/2] Instalando 'build' (para construir paquetes)...
pip install --upgrade build
echo.

echo [2/2] Instalando 'twine' (para subir a PyPI)...
pip install --upgrade twine
echo.

echo ========================================================================
echo Instalacion completada
echo ========================================================================
echo.
echo Ahora puedes publicar CodeAgent usando:
echo   python publish.py test    - Para publicar en TestPyPI (pruebas)
echo   python publish.py prod    - Para publicar en PyPI (produccion)
echo.
pause
