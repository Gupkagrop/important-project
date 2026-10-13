"""Реализация разреженной матрицы (Sparse Matrix) на базе словаря координат (DOK).

Обеспечивает компактное хранение матриц с преобладанием нулевых или значений
по умолчанию, доступ к элементам за O(1), матричные вычисления (сложение,
вычитание, умножение на скаляр, матричное произведение и транспонирование),
а также операции преобразования между разреженным и плотным представлениями.
"""

from collections.abc import Iterator, Mapping, Sequence
from typing import Self


class SparseMatrix[T]:
    """Разреженная матрица на базе словаря координат (Dictionary of Keys, DOK).

    Хранит только элементы, отличные от значения по умолчанию (обычно 0).
    Координаты задаются парой целых чисел (row, col) с поддержкой отрицательных
    индексов в стиле стандартных последовательностей Python.
    """

    def __init__(self, rows: int, cols: int, default: T = 0) -> None:
        """Инициализирует разреженную матрицу заданного размера.

        :param rows: Количество строк матрицы (строго > 0).
        :param cols: Количество столбцов матрицы (строго > 0).
        :param default: Значение по умолчанию для неинициализированных ячеек.
        :raises ValueError: Если количество строк или столбцов меньше либо равно 0.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Размеры матрицы (rows и cols) должны быть строго больше нуля")

        self._rows: int = rows
        self._cols: int = cols
        self._default: T = default
        self._data: dict[tuple[int, int], T] = {}

    @property
    def rows(self) -> int:
        """Возвращает количество строк в матрице."""
        return self._rows

    @property
    def cols(self) -> int:
        """Возвращает количество столбцов в матрице."""
        return self._cols

    @property
    def shape(self) -> tuple[int, int]:
        """Возвращает размерность матрицы в виде кортежа (rows, cols)."""
        return self._rows, self._cols

    @property
    def default(self) -> T:
        """Возвращает значение по умолчанию для незаполненных ячеек."""
        return self._default

    @property
    def nnz(self) -> int:
        """Возвращает количество фактически сохраненных (ненулевых) элементов."""
        return len(self._data)

    @property
    def density(self) -> float:
        """Возвращает плотность матрицы (долю заполненных элементов)."""
        total_cells: int = self._rows * self._cols
        return self.nnz / total_cells

    @property
    def sparsity(self) -> float:
        """Возвращает разреженность матрицы (долю элементов со значением по умолчанию)."""
        return 1.0 - self.density

    @property
    def is_square(self) -> bool:
        """Проверяет, является ли матрица квадратной."""
        return self._rows == self._cols

    @property
    def T(self) -> Self:
        """Возвращает транспонированную матрицу (синоним метода transpose)."""
        return self.transpose()

    @classmethod
    def from_dense(cls, matrix: Sequence[Sequence[T]], default: T = 0) -> Self:
        """Создает разреженную матрицу из двумерной плотной последовательности.

        :param matrix: Плотная матрица (список строк).
        :param default: Значение по умолчанию для пустых ячеек.
        :return: Новый экземпляр SparseMatrix.
        :raises ValueError: Если матрица пуста или строки имеют разную длину.
        """
        if not matrix:
            raise ValueError("Плотная матрица не может быть пустой")

        num_rows: int = len(matrix)
        if not matrix[0]:
            raise ValueError("Строки плотной матрицы не могут быть пустыми")

        num_cols: int = len(matrix[0])
        instance: Self = cls(num_rows, num_cols, default=default)

        for r_idx, row in enumerate(matrix):
            if len(row) != num_cols:
                raise ValueError("Все строки плотной матрицы должны иметь одинаковую длину")
            for c_idx, val in enumerate(row):
                if val != default:
                    instance._data[(r_idx, c_idx)] = val

        return instance

    @classmethod
    def from_dok(
        cls,
        dok: Mapping[tuple[int, int], T],
        rows: int,
        cols: int,
        default: T = 0,
    ) -> Self:
        """Создает разреженную матрицу из словаря координат.

        :param dok: Словарь с координатами (r, c) и значениями.
        :param rows: Количество строк матрицы.
        :param cols: Количество столбцов матрицы.
        :param default: Значение по умолчанию.
        :return: Новый экземпляр SparseMatrix.
        :raises IndexError: Если координаты выходят за допустимые границы.
        """
        instance: Self = cls(rows, cols, default=default)
        for (r_coord, c_coord), val in dok.items():
            norm_r, norm_c = instance._validate_index(r_coord, c_coord)
            if val != default:
                instance._data[(norm_r, norm_c)] = val
        return instance

    @classmethod
    def identity(cls, size: int, one: T = 1, default: T = 0) -> Self:
        """Создает единичную разреженную матрицу заданного размера.

        :param size: Размер квадратной матрицы (число строк и столбцов).
        :param one: Значение на главной диагонали (по умолчанию 1).
        :param default: Значение вне диагонали (по умолчанию 0).
        :return: Единичная разреженная матрица.
        :raises ValueError: Если размер меньше либо равен 0.
        """
        if size <= 0:
            raise ValueError("Размер единичной матрицы должен быть больше нуля")

        instance: Self = cls(size, size, default=default)
        if one != default:
            for idx in range(size):
                instance._data[(idx, idx)] = one
        return instance

    @classmethod
    def diag(cls, diagonal: Sequence[T], default: T = 0) -> Self:
        """Создает диагональную разреженную матрицу из переданной последовательности.

        :param diagonal: Элементы главной диагонали.
        :param default: Значение вне диагонали.
        :return: Диагональная разреженная матрица.
        :raises ValueError: Если последовательность диагонали пуста.
        """
        if not diagonal:
            raise ValueError("Диагональ матрицы не может быть пустой")

        size: int = len(diagonal)
        instance: Self = cls(size, size, default=default)
        for idx, val in enumerate(diagonal):
            if val != default:
                instance._data[(idx, idx)] = val
        return instance

    def _validate_index(self, row: int, col: int) -> tuple[int, int]:
        """Проверяет и нормализует индексы строки и столбца.

        :param row: Индекс строки.
        :param col: Индекс столбцов.
        :return: Нормализованные индексы (row, col) в диапазоне [0, size).
        :raises IndexError: Если индекс выходит за границы матрицы.
        """
        norm_row: int = row + self._rows if row < 0 else row
        norm_col: int = col + self._cols if col < 0 else col

        if not (0 <= norm_row < self._rows and 0 <= norm_col < self._cols):
            raise IndexError(
                f"Индекс ({row}, {col}) выходит за границы матрицы формы {self.shape}"
            )
        return norm_row, norm_col

    def _check_key_tuple(self, key: tuple[int, int]) -> tuple[int, int]:
        """Проверяет тип ключа доступа к ячейке матрицы.

        :param key: Кортеж из двух целочисленных индексов (row, col).
        :return: Проверенный кортеж индексов.
        :raises TypeError: Если передан не двухэлементный кортеж.
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError("Индекс матрицы должен быть кортежем из двух элементов (row, col)")
        return key[0], key[1]

    def __getitem__(self, key: tuple[int, int]) -> T:
        """Возвращает значение элемента по координатам (row, col)."""
        raw_row, raw_col = self._check_key_tuple(key)
        norm_row, norm_col = self._validate_index(raw_row, raw_col)
        return self._data.get((norm_row, norm_col), self._default)

    def __setitem__(self, key: tuple[int, int], value: T) -> None:
        """Устанавливает значение элемента по координатам (row, col)."""
        raw_row, raw_col = self._check_key_tuple(key)
        norm_row, norm_col = self._validate_index(raw_row, raw_col)

        if value == self._default:
            self._data.pop((norm_row, norm_col), None)
            return

        self._data[(norm_row, norm_col)] = value

    def __delitem__(self, key: tuple[int, int]) -> None:
        """Сбрасывает элемент матрицы в значение по умолчанию."""
        raw_row, raw_col = self._check_key_tuple(key)
        norm_row, norm_col = self._validate_index(raw_row, raw_col)
        self._data.pop((norm_row, norm_col), None)

    def __contains__(self, key: tuple[int, int]) -> bool:
        """Проверяет наличие явно сохраненного (не дефолтного) значения по координатам."""
        raw_row, raw_col = self._check_key_tuple(key)
        norm_row, norm_col = self._validate_index(raw_row, raw_col)
        return (norm_row, norm_col) in self._data

    def get(self, row: int, col: int, default: T | None = None) -> T | None:
        """Безопасно возвращает элемент матрицы или значение fallback при выходе за границы.

        :param row: Индекс строки.
        :param col: Индекс столбца.
        :param default: Значение при выходе индексов за границы матрицы.
        :return: Значение ячейки матрицы либо fallback.
        """
        if not (-self._rows <= row < self._rows and -self._cols <= col < self._cols):
            return default

        norm_row: int = row + self._rows if row < 0 else row
        norm_col: int = col + self._cols if col < 0 else col
        return self._data.get((norm_row, norm_col), self._default)

    def is_symmetric(self) -> bool:
        """Проверяет, является ли матрица симметричной относительно главной диагонали."""
        if not self.is_square:
            return False

        for (r_coord, c_coord), val in self._data.items():
            if self._data.get((c_coord, r_coord), self._default) != val:
                return False
        return True

    def trace(self) -> T:
        """Вычисляет след матрицы (сумму элементов главной диагонали).

        :return: Сумма элементов на главной диагонали.
        :raises ValueError: Если матрица не является квадратной.
        """
        if not self.is_square:
            raise ValueError("След (trace) определен только для квадратных матриц")

        accum: T = self[0, 0]
        for idx in range(1, self._rows):
            accum = accum + self[idx, idx]
        return accum

    def transpose(self) -> Self:
        """Возвращает новую транспонированную матрицу."""
        transposed: Self = self.__class__(self._cols, self._rows, default=self._default)
        for (r_coord, c_coord), val in self._data.items():
            transposed._data[(c_coord, r_coord)] = val
        return transposed

    def submatrix(
        self,
        row_start: int,
        row_end: int,
        col_start: int,
        col_end: int,
    ) -> Self:
        """Извлекает прямоугольную подматрицу по заданным диапазонам индексов.

        :param row_start: Начальный индекс строки (включительно).
        :param row_end: Конечный индекс строки (исключительно).
        :param col_start: Начальный индекс столбца (включительно).
        :param col_end: Конечный индекс столбца (исключительно).
        :return: Новая разреженная подматрица.
        :raises IndexError: При выходе диапазонов за границы исходной матрицы.
        """
        if not (0 <= row_start < row_end <= self._rows):
            raise IndexError("Некорректный диапазон строк для подматрицы")
        if not (0 <= col_start < col_end <= self._cols):
            raise IndexError("Некорректный диапазон столбцов для подматрицы")

        sub: Self = self.__class__(
            row_end - row_start,
            col_end - col_start,
            default=self._default,
        )
        for (r_coord, c_coord), val in self._data.items():
            if row_start <= r_coord < row_end and col_start <= c_coord < col_end:
                sub._data[(r_coord - row_start, c_coord - col_start)] = val
        return sub

    def get_row(self, row: int) -> list[T]:
        """Возвращает полную плотную строку элементов матрицы.

        :param row: Индекс строки.
        :return: Список всех элементов указанной строки.
        """
        norm_r, _ = self._validate_index(row, 0)
        return [self._data.get((norm_r, c), self._default) for c in range(self._cols)]

    def get_col(self, col: int) -> list[T]:
        """Возвращает полный плотный столбец элементов матрицы.

        :param col: Индекс столбца.
        :return: Список всех элементов указанного столбца.
        """
        _, norm_c = self._validate_index(0, col)
        return [self._data.get((r, norm_c), self._default) for r in range(self._rows)]

    def get_row_sparse(self, row: int) -> dict[int, T]:
        """Возвращает словарь ненулевых элементов строки в формате {col: value}.

        :param row: Индекс строки.
        :return: Словарь индексов столбцов и их значений.
        """
        norm_r, _ = self._validate_index(row, 0)
        return {c: val for (r, c), val in self._data.items() if r == norm_r}

    def get_col_sparse(self, col: int) -> dict[int, T]:
        """Возвращает словарь ненулевых элементов столбца в формате {row: value}.

        :param col: Индекс столбца.
        :return: Словарь индексов строк и их значений.
        """
        _, norm_c = self._validate_index(0, col)
        return {r: val for (r, c), val in self._data.items() if c == norm_c}

    def __add__(self, other: Self) -> Self:
        """Складывает две разреженные матрицы одинакового размера."""
        if not isinstance(other, SparseMatrix):
            return NotImplemented

        if self.shape != other.shape:
            raise ValueError(
                f"Невозможно сложить матрицы разных размеров: {self.shape} и {other.shape}"
            )

        new_default: T = self._default + other._default
        result: Self = self.__class__(self._rows, self._cols, default=new_default)
        all_coords: set[tuple[int, int]] = set(self._data.keys()) | set(other._data.keys())

        for coord in all_coords:
            sum_val: T = self[coord] + other[coord]
            if sum_val != new_default:
                result._data[coord] = sum_val

        return result

    def __sub__(self, other: Self) -> Self:
        """Вычитает матрицу other из текущей матрицы."""
        if not isinstance(other, SparseMatrix):
            return NotImplemented

        if self.shape != other.shape:
            raise ValueError(
                f"Невозможно вычесть матрицы разных размеров: {self.shape} и {other.shape}"
            )

        new_default: T = self._default - other._default
        result: Self = self.__class__(self._rows, self._cols, default=new_default)
        all_coords: set[tuple[int, int]] = set(self._data.keys()) | set(other._data.keys())

        for coord in all_coords:
            diff_val: T = self[coord] - other[coord]
            if diff_val != new_default:
                result._data[coord] = diff_val

        return result

    def __mul__(self, scalar: T) -> Self:
        """Выполняет поэлементное умножение матрицы на скаляр."""
        new_default: T = self._default * scalar
        result: Self = self.__class__(self._rows, self._cols, default=new_default)

        for coord, val in self._data.items():
            prod_val: T = val * scalar
            if prod_val != new_default:
                result._data[coord] = prod_val

        return result

    def __rmul__(self, scalar: T) -> Self:
        """Поддерживает правостороннее умножение скаляра на матрицу."""
        return self.__mul__(scalar)

    def __neg__(self) -> Self:
        """Возвращает отрицание матрицы (все элементы умножаются на -1)."""
        new_default: T = -self._default
        result: Self = self.__class__(self._rows, self._cols, default=new_default)

        for coord, val in self._data.items():
            neg_val: T = -val
            if neg_val != new_default:
                result._data[coord] = neg_val

        return result

    def __matmul__(self, other: Self) -> Self:
        """Выполняет матричное умножение текущей матрицы на матрицу other."""
        if not isinstance(other, SparseMatrix):
            return NotImplemented

        if self._cols != other._rows:
            raise ValueError(
                f"Несогласованные размеры матриц для умножения: {self.shape} и {other.shape}"
            )

        other_by_row: dict[int, list[tuple[int, T]]] = {}
        for (r_coord, c_coord), b_val in other._data.items():
            other_by_row.setdefault(r_coord, []).append((c_coord, b_val))

        accumulator: dict[tuple[int, int], T] = {}
        for (i_coord, k_coord), a_val in self._data.items():
            row_entries = other_by_row.get(k_coord)
            if row_entries is None:
                continue
            for j_coord, b_val in row_entries:
                target_coord: tuple[int, int] = (i_coord, j_coord)
                product_val: T = a_val * b_val
                if target_coord in accumulator:
                    accumulator[target_coord] = accumulator[target_coord] + product_val
                else:
                    accumulator[target_coord] = product_val

        result: Self = self.__class__(self._rows, other._cols, default=0)
        for coord, val in accumulator.items():
            if val != result.default:
                result._data[coord] = val

        return result

    def to_dense(self) -> list[list[T]]:
        """Преобразует разреженную матрицу в плотный двумерный список."""
        return [
            [self._data.get((r, c), self._default) for c in range(self._cols)]
            for r in range(self._rows)
        ]

    def to_dok(self) -> dict[tuple[int, int], T]:
        """Возвращает копию внутреннего словаря координат ненулевых элементов."""
        return dict(self._data)

    def items(self) -> Iterator[tuple[tuple[int, int], T]]:
        """Итерирует по координатам и значениям ненулевых элементов."""
        for coord in sorted(self._data.keys()):
            yield coord, self._data[coord]

    def keys(self) -> Iterator[tuple[int, int]]:
        """Итерирует по координатам ненулевых элементов матрицы."""
        yield from sorted(self._data.keys())

    def values(self) -> Iterator[T]:
        """Итерирует по значениям ненулевых элементов матрицы."""
        for coord in sorted(self._data.keys()):
            yield self._data[coord]

    def clear(self) -> None:
        """Очищает матрицу, сбрасывая все элементы в значение по умолчанию."""
        self._data.clear()

    def copy(self) -> Self:
        """Создает независимую копию матрицы."""
        copied: Self = self.__class__(self._rows, self._cols, default=self._default)
        copied._data = dict(self._data)
        return copied

    def __iter__(self) -> Iterator[tuple[tuple[int, int], T]]:
        """Итерирует по элементам матрицы аналогично методу items()."""
        return self.items()

    def __len__(self) -> int:
        """Возвращает количество сохраненных элементов (nnz)."""
        return self.nnz

    def __eq__(self, other: object) -> bool:
        """Проверяет поэлементное равенство двух матриц."""
        if not isinstance(other, SparseMatrix):
            return False

        if self.shape != other.shape:
            return False

        all_coords: set[tuple[int, int]] = set(self._data.keys()) | set(other._data.keys())
        for coord in all_coords:
            if self[coord] != other[coord]:
                return False

        return True

    def __repr__(self) -> str:
        """Возвращает формальное строковое представление матрицы."""
        return (
            f"SparseMatrix(rows={self._rows}, cols={self._cols}, "
            f"nnz={self.nnz}, default={self._default!r})"
        )

    def __str__(self) -> str:
        """Возвращает компактное текстовое описание матрицы."""
        return (
            f"<SparseMatrix {self._rows}x{self._cols}, "
            f"{self.nnz} non-default entries (density: {self.density:.1%})>"
        )
