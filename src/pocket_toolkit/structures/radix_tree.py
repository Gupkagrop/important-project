"""Реализация сжатого префиксного дерева (Radix Tree / Patricia Trie).

Обеспечивает компактное хранение строковых ключей с автоматическим слиянием
однородных ребер и эффективным поиском по префиксу.
"""

from collections.abc import Iterable, Iterator


class RadixNode[V]:
    """Узел сжатого префиксного дерева (Radix Tree).

    Хранит сжатый строковый префикс ребра, словарь дочерних узлов,
    признак завершения слова и ассоциированное значение полезной нагрузки.
    """

    __slots__ = ("children", "is_end_of_word", "prefix", "value")

    def __init__(
        self,
        prefix: str = "",
        is_end_of_word: bool = False,
        value: V | None = None,
    ) -> None:
        """Инициализирует узел сжатого префиксного дерева.

        :param prefix: Строковый фрагмент (префикс), ассоциированный с данным узлом.
        :param is_end_of_word: Флаг завершения слова на данном узле.
        :param value: Полезная нагрузка (значение), ассоциированная со словом.
        """
        self.prefix: str = prefix
        self.children: dict[str, RadixNode[V]] = {}
        self.is_end_of_word: bool = is_end_of_word
        self.value: V | None = value

    @property
    def has_children(self) -> bool:
        """Проверяет наличие дочерних узлов."""
        return len(self.children) > 0

    @property
    def children_count(self) -> int:
        """Возвращает количество дочерних узлов."""
        return len(self.children)

    def __repr__(self) -> str:
        """Строковое представление узла сжатого префиксного дерева."""
        return (
            f"RadixNode(prefix={self.prefix!r}, is_end_of_word={self.is_end_of_word}, "
            f"value={self.value!r}, children_count={len(self.children)})"
        )


class RadixTree[V]:
    """Сжатое префиксное дерево (Radix Tree / Patricia Trie).

    Оптимизированная версия префиксного дерева, в которой узлы с единственным
    дочерним элементом объединяются, что значительно снижает потребление памяти
    и глубину дерева при сохранении быстродействия O(K) для операций поиска.
    """

    def __init__(
        self,
        words: Iterable[str] | None = None,
        initial_items: Iterable[tuple[str, V]] | None = None,
        case_sensitive: bool = True,
    ) -> None:
        """Инициализирует пустое сжатое префиксное дерево.

        :param words: Опциональная последовательность строк для добавления.
        :param initial_items: Опциональная последовательность пар (ключ, значение).
        :param case_sensitive: Флаг чувствительности к регистру символов.
        """
        self._root: RadixNode[V] = RadixNode()
        self._size: int = 0
        self._case_sensitive: bool = case_sensitive

        if words is not None:
            for word in words:
                self.insert(word)

        if initial_items is not None:
            for key, val in initial_items:
                self.insert(key, val)

    @property
    def root(self) -> RadixNode[V]:
        """Возвращает корневой узел дерева."""
        return self._root

    @property
    def size(self) -> int:
        """Возвращает количество уникальных слов, сохраненных в дереве."""
        return self._size

    @property
    def case_sensitive(self) -> bool:
        """Возвращает True, если дерево чувствительно к регистру."""
        return self._case_sensitive

    @property
    def node_count(self) -> int:
        """Возвращает общее количество физических узлов в дереве (включая корень)."""
        count: int = 0
        stack: list[RadixNode[V]] = [self._root]
        while stack:
            node: RadixNode[V] = stack.pop()
            count += 1
            stack.extend(node.children.values())
        return count

    def is_empty(self) -> bool:
        """Проверяет, пусто ли сжатое префиксное дерево."""
        return self._size == 0

    def _normalize_key(self, key: str) -> str:
        """Проверяет тип ключа и приводит его к целевому регистру.

        :param key: Исходный строковый ключ.
        :return: Нормализованная строка.
        :raises TypeError: Если ключ не является строкой.
        """
        if not isinstance(key, str):
            raise TypeError(f"Ключ должен быть строкой, получено: {type(key).__name__}")
        if not self._case_sensitive:
            return key.lower()
        return key

    @staticmethod
    def _common_prefix_length(str1: str, str2: str) -> int:
        """Вычисляет длину наибольшего общего префикса двух строк."""
        min_len: int = min(len(str1), len(str2))
        idx: int = 0
        while idx < min_len and str1[idx] == str2[idx]:
            idx += 1
        return idx

    def insert(self, key: str, value: V | None = None) -> None:
        """Добавляет строку и опциональное значение в сжатое префиксное дерево.

        :param key: Строка для добавления.
        :param value: Ассоциированное значение (по умолчанию None).
        :raises TypeError: Если ключ не является строкой.
        """
        norm_key: str = self._normalize_key(key)
        if not norm_key:
            if not self._root.is_end_of_word:
                self._root.is_end_of_word = True
                self._size += 1
            self._root.value = value
            return

        self._insert_non_empty(norm_key, value)

    def _insert_non_empty(self, key: str, value: V | None) -> None:
        """Вставляет непустой ключ в дерево с расщеплением узлов при необходимости."""
        current: RadixNode[V] = self._root
        rem_key: str = key

        while rem_key:
            first_char: str = rem_key[0]
            if first_char not in current.children:
                current.children[first_char] = RadixNode(
                    prefix=rem_key,
                    is_end_of_word=True,
                    value=value,
                )
                self._size += 1
                return

            child: RadixNode[V] = current.children[first_char]
            common_len: int = self._common_prefix_length(rem_key, child.prefix)

            if common_len < len(child.prefix):
                self._split_and_insert(
                    current, child, first_char, common_len, rem_key, value
                )
                return

            if common_len == len(rem_key):
                if not child.is_end_of_word:
                    child.is_end_of_word = True
                    self._size += 1
                child.value = value
                return

            current = child
            rem_key = rem_key[common_len:]

    def _split_and_insert(
        self,
        parent: RadixNode[V],
        child: RadixNode[V],
        first_char: str,
        common_len: int,
        rem_key: str,
        value: V | None,
    ) -> None:
        """Расщепляет существующий узел на общий префикс и суффиксы."""
        common_part: str = child.prefix[:common_len]
        child_suffix: str = child.prefix[common_len:]

        child.prefix = child_suffix
        split_node: RadixNode[V] = RadixNode(prefix=common_part)
        split_node.children[child_suffix[0]] = child
        parent.children[first_char] = split_node

        if common_len == len(rem_key):
            split_node.is_end_of_word = True
            split_node.value = value
            self._size += 1
            return

        new_suffix: str = rem_key[common_len:]
        new_leaf: RadixNode[V] = RadixNode(
            prefix=new_suffix,
            is_end_of_word=True,
            value=value,
        )
        split_node.children[new_suffix[0]] = new_leaf
        self._size += 1

    def search(self, key: str) -> bool:
        """Проверяет наличие точного совпадения слова в дереве.

        :param key: Искомое слово.
        :return: True, если слово присутствует в дереве, иначе False.
        :raises TypeError: Если ключ не является строкой.
        """
        norm_key: str = self._normalize_key(key)
        if not norm_key:
            return self._root.is_end_of_word

        current: RadixNode[V] = self._root
        rem_key: str = norm_key

        while rem_key:
            first_char: str = rem_key[0]
            if first_char not in current.children:
                return False
            child: RadixNode[V] = current.children[first_char]
            if not rem_key.startswith(child.prefix):
                return False
            rem_key = rem_key[len(child.prefix) :]
            current = child

        return current.is_end_of_word

    def get(self, key: str, default: V | None = None) -> V | None:
        """Возвращает ассоциированное значение для слова или значение по умолчанию.

        :param key: Искомое слово.
        :param default: Значение по умолчанию, если слово отсутствует.
        :return: Сохраненное значение или default.
        :raises TypeError: Если ключ не является строкой.
        """
        norm_key: str = self._normalize_key(key)
        if not norm_key:
            return self._root.value if self._root.is_end_of_word else default

        current: RadixNode[V] = self._root
        rem_key: str = norm_key

        while rem_key:
            first_char: str = rem_key[0]
            if first_char not in current.children:
                return default
            child: RadixNode[V] = current.children[first_char]
            if not rem_key.startswith(child.prefix):
                return default
            rem_key = rem_key[len(child.prefix) :]
            current = child

        if not current.is_end_of_word:
            return default
        return current.value

    def starts_with(self, prefix: str) -> bool:
        """Проверяет, существует ли в дереве хотя бы одно слово с данным префиксом.

        :param prefix: Искомый строковый префикс.
        :return: True, если префикс найден, иначе False.
        :raises TypeError: Если префикс не является строкой.
        """
        normalized_prefix: str = self._normalize_key(prefix)
        if self._size == 0:
            return False
        start_node, _ = self._find_prefix_subtree(normalized_prefix)
        return start_node is not None

    def _find_prefix_subtree(self, prefix: str) -> tuple[RadixNode[V] | None, str]:
        """Находит узел поддерева и накопленный базовый префикс для заданного поиска."""
        if not prefix:
            return self._root, ""

        current: RadixNode[V] = self._root
        rem_prefix: str = prefix
        accumulated_path: str = ""

        while rem_prefix:
            first_char: str = rem_prefix[0]
            if first_char not in current.children:
                return None, ""

            child: RadixNode[V] = current.children[first_char]
            if len(rem_prefix) <= len(child.prefix):
                if not child.prefix.startswith(rem_prefix):
                    return None, ""
                return child, accumulated_path + child.prefix

            if not rem_prefix.startswith(child.prefix):
                return None, ""

            accumulated_path += child.prefix
            rem_prefix = rem_prefix[len(child.prefix) :]
            current = child

        return current, accumulated_path

    def autocomplete(self, prefix: str = "", limit: int | None = None) -> list[str]:
        """Возвращает список слов, начинающихся с заданного префикса.

        Слова отсортированы в лексикографическом порядке.

        :param prefix: Исходный строковый префикс (по умолчанию пустая строка).
        :param limit: Опциональное максимальное количество возвращаемых слов.
        :return: Список найденных слов.
        :raises TypeError: Если префикс не является строкой.
        :raises ValueError: Если лимит меньше нуля.
        """
        if limit is not None and limit < 0:
            raise ValueError("Лимит выборки не может быть отрицательным числом")

        norm_prefix: str = self._normalize_key(prefix)
        start_node, base_prefix = self._find_prefix_subtree(norm_prefix)
        if start_node is None:
            return []

        return self._collect_words(start_node, base_prefix, limit)

    def find_words_with_prefix(
        self, prefix: str = "", limit: int | None = None
    ) -> list[str]:
        """Псевдоним метода autocomplete для явного семантического поиска.

        :param prefix: Исходный строковый префикс.
        :param limit: Опциональный лимит количества результатов.
        :return: Список найденных слов.
        """
        return self.autocomplete(prefix=prefix, limit=limit)

    def find_items_with_prefix(
        self,
        prefix: str = "",
        limit: int | None = None,
    ) -> list[tuple[str, V | None]]:
        """Возвращает пары (слово, значение) для всех слов с заданным префиксом.

        :param prefix: Исходный строковый префикс.
        :param limit: Опциональный лимит количества результатов.
        :return: Список кортежей (слово, значение).
        :raises TypeError: Если префикс не является строкой.
        :raises ValueError: Если лимит меньше нуля.
        """
        if limit is not None and limit < 0:
            raise ValueError("Лимит выборки не может быть отрицательным числом")

        norm_prefix: str = self._normalize_key(prefix)
        start_node, base_prefix = self._find_prefix_subtree(norm_prefix)
        if start_node is None:
            return []

        return self._collect_items(start_node, base_prefix, limit)

    def _collect_words(
        self,
        start_node: RadixNode[V],
        base_prefix: str,
        limit: int | None,
    ) -> list[str]:
        """Итеративно собирает слова в лексикографическом порядке."""
        if limit is not None and limit == 0:
            return []

        results: list[str] = []
        stack: list[tuple[RadixNode[V], str]] = [(start_node, base_prefix)]

        while stack:
            node, current_word = stack.pop()
            if node.is_end_of_word:
                results.append(current_word)
                if limit is not None and len(results) >= limit:
                    break

            sorted_keys: list[str] = sorted(node.children.keys(), reverse=True)
            for key in sorted_keys:
                child: RadixNode[V] = node.children[key]
                stack.append((child, current_word + child.prefix))

        return results

    def _collect_items(
        self,
        start_node: RadixNode[V],
        base_prefix: str,
        limit: int | None,
    ) -> list[tuple[str, V | None]]:
        """Итеративно собирает пары (слово, значение) в лексикографическом порядке."""
        if limit is not None and limit == 0:
            return []

        results: list[tuple[str, V | None]] = []
        stack: list[tuple[RadixNode[V], str]] = [(start_node, base_prefix)]

        while stack:
            node, current_word = stack.pop()
            if node.is_end_of_word:
                results.append((current_word, node.value))
                if limit is not None and len(results) >= limit:
                    break

            sorted_keys: list[str] = sorted(node.children.keys(), reverse=True)
            for key in sorted_keys:
                child: RadixNode[V] = node.children[key]
                stack.append((child, current_word + child.prefix))

        return results

    def count_words_with_prefix(self, prefix: str = "") -> int:
        """Подсчитывает общее количество слов в дереве, начинающихся с префикса.

        :param prefix: Искомый префикс.
        :return: Количество слов с данным префиксом.
        :raises TypeError: Если префикс не является строкой.
        """
        normalized_prefix: str = self._normalize_key(prefix)
        start_node, _ = self._find_prefix_subtree(normalized_prefix)
        if start_node is None:
            return 0

        count: int = 0
        stack: list[RadixNode[V]] = [start_node]
        while stack:
            current: RadixNode[V] = stack.pop()
            if current.is_end_of_word:
                count += 1
            stack.extend(current.children.values())
        return count

    def longest_common_prefix(self) -> str:
        """Вычисляет наибольший общий префикс (LCP) среди всех сохраненных слов.

        :return: Строка общего префикса или пустая строка, если слов нет или они не имеют общего начала.
        """
        if self._size == 0 or self._root.is_end_of_word:
            return ""

        if len(self._root.children) != 1:
            return ""

        prefix_parts: list[str] = []
        current: RadixNode[V] = self._root

        while len(current.children) == 1:
            child: RadixNode[V] = next(iter(current.children.values()))
            prefix_parts.append(child.prefix)
            if child.is_end_of_word:
                break
            current = child

        return "".join(prefix_parts)

    def find_longest_prefix_of(self, text: str) -> str:
        """Находит самый длинный сохраненный ключ, являющийся префиксом заданного текста.

        :param text: Исходная строка для сопоставления.
        :return: Наибольший найденный префикс или пустая строка, если совпадений нет.
        :raises TypeError: Если входной параметр не является строкой.
        """
        if not isinstance(text, str):
            raise TypeError(
                f"Текст должен быть строкой, получено: {type(text).__name__}"
            )

        norm_text: str = text if self._case_sensitive else text.lower()
        longest_match: str = ""
        current_path: str = ""
        current: RadixNode[V] = self._root

        if current.is_end_of_word:
            longest_match = ""

        rem_text: str = norm_text
        while rem_text:
            first_char: str = rem_text[0]
            if first_char not in current.children:
                break
            child: RadixNode[V] = current.children[first_char]
            if not rem_text.startswith(child.prefix):
                break
            current_path += child.prefix
            rem_text = rem_text[len(child.prefix) :]
            current = child
            if current.is_end_of_word:
                longest_match = current_path

        return longest_match

    def find_longest_prefix_item_of(self, text: str) -> tuple[str, V | None] | None:
        """Находит самый длинный ключ-префикс текста и ассоциированное значение.

        :param text: Исходная строка для сопоставления.
        :return: Кортеж (ключ, значение) или None, если совпадений нет.
        :raises TypeError: Если входной параметр не является строкой.
        """
        longest_prefix: str = self.find_longest_prefix_of(text)
        if longest_prefix:
            return longest_prefix, self.get(longest_prefix)
        if self._root.is_end_of_word:
            return "", self._root.value
        return None

    def remove(self, key: str) -> bool:
        """Удаляет слово из сжатого префиксного дерева с последующим сжатием узлов.

        :param key: Удаляемое слово.
        :return: True, если слово найдено и успешно удалено, иначе False.
        :raises TypeError: Если ключ не является строкой.
        """
        norm_key: str = self._normalize_key(key)
        if not norm_key:
            return self._remove_empty_key()

        return self._remove_non_empty(norm_key)

    def _remove_empty_key(self) -> bool:
        """Удаляет ключ пустой строки из корня."""
        if not self._root.is_end_of_word:
            return False
        self._root.is_end_of_word = False
        self._root.value = None
        self._size -= 1
        return True

    def _remove_non_empty(self, key: str) -> bool:
        """Удаляет непустой ключ и сжимает цепочки узлов."""
        path: list[tuple[RadixNode[V], str, RadixNode[V]]] = []
        current: RadixNode[V] = self._root
        rem_key: str = key

        while rem_key:
            first_char: str = rem_key[0]
            if first_char not in current.children:
                return False
            child: RadixNode[V] = current.children[first_char]
            if not rem_key.startswith(child.prefix):
                return False
            path.append((current, first_char, child))
            rem_key = rem_key[len(child.prefix) :]
            current = child

        if not current.is_end_of_word:
            return False

        current.is_end_of_word = False
        current.value = None
        self._size -= 1

        self._cleanup_after_removal(path, current)
        return True

    def _cleanup_after_removal(
        self,
        path: list[tuple[RadixNode[V], str, RadixNode[V]]],
        target: RadixNode[V],
    ) -> None:
        """Выполняет удаление пустых листьев и слияние узлов после удаления ключа."""
        if target.has_children:
            if (
                len(target.children) == 1
                and not target.is_end_of_word
                and target is not self._root
            ):
                self._merge_with_child(target)
            return

        parent, char_key, _ = path.pop()
        del parent.children[char_key]

        if (
            parent is not self._root
            and not parent.is_end_of_word
            and len(parent.children) == 1
        ):
            self._merge_with_child(parent)

    @staticmethod
    def _merge_with_child(node: RadixNode[V]) -> None:
        """Сливает узел с его единственным дочерним узлом."""
        child: RadixNode[V] = next(iter(node.children.values()))
        node.prefix = node.prefix + child.prefix
        node.is_end_of_word = child.is_end_of_word
        node.value = child.value
        node.children = child.children

    def words(self) -> list[str]:
        """Возвращает отсортированный список всех сохраненных слов."""
        return self.autocomplete(prefix="")

    def keys(self) -> list[str]:
        """Возвращает отсортированный список всех ключей (псевдоним words)."""
        return self.words()

    def items(self) -> list[tuple[str, V | None]]:
        """Возвращает отсортированный список всех пар (слово, значение)."""
        return self.find_items_with_prefix(prefix="")

    def values(self) -> list[V | None]:
        """Возвращает список всех значений для сохраненных слов."""
        return [value for _, value in self.items()]

    def clear(self) -> None:
        """Полностью очищает сжатое префиксное дерево."""
        self._root = RadixNode()
        self._size = 0

    def __contains__(self, key: str) -> bool:
        """Проверяет принадлежность слова дереву через оператор `in`."""
        return self.search(key)

    def __getitem__(self, key: str) -> V | None:
        """Возвращает ассоциированное со словом значение по индексу."""
        norm_key: str = self._normalize_key(key)
        if not norm_key:
            if not self._root.is_end_of_word:
                raise KeyError(f"Ключ '{key}' не найден в дереве")
            return self._root.value

        current: RadixNode[V] = self._root
        rem_key: str = norm_key
        while rem_key:
            first_char: str = rem_key[0]
            if first_char not in current.children:
                raise KeyError(f"Ключ '{key}' не найден в дереве")
            child: RadixNode[V] = current.children[first_char]
            if not rem_key.startswith(child.prefix):
                raise KeyError(f"Ключ '{key}' не найден в дереве")
            rem_key = rem_key[len(child.prefix) :]
            current = child

        if not current.is_end_of_word:
            raise KeyError(f"Ключ '{key}' не найден в дереве")
        return current.value

    def __setitem__(self, key: str, value: V) -> None:
        """Добавляет или обновляет слово со значением через оператор `[]`."""
        self.insert(key, value)

    def __delitem__(self, key: str) -> None:
        """Удаляет слово из дерева через оператор `del`."""
        removed: bool = self.remove(key)
        if not removed:
            raise KeyError(f"Ключ '{key}' не найден для удаления")

    def __len__(self) -> int:
        """Возвращает количество слов в дереве."""
        return self._size

    def __iter__(self) -> Iterator[str]:
        """Итерирует по всем сохраненным словам в лексикографическом порядке."""
        yield from self.words()

    def __repr__(self) -> str:
        """Строковое представление сжатого префиксного дерева."""
        return (
            f"RadixTree(size={self._size}, node_count={self.node_count}, "
            f"case_sensitive={self._case_sensitive})"
        )

    def __eq__(self, other: object) -> bool:
        """Проверяет равенство с другим деревом или словарем."""
        if isinstance(other, RadixTree):
            return self.items() == other.items()
        if isinstance(other, dict):
            return dict(self.items()) == other
        return False
