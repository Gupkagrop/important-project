"""Модульные тесты для разреженной матрицы SparseMatrix."""

import pytest

from pocket_toolkit.structures.sparse_matrix import SparseMatrix


def test_sparse_matrix_init_valid() -> None:
    """Проверка корректной инициализации разреженной матрицы."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=3, cols=4, default=0)
    assert matrix.rows == 3
    assert matrix.cols == 4
    assert matrix.shape == (3, 4)
    assert matrix.default == 0
    assert matrix.nnz == 0
    assert len(matrix) == 0
    assert matrix.density == 0.0
    assert matrix.sparsity == 1.0
    assert matrix.is_square is False


def test_sparse_matrix_init_invalid() -> None:
    """Проверка возбуждения исключений при некорректных размерах матрицы."""
    with pytest.raises(ValueError, match="Размеры матрицы.*должны быть строго больше нуля"):
        SparseMatrix(rows=0, cols=5)

    with pytest.raises(ValueError, match="Размеры матрицы.*должны быть строго больше нуля"):
        SparseMatrix(rows=5, cols=-1)


def test_sparse_matrix_from_dense() -> None:
    """Проверка создания разреженной матрицы из плотного списка."""
    dense: list[list[int]] = [
        [0, 5, 0],
        [0, 0, 8],
        [3, 0, 0],
    ]
    matrix: SparseMatrix[int] = SparseMatrix.from_dense(dense, default=0)
    assert matrix.shape == (3, 3)
    assert matrix.nnz == 3
    assert matrix[0, 1] == 5
    assert matrix[1, 2] == 8
    assert matrix[2, 0] == 3
    assert matrix[0, 0] == 0
    assert matrix.density == pytest.approx(3 / 9)
    assert matrix.sparsity == pytest.approx(6 / 9)
    assert matrix.is_square is True


def test_sparse_matrix_from_dense_invalid() -> None:
    """Проверка валидации данных при создании из плотного списка."""
    with pytest.raises(ValueError, match="Плотная матрица не может быть пустой"):
        SparseMatrix.from_dense([])

    with pytest.raises(ValueError, match="Строки плотной матрицы не могут быть пустыми"):
        SparseMatrix.from_dense([[]])

    with pytest.raises(ValueError, match="Все строки плотной матрицы должны иметь одинаковую длину"):
        SparseMatrix.from_dense([[1, 2], [3]])


def test_sparse_matrix_from_dok() -> None:
    """Проверка создания матрицы из словаря координат DOK."""
    dok: dict[tuple[int, int], float] = {
        (0, 0): 1.5,
        (1, 2): 3.0,
        (2, 1): 0.0,  # Совпадает с default, не должно сохраниться в nnz
    }
    matrix: SparseMatrix[float] = SparseMatrix.from_dok(dok, rows=3, cols=3, default=0.0)
    assert matrix.nnz == 2
    assert matrix[0, 0] == 1.5
    assert matrix[1, 2] == 3.0
    assert matrix[2, 1] == 0.0


def test_sparse_matrix_from_dok_out_of_bounds() -> None:
    """Проверка ошибки выхода за границы при импорте из DOK."""
    dok: dict[tuple[int, int], int] = {(3, 0): 10}
    with pytest.raises(IndexError, match="выходит за границы"):
        SparseMatrix.from_dok(dok, rows=3, cols=3)


def test_sparse_matrix_identity() -> None:
    """Проверка создания единичной матрицы."""
    ident: SparseMatrix[int] = SparseMatrix.identity(size=3)
    assert ident.shape == (3, 3)
    assert ident.nnz == 3
    assert ident[0, 0] == 1
    assert ident[1, 1] == 1
    assert ident[2, 2] == 1
    assert ident[0, 1] == 0
    assert ident.is_symmetric() is True

    with pytest.raises(ValueError, match="Размер единичной матрицы должен быть больше нуля"):
        SparseMatrix.identity(size=0)


def test_sparse_matrix_diag() -> None:
    """Проверка создания диагональной матрицы."""
    diag_matrix: SparseMatrix[int] = SparseMatrix.diag([10, 20, 30])
    assert diag_matrix.shape == (3, 3)
    assert diag_matrix.nnz == 3
    assert diag_matrix[0, 0] == 10
    assert diag_matrix[1, 1] == 20
    assert diag_matrix[2, 2] == 30
    assert diag_matrix[1, 0] == 0

    with pytest.raises(ValueError, match="Диагональ матрицы не может быть пустой"):
        SparseMatrix.diag([])


def test_sparse_matrix_indexing_and_mutation() -> None:
    """Проверка доступа по индексу, отрицательных индексов и мутации."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=3, cols=3, default=0)
    matrix[0, 1] = 42
    assert matrix[0, 1] == 42
    assert matrix.nnz == 1
    assert (0, 1) in matrix

    # Проверка отрицательного индексирования
    matrix[-1, -1] = 99
    assert matrix[2, 2] == 99
    assert matrix[-1, -1] == 99
    assert matrix.nnz == 2

    # Запись дефолтного значения удаляет элемент
    matrix[0, 1] = 0
    assert matrix[0, 1] == 0
    assert matrix.nnz == 1
    assert (0, 1) not in matrix

    # Удаление через del
    del matrix[2, 2]
    assert matrix[2, 2] == 0
    assert matrix.nnz == 0

    # Проверка ошибок некорректного типа ключа
    with pytest.raises(TypeError, match="Индекс матрицы должен быть кортежем"):
        _ = matrix[1]  # type: ignore[index]

    with pytest.raises(TypeError, match="Индекс матрицы должен быть кортежем"):
        _ = matrix[(1, 2, 3)]  # type: ignore[index]


def test_sparse_matrix_index_error() -> None:
    """Проверка выброса IndexError при выходе за пределы матрицы."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    with pytest.raises(IndexError, match="выходит за границы"):
        _ = matrix[2, 0]

    with pytest.raises(IndexError, match="выходит за границы"):
        matrix[0, 5] = 10

    with pytest.raises(IndexError, match="выходит за границы"):
        del matrix[-3, 0]


def test_sparse_matrix_get_safe() -> None:
    """Проверка безопасного метода get."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=2, cols=2, default=0)
    matrix[0, 1] = 77

    assert matrix.get(0, 1) == 77
    assert matrix.get(0, 0) == 0
    assert matrix.get(5, 5) is None
    assert matrix.get(5, 5, default=-1) == -1
    assert matrix.get(-1, -1) == 0


def test_sparse_matrix_symmetry_and_trace() -> None:
    """Проверка определения симметричности и вычисления следа матрицы."""
    sym: SparseMatrix[int] = SparseMatrix.from_dense([
        [1, 2, 3],
        [2, 4, 5],
        [3, 5, 6],
    ])
    assert sym.is_symmetric() is True
    assert sym.trace() == 1 + 4 + 6

    non_sym: SparseMatrix[int] = SparseMatrix.from_dense([
        [1, 2],
        [3, 4],
    ])
    assert non_sym.is_symmetric() is False
    assert non_sym.trace() == 5

    rect: SparseMatrix[int] = SparseMatrix(rows=2, cols=3)
    assert rect.is_symmetric() is False
    with pytest.raises(ValueError, match="След.*определен только для квадратных"):
        rect.trace()


def test_sparse_matrix_transpose() -> None:
    """Проверка транспонирования матрицы и свойства T."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=2, cols=3)
    matrix[0, 1] = 5
    matrix[1, 2] = 9

    transposed: SparseMatrix[int] = matrix.transpose()
    assert transposed.shape == (3, 2)
    assert transposed[1, 0] == 5
    assert transposed[2, 1] == 9
    assert transposed.nnz == 2

    # Проверка свойства T
    assert matrix.T.shape == (3, 2)
    assert matrix.T[1, 0] == 5

    # Двойное транспонирование возвращает исходную структуру
    assert matrix.T.T == matrix


def test_sparse_matrix_submatrix() -> None:
    """Проверка извлечения прямоугольной подматрицы."""
    dense: list[list[int]] = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
    ]
    matrix: SparseMatrix[int] = SparseMatrix.from_dense(dense)
    sub: SparseMatrix[int] = matrix.submatrix(row_start=1, row_end=3, col_start=1, col_end=3)

    assert sub.shape == (2, 2)
    assert sub[0, 0] == 6
    assert sub[0, 1] == 7
    assert sub[1, 0] == 10
    assert sub[1, 1] == 11

    with pytest.raises(IndexError, match="Некорректный диапазон"):
        matrix.submatrix(row_start=2, row_end=1, col_start=0, col_end=2)

    with pytest.raises(IndexError, match="Некорректный диапазон"):
        matrix.submatrix(row_start=0, row_end=2, col_start=0, col_end=5)


def test_sparse_matrix_get_row_and_col() -> None:
    """Проверка извлечения строк и столбцов в плотном и разреженном виде."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=3, cols=3)
    matrix[1, 0] = 10
    matrix[1, 2] = 30

    assert matrix.get_row(1) == [10, 0, 30]
    assert matrix.get_col(2) == [0, 30, 0]
    assert matrix.get_row_sparse(1) == {0: 10, 2: 30}
    assert matrix.get_col_sparse(2) == {1: 30}
    assert matrix.get_row_sparse(0) == {}


def test_sparse_matrix_add_and_sub() -> None:
    """Проверка сложения и вычитания разреженных матриц."""
    a: SparseMatrix[int] = SparseMatrix.from_dense([
        [1, 0],
        [0, 2],
    ])
    b: SparseMatrix[int] = SparseMatrix.from_dense([
        [0, 3],
        [4, 0],
    ])

    c: SparseMatrix[int] = a + b
    assert c.to_dense() == [
        [1, 3],
        [4, 2],
    ]
    assert c.nnz == 4

    diff: SparseMatrix[int] = c - b
    assert diff == a

    zero_mat: SparseMatrix[int] = a - a
    assert zero_mat.nnz == 0
    assert zero_mat.to_dense() == [[0, 0], [0, 0]]


def test_sparse_matrix_add_sub_invalid_dimensions() -> None:
    """Проверка сложения и вычитания матриц несогласованных размеров."""
    a: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    b: SparseMatrix[int] = SparseMatrix(rows=2, cols=3)

    with pytest.raises(ValueError, match="Невозможно сложить матрицы разных размеров"):
        _ = a + b

    with pytest.raises(ValueError, match="Невозможно вычесть матрицы разных размеров"):
        _ = a - b

    with pytest.raises(TypeError):
        _ = a + "not_a_matrix"  # type: ignore[operator]

    with pytest.raises(TypeError):
        _ = a - "not_a_matrix"  # type: ignore[operator]


def test_sparse_matrix_scalar_multiplication_and_negation() -> None:
    """Проверка умножения на скаляр и поэлементного отрицания."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    matrix[0, 0] = 5
    matrix[1, 1] = -3

    scaled: SparseMatrix[int] = matrix * 2
    assert scaled[0, 0] == 10
    assert scaled[1, 1] == -6

    rscaled: SparseMatrix[int] = 3 * matrix
    assert rscaled[0, 0] == 15
    assert rscaled[1, 1] == -9

    zero_scaled: SparseMatrix[int] = matrix * 0
    assert zero_scaled.nnz == 0

    neg: SparseMatrix[int] = -matrix
    assert neg[0, 0] == -5
    assert neg[1, 1] == 3


def test_sparse_matrix_matmul() -> None:
    """Проверка матричного умножения A @ B."""
    a: SparseMatrix[int] = SparseMatrix.from_dense([
        [1, 2, 0],
        [0, 3, 4],
    ])
    b: SparseMatrix[int] = SparseMatrix.from_dense([
        [1, 0],
        [2, 3],
        [0, 4],
    ])

    res: SparseMatrix[int] = a @ b
    assert res.shape == (2, 2)
    # [1*1 + 2*2 + 0,  1*0 + 2*3 + 0] = [5, 6]
    # [0 + 3*2 + 0,    0 + 3*3 + 4*4] = [6, 25]
    assert res.to_dense() == [
        [5, 6],
        [6, 25],
    ]

    # Умножение на единичную матрицу
    ident: SparseMatrix[int] = SparseMatrix.identity(2)
    assert res @ ident == res


def test_sparse_matrix_matmul_invalid() -> None:
    """Проверка возбуждения ошибок при некорректных размерах матричного умножения."""
    a: SparseMatrix[int] = SparseMatrix(rows=2, cols=3)
    b: SparseMatrix[int] = SparseMatrix(rows=2, cols=3)

    with pytest.raises(ValueError, match="Несогласованные размеры матриц"):
        _ = a @ b

    with pytest.raises(TypeError):
        _ = a @ 42  # type: ignore[operator]


def test_sparse_matrix_conversions_and_iterations() -> None:
    """Проверка методов преобразования, итерации и копирования."""
    matrix: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    matrix[0, 1] = 10
    matrix[1, 0] = 20

    assert matrix.to_dok() == {(0, 1): 10, (1, 0): 20}
    assert matrix.to_dense() == [[0, 10], [20, 0]]

    coords: list[tuple[int, int]] = list(matrix.keys())
    assert coords == [(0, 1), (1, 0)]

    vals: list[int] = list(matrix.values())
    assert vals == [10, 20]

    items: list[tuple[tuple[int, int], int]] = list(matrix.items())
    assert items == [((0, 1), 10), ((1, 0), 20)]
    assert list(matrix) == items

    # Копирование
    copied: SparseMatrix[int] = matrix.copy()
    assert copied == matrix
    copied[0, 0] = 99
    assert matrix[0, 0] == 0

    # Очистка
    copied.clear()
    assert copied.nnz == 0
    assert len(copied) == 0

    # Строковые представления
    assert repr(matrix) == "SparseMatrix(rows=2, cols=2, nnz=2, default=0)"
    assert "<SparseMatrix 2x2, 2 non-default entries" in str(matrix)


def test_sparse_matrix_equality() -> None:
    """Проверка оператора равенства для матриц."""
    a: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    b: SparseMatrix[int] = SparseMatrix(rows=2, cols=2)
    assert a == b

    a[0, 0] = 5
    assert a != b

    b[0, 0] = 5
    assert a == b

    diff_shape: SparseMatrix[int] = SparseMatrix(rows=3, cols=2)
    assert a != diff_shape

    assert a != "not a matrix"
