"""
Módulo para funciones de ordenamiento de arreglos
"""

def ordenar_arreglo(arr):
    """
    Ordena un arreglo de números enteros en orden ascendente
    
    Args:
        arr (list): Lista de números enteros a ordenar
        
    Returns:
        list: Lista ordenada en orden ascendente
        
    Examples:
        >>> ordenar_arreglo([3, 1, 4, 1, 5, 9, 2])
        [1, 1, 2, 3, 4, 5, 9]
        >>> ordenar_arreglo([5, 2, 8, 1, 9])
        [1, 2, 5, 8, 9]
    """
    # Usando el algoritmo de ordenamiento por inserción
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

def ordenar_arreglo_descendente(arr):
    """
    Ordena un arreglo de números enteros en orden descendente
    
    Args:
        arr (list): Lista de números enteros a ordenar
        
    Returns:
        list: Lista ordenada en orden descendente
        
    Examples:
        >>> ordenar_arreglo_descendente([3, 1, 4, 1, 5, 9, 2])
        [9, 5, 4, 3, 2, 1, 1]
        >>> ordenar_arreglo_descendente([5, 2, 8, 1, 9])
        [9, 8, 5, 2, 1]
    """
    # Usando el algoritmo de ordenamiento por inserción en orden descendente
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] < key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

def ordenar_arreglo_builtin(arr, descendente=False):
    """
    Ordena un arreglo usando la función sorted() de Python
    
    Args:
        arr (list): Lista de números enteros a ordenar
        descendente (bool): Si es True, ordena en orden descendente
        
    Returns:
        list: Lista ordenada
        
    Examples:
        >>> ordenar_arreglo_builtin([3, 1, 4, 1, 5, 9, 2])
        [1, 1, 2, 3, 4, 5, 9]
        >>> ordenar_arreglo_builtin([5, 2, 8, 1, 9], descendente=True)
        [9, 8, 5, 2, 1]
    """
    return sorted(arr, reverse=descendente)


if __name__ == "__main__":
    # Ejemplos de uso
    print("=== Pruebas de la función de ordenamiento ===")
    
    # Test 1: Ordenamiento ascendente
    test_arr1 = [3, 1, 4, 1, 5, 9, 2]
    print(f"Arreglo original: {test_arr1}")
    print(f"Ordenado ascendente: {ordenar_arreglo(test_arr1.copy())}")
    
    # Test 2: Ordenamiento descendente
    test_arr2 = [5, 2, 8, 1, 9]
    print(f"\nArreglo original: {test_arr2}")
    print(f"Ordenado descendente: {ordenar_arreglo_descendente(test_arr2.copy())}")
    
    # Test 3: Usando función built-in
    test_arr3 = [7, 3, 9, 2, 6]
    print(f"\nArreglo original: {test_arr3}")
    print(f"Built-in ascendente: {ordenar_arreglo_builtin(test_arr3.copy())}")
    print(f"Built-in descendente: {ordenar_arreglo_builtin(test_arr3.copy(), descendente=True)}")