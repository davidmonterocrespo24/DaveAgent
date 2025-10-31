"""
Herramientas para trabajar con archivos CSV - Formato AutoGen
"""
import logging
from typing import List, Dict, Any
from importlib import util


def _check_pandas():
    """Verifica si pandas está instalado"""
    if util.find_spec('pandas') is None:
        raise ImportError("pandas package no disponible. Instalar con: pip install pandas")
    import pandas as pd
    return pd


async def read_csv(
    filepath: str,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    max_rows: int = None
) -> str:
    """
    Lee un archivo CSV y retorna su contenido.

    Args:
        filepath: Ruta al archivo CSV
        delimiter: Delimitador de columnas (default: ',')
        encoding: Codificación del archivo (default: utf-8)
        max_rows: Número máximo de filas a leer (None = todas)

    Returns:
        str: Contenido del CSV en formato legible
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            nrows=max_rows
        )

        output = f"CSV: {filepath}\n"
        output += f"Filas: {len(df)}, Columnas: {len(df.columns)}\n\n"
        output += f"Columnas: {', '.join(df.columns.tolist())}\n\n"
        output += "Primeras filas:\n"
        output += df.head(10).to_string()

        if len(df) > 10:
            output += f"\n\n... (mostrando 10 de {len(df)} filas)"

        return output

    except Exception as e:
        error_msg = f"Error leyendo CSV {filepath}: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def write_csv(
    filepath: str,
    data: str,
    delimiter: str = ',',
    mode: str = 'w',
    encoding: str = 'utf-8'
) -> str:
    """
    Escribe datos en un archivo CSV.

    Args:
        filepath: Ruta del archivo de salida
        data: Datos en formato CSV (string con delimitadores)
        delimiter: Delimitador de columnas (default: ',')
        mode: Modo de escritura ('w' = sobrescribir, 'a' = agregar)
        encoding: Codificación del archivo (default: utf-8)

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        # Escribir directamente el string como CSV
        with open(filepath, mode, encoding=encoding, newline='') as f:
            f.write(data)
            if not data.endswith('\n'):
                f.write('\n')

        return f"✓ Datos escritos en {filepath}"

    except Exception as e:
        error_msg = f"Error escribiendo CSV {filepath}: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def csv_info(filepath: str, delimiter: str = ',', encoding: str = 'utf-8') -> str:
    """
    Obtiene información estadística sobre un archivo CSV.

    Args:
        filepath: Ruta al archivo CSV
        delimiter: Delimitador de columnas
        encoding: Codificación del archivo

    Returns:
        str: Información estadística del CSV
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)

        output = f"=== Información de {filepath} ===\n\n"
        output += f"Dimensiones: {len(df)} filas x {len(df.columns)} columnas\n\n"

        output += "Columnas y tipos:\n"
        for col in df.columns:
            output += f"  - {col}: {df[col].dtype}\n"

        output += f"\nValores nulos:\n"
        nulls = df.isnull().sum()
        if nulls.sum() == 0:
            output += "  No hay valores nulos\n"
        else:
            for col in nulls[nulls > 0].index:
                output += f"  - {col}: {nulls[col]} nulos\n"

        output += "\nEstadísticas numéricas:\n"
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            output += numeric_df.describe().to_string()
        else:
            output += "  No hay columnas numéricas\n"

        return output

    except Exception as e:
        error_msg = f"Error obteniendo info de CSV {filepath}: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def filter_csv(
    filepath: str,
    column: str,
    value: str,
    output_file: str = None,
    delimiter: str = ','
) -> str:
    """
    Filtra un CSV por el valor de una columna.

    Args:
        filepath: Ruta al archivo CSV
        column: Nombre de la columna a filtrar
        value: Valor a buscar
        output_file: Archivo de salida (None = retornar como texto)
        delimiter: Delimitador de columnas

    Returns:
        str: Resultado filtrado o mensaje de éxito
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath, delimiter=delimiter)

        if column not in df.columns:
            return f"ERROR: Columna '{column}' no existe. Columnas disponibles: {', '.join(df.columns)}"

        # Filtrar
        filtered_df = df[df[column].astype(str).str.contains(value, case=False, na=False)]

        if len(filtered_df) == 0:
            return f"No se encontraron filas con '{value}' en columna '{column}'"

        if output_file:
            filtered_df.to_csv(output_file, index=False, sep=delimiter)
            return f"✓ {len(filtered_df)} filas filtradas guardadas en {output_file}"
        else:
            output = f"Filtrado: {len(filtered_df)} filas con '{value}' en '{column}':\n\n"
            output += filtered_df.to_string()
            return output

    except Exception as e:
        error_msg = f"Error filtrando CSV: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def merge_csv_files(
    file1: str,
    file2: str,
    output_file: str,
    on_column: str = None,
    how: str = 'inner'
) -> str:
    """
    Fusiona dos archivos CSV.

    Args:
        file1: Primer archivo CSV
        file2: Segundo archivo CSV
        output_file: Archivo de salida
        on_column: Columna para hacer merge (None = concatenar)
        how: Tipo de merge ('inner', 'outer', 'left', 'right')

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        pd = _check_pandas()

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        if on_column:
            # Merge por columna
            if on_column not in df1.columns:
                return f"ERROR: Columna '{on_column}' no existe en {file1}"
            if on_column not in df2.columns:
                return f"ERROR: Columna '{on_column}' no existe en {file2}"

            result = pd.merge(df1, df2, on=on_column, how=how)
            operation = f"merge por '{on_column}' (tipo: {how})"
        else:
            # Concatenar verticalmente
            result = pd.concat([df1, df2], ignore_index=True)
            operation = "concatenación"

        result.to_csv(output_file, index=False)

        return f"✓ Archivos fusionados ({operation})\n  Resultado: {len(result)} filas x {len(result.columns)} columnas\n  Guardado en: {output_file}"

    except Exception as e:
        error_msg = f"Error fusionando CSVs: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def csv_to_json(
    csv_file: str,
    json_file: str,
    orient: str = 'records'
) -> str:
    """
    Convierte un archivo CSV a JSON.

    Args:
        csv_file: Archivo CSV de entrada
        json_file: Archivo JSON de salida
        orient: Orientación del JSON ('records', 'index', 'columns', 'values')

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(csv_file)
        df.to_json(json_file, orient=orient, indent=2)

        return f"✓ CSV convertido a JSON\n  {len(df)} filas exportadas a {json_file}"

    except Exception as e:
        error_msg = f"Error convirtiendo CSV a JSON: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def sort_csv(
    filepath: str,
    column: str,
    output_file: str = None,
    ascending: bool = True
) -> str:
    """
    Ordena un archivo CSV por una columna.

    Args:
        filepath: Archivo CSV
        column: Columna por la que ordenar
        output_file: Archivo de salida (None = sobrescribir original)
        ascending: True para ascendente, False para descendente

    Returns:
        str: Mensaje de éxito o error
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath)

        if column not in df.columns:
            return f"ERROR: Columna '{column}' no existe. Columnas: {', '.join(df.columns)}"

        df_sorted = df.sort_values(by=column, ascending=ascending)

        output = output_file or filepath
        df_sorted.to_csv(output, index=False)

        direction = "ascendente" if ascending else "descendente"
        return f"✓ CSV ordenado por '{column}' ({direction})\n  Guardado en: {output}"

    except Exception as e:
        error_msg = f"Error ordenando CSV: {str(e)}"
        logging.error(error_msg)
        return error_msg
