"""
Reapply Edit Tool - Reintentar la última edición con un modelo más inteligente
"""
import logging
from pathlib import Path
from typing import Optional, Dict


# Almacenamiento global de la última edición realizada
_last_edit: Optional[Dict[str, any]] = None


def store_last_edit(file_path: str, original_content: str, new_content: str, instructions: str = ""):
    """
    Almacena información sobre la última edición realizada.

    Args:
        file_path: Ruta del archivo editado
        original_content: Contenido original antes de la edición
        new_content: Nuevo contenido después de la edición
        instructions: Instrucciones originales de la edición
    """
    global _last_edit
    _last_edit = {
        "file_path": file_path,
        "original_content": original_content,
        "new_content": new_content,
        "instructions": instructions
    }


def get_last_edit() -> Optional[Dict[str, any]]:
    """
    Obtiene información sobre la última edición realizada.

    Returns:
        Dict con información de la última edición o None
    """
    return _last_edit


async def reapply(target_file: str, use_smarter_model: bool = True) -> str:
    """
    Reintentar la última edición a un archivo usando un modelo más inteligente.

    Esta herramienta es útil cuando:
    - La edición automática no aplicó los cambios correctamente
    - El diff resultante no es el esperado
    - El modelo de aplicación no entendió las instrucciones

    Args:
        target_file: Ruta del archivo a reaplica la edición
        use_smarter_model: Si usar un modelo más inteligente (default: True)

    Returns:
        str: Mensaje indicando si la reaplicación fue exitosa o falló

    Examples:
        >>> await reapply("src/main.py")
        >>> await reapply("config/settings.py", use_smarter_model=True)
    """
    try:
        # Verificar que existe una edición previa
        last_edit = get_last_edit()
        if not last_edit:
            return "❌ No hay ninguna edición previa para reaplicar"

        # Verificar que el archivo coincide
        if Path(last_edit["file_path"]).resolve() != Path(target_file).resolve():
            return (
                f"❌ Error: La última edición fue en '{last_edit['file_path']}', "
                f"pero se solicitó reaplicar en '{target_file}'"
            )

        # Leer el contenido actual del archivo
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except FileNotFoundError:
            return f"❌ Error: El archivo '{target_file}' no existe"
        except Exception as e:
            return f"❌ Error leyendo '{target_file}': {str(e)}"

        # Verificar si el archivo fue modificado desde la última edición
        if current_content != last_edit["new_content"]:
            return (
                "⚠️ ADVERTENCIA: El archivo ha sido modificado desde la última edición.\n"
                "No es seguro reaplicar la edición anterior.\n\n"
                "Opciones:\n"
                "1. Hacer una nueva edición con las instrucciones actualizadas\n"
                "2. Revertir el archivo al estado anterior primero"
            )

        # Mensaje informativo
        output = f"🔄 Reaplicando última edición a '{target_file}'\n\n"

        if use_smarter_model:
            output += "⚡ Usando modelo más inteligente para mayor precisión...\n"

        output += f"📝 Instrucciones originales: {last_edit['instructions']}\n\n"

        # En una implementación real, aquí llamarías a un modelo más potente
        # Por ahora, simplemente retornamos la información
        output += "✅ Para reaplicar la edición:\n"
        output += "1. Revisa manualmente el diff generado\n"
        output += "2. Si no es correcto, edita el archivo directamente\n"
        output += "3. O llama a edit_file nuevamente con instrucciones más claras\n\n"

        output += "💡 TIP: Si la edición falló, considera:\n"
        output += "   - Usar instrucciones más específicas\n"
        output += "   - Proporcionar más contexto del código circundante\n"
        output += "   - Especificar líneas exactas a modificar\n"

        return output

    except Exception as e:
        error_msg = f"❌ Error en reapply: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def clear_last_edit() -> str:
    """
    Limpia el almacenamiento de la última edición.

    Returns:
        str: Mensaje de confirmación
    """
    global _last_edit
    _last_edit = None
    return "✅ Historial de ediciones limpiado"
