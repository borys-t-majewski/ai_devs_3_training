def print_type_structure(obj):
    """
    Returns a string representation of a nested object's type structure.
    Examples:
        {'a': {'b': 1}} -> dict[str, dict[str, int]]
        [{'a': 1}, {'b': 2}] -> list[dict[str, int]]
    """
    if isinstance(obj, dict):
        if not obj:
            return 'dict'
        # Get a sample key-value pair
        key, value = next(iter(obj.items()))
        return f'dict[{print_type_structure(key)}, {print_type_structure(value)}]'
    elif isinstance(obj, (list, tuple, set)):
        if not obj:
            return type(obj).__name__
        # Get the type of the first element
        return f'{type(obj).__name__}[{print_type_structure(obj[0])}]'
    else:
        return type(obj).__name__

if __name__ == "__main__":
    
    # Example usage
    test_data = {
        'A': {'B': 3},
        'C': {'D': [1, 2, 3]},
        'E': [{'F': 'text', 'G':124.44}]
    }

    print(print_type_structure(test_data))  # dict[str, dict[str, int]]