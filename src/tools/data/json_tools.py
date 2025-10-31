"""
Herramientas para trabajar con archivos JSON - Formato AutoGen
"""
import json
import logging
from typing import Dict, List, Any, Union


async def read_json(filepath: str, encoding: str = 'utf-8') -> Union[Dict[str, Any], List[Any]]:
    """
    Lee un archivo JSON y retorna su contenido.

    Args:
        filepath: Ruta al archivo JSON
        encoding: Codificación del archivo (default: utf-8)

    Returns:
        Dict o List: Contenido del archivo JSON
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)
        return data
    except Exception as e:
        error_msg = f"Error leyendo archivo JSON {filepath}: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}


async def write_json(
    filepath: str,
    data: Union[Dict[str, Any], List[Any]],
    encoding: str = 'utf-8',
    indent: int = 2,
    ensure_ascii: bool = False
) -> str:
    """
    Escribe datos en un archivo JSON.

    Args:
        filepath: Ruta del archivo de salida
        data: Datos a escribir (dict o list)
        encoding: Codificación del archivo (default: utf-8)
        indent: Espacios para indentación (default: 2)
        ensure_ascii: Escapar caracteres no-ASCII (default: False)

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(
                data,
                f,
                indent=indent,
                ensure_ascii=ensure_ascii
            )
        return f"✓ Archivo JSON guardado exitosamente en {filepath}"
    except Exception as e:
        error_msg = f"Error escribiendo archivo JSON {filepath}: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def merge_json_files(
    file1: str,
    file2: str,
    output_file: str,
    overwrite_duplicates: bool = True
) -> str:
    """
    Fusiona dos archivos JSON.

    Args:
        file1: Primera archivo JSON
        file2: Segundo archivo JSON
        output_file: Archivo de salida
        overwrite_duplicates: Sobrescribir claves duplicadas con valores de file2

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        # Leer ambos archivos
        data1 = await read_json(file1)
        data2 = await read_json(file2)

        if isinstance(data1, dict) and "error" in data1:
            return str(data1["error"])
        if isinstance(data2, dict) and "error" in data2:
            return str(data2["error"])

        # Fusionar
        if isinstance(data1, dict) and isinstance(data2, dict):
            if overwrite_duplicates:
                result = {**data1, **data2}
            else:
                result = data1.copy()
                for key, value in data2.items():
                    if key not in result:
                        result[key] = value
        elif isinstance(data1, list) and isinstance(data2, list):
            result = data1 + data2
        else:
            return f"ERROR: No se pueden fusionar tipos incompatibles: {type(data1).__name__} y {type(data2).__name__}"

        # Escribir resultado
        return await write_json(output_file, result)

    except Exception as e:
        error_msg = f"Error fusionando archivos JSON: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def validate_json(filepath: str) -> str:
    """
    Valida que un archivo tenga formato JSON válido.

    Args:
        filepath: Ruta al archivo JSON

    Returns:
        str: Mensaje indicando si es válido o no
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return f"✓ {filepath} es un JSON válido"
    except json.JSONDecodeError as e:
        return f"ERROR: JSON inválido en {filepath}: {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"


async def format_json(filepath: str, indent: int = 2) -> str:
    """
    Formatea un archivo JSON con indentación consistente.

    Args:
        filepath: Ruta al archivo JSON
        indent: Espacios para indentación

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        # Leer archivo
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Reescribir con formato
        return await write_json(filepath, data, indent=indent)

    except Exception as e:
        error_msg = f"Error formateando JSON: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def json_get_value(filepath: str, key_path: str) -> str:
    """
    Obtiene un valor de un archivo JSON usando una ruta de claves.

    Args:
        filepath: Ruta al archivo JSON
        key_path: Ruta de claves separadas por punto (ej: "user.name")

    Returns:
        str: Valor encontrado o mensaje de error
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Navegar por las claves
        keys = key_path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    return f"ERROR: Clave '{key}' no encontrada"
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return f"ERROR: Índice '{key}' inválido o fuera de rango"
            else:
                return f"ERROR: No se puede navegar en tipo {type(current).__name__}"

        return f"Valor en '{key_path}': {json.dumps(current, indent=2, ensure_ascii=False)}"

    except Exception as e:
        return f"ERROR: {str(e)}"


async def json_set_value(filepath: str, key_path: str, value: str) -> str:
    """
    Establece un valor en un archivo JSON usando una ruta de claves.

    Args:
        filepath: Ruta al archivo JSON
        key_path: Ruta de claves separadas por punto (ej: "user.name")
        value: Valor a establecer (como string JSON)

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Parsear el valor
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            # Si no es JSON válido, usar como string
            parsed_value = value

        # Navegar y establecer valor
        keys = key_path.split('.')
        current = data

        for key in keys[:-1]:
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            else:
                return f"ERROR: No se puede navegar en tipo {type(current).__name__}"

        # Establecer el valor final
        last_key = keys[-1]
        if isinstance(current, dict):
            current[last_key] = parsed_value
        else:
            return f"ERROR: No se puede establecer valor en tipo {type(current).__name__}"

        # Guardar cambios
        return await write_json(filepath, data)

    except Exception as e:
        return f"ERROR: {str(e)}"


async def json_to_text(filepath: str, pretty: bool = True) -> str:
    """
    Convierte un archivo JSON a texto legible.

    Args:
        filepath: Ruta al archivo JSON
        pretty: Si True, formatea con indentación

    Returns:
        str: Contenido JSON como texto
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        return f"ERROR: {str(e)}"
