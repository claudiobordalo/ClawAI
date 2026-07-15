def function_no_hints(a, b):
    return a + b

def function_partial_hints(a: int, b: str) -> None:
    pass

def function_missing_return(a: int, b: int):
    return a + b

def complex_comprehension(data):
    # Alta complexidade via list comprehension (deve ser capturado pelo novo visitor)
    return [x for x in data if x > 0 for y in range(10) if x % y == 0]
