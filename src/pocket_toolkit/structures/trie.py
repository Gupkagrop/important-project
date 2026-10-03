"""Реализация префиксного дерева (Trie) для эффективного поиска и автодополнения строк."""

from collections.abc import Iterable, Iterator


class TrieNode[V]:
    """Узел префиксного дерева (Trie).

    Хранит словарь ссылок на дочерние узлы по символам, признак окончания слова
    и опциональное полезное значение (payload), ассоциированное со словом.
    """

    __slots__ = ("children", "is_end_of_word", "value")

    def __init__(
        self,
        is_end_of_word: bool = False,
        value: V | None = None,
    ) -> None:
        """Инициализирует узел префиксного дерева.

        :param is_end_of_word: Флаг завершения слова на данном узле.
        :param value: Полезная нагрузка (значение), ассоциированная со словом.
        """
        self.children: dict[str, TrieNode[V]] = {}
        self.is_end_of_word: bool = is_end_of_word
        self.value: V | None = value

    @property
    def has_children(self) -> bool:
        """Проверяет, есть ли у узла дочерние элементы."""
        return len(self.children) > 0

    def __repr__(self) -> str:
        """Строковое представление узла префиксного дерева."""
        return (
            f"TrieNode(is_end_of_word={self.is_end_of_word}, "
            f"value={self.value!r}, children_count={len(self.children)})"
        )


class Trie[V]:
    """Префиксное дерево (Trie / Prefix Tree).

    Обеспечивает эффективную вставку, поиск, проверку префиксов и автодополнение
    строк за время O(L), где L — длина строки, независимо от размера словаря.
    Поддерживает сохранение полезной нагрузки для каждого ключа, удаление с очисткой
    неиспользуемых узлов и настройку чувствительности к регистру символов.
    """

    def __init__(
        self,
        words: Iterable[str] | None = None,
        initial_items: Iterable[tuple[str, V]] | None = None,
        case_sensitive: bool = True,
    ) -> None:
        """Инициализирует пустое префиксное дерево.

        :param words: Опциональная последовательность строк для начального добавления.
        :param initial_items: Опциональная последовательность пар (слово, значение).
        :param case_sensitive: Флаг чувствительности к регистру символов.
        """
        self._root: TrieNode[V] = TrieNode()
        self._size: int = 0
        self._case_sensitive: bool = case_sensitive

        if words is not None:
            for word in words:
                self.insert(word)

        if initial_items is not None:
            for key, val in initial_items:
                self.insert(key, val)

    @property
    def root(self) -> TrieNode[V]:
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

    def is_empty(self) -> bool:
        """Проверяет, пусти ли префиксное дерево."""
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

    def insert(self, key: str, value: V | None = None) -> None:
        """Добавляет строку и опциональное значение в префиксное дерево.

        :param key: Строка для добавления.
        :param value: Ассоциированное значение (по умолчанию None).
        :raises TypeError: Если ключ не является строкой.
        """
        normalized_key: str = self._normalize_key(key)
        current: TrieNode[V] = self._root

        for char in normalized_key:
            if char not in current.children:
                current.children[char] = TrieNode()
            current = current.children[char]

        if not current.is_end_of_word:
            current.is_end_of_word = True
            self._size += 1

        current.value = value

    def search(self, key: str) -> bool:
        """Проверяет наличие точного совпадения слова в дереве.

        :param key: Искомое слово.
        :return: True, если слово присутствует в дереве, иначе False.
        :raises TypeError: Если ключ не является строкой.
        """
        normalized_key: str = self._normalize_key(key)
        node: TrieNode[V] | None = self._find_node(normalized_key)
        if node is None:
            return False
        return node.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """Проверяет, существует ли в дереве хотя бы одно слово с данным префиксом.

        :param prefix: Искомый строковый префикс.
        :return: True, если префикс найден, иначе False.
        :raises TypeError: Если префикс не является строкой.
        """
        normalized_prefix: str = self._normalize_key(prefix)
        if self._size == 0:
            return False

        node: TrieNode[V] | None = self._find_node(normalized_prefix)
        return node is not None

    def get(self, key: str, default: V | None = None) -> V | None:
        """Возвращает ассоциированное значение для слова или default, если слово не найдено.

        :param key: Искомое слово.
        :param default: Значение по умолчанию.
        :return: Значение узла или default.
        :raises TypeError: Если ключ не является строкой.
        """
        normalized_key: str = self._normalize_key(key)
        node: TrieNode[V] | None = self._find_node(normalized_key)
        if node is None or not node.is_end_of_word:
            return default
        return node.value

    def remove(self, key: str) -> bool:
        """Удаляет слово из префиксного дерева с очисткой неиспользуемых узлов.

        :param key: Удаляемое слово.
        :return: True, если слово найдено и успешно удалено, False если слова не было.
        :raises TypeError: Если ключ не является строкой.
        """
        normalized_key: str = self._normalize_key(key)
        stack: list[tuple[str, TrieNode[V], TrieNode[V]]] = []
        current: TrieNode[V] = self._root

        for char in normalized_key:
            if char not in current.children:
                return False
            next_node: TrieNode[V] = current.children[char]
            stack.append((char, current, next_node))
            current = next_node

        if not current.is_end_of_word:
            return False

        current.is_end_of_word = False
        current.value = None
        self._size -= 1

        self._prune_nodes(stack)
        return True

    def _prune_nodes(self, stack: list[tuple[str, TrieNode[V], TrieNode[V]]]) -> None:
        """Удаляет цепочку пустых родительских узлов снизу вверх."""
        while stack:
            char, parent_node, child_node = stack.pop()
            if child_node.has_children or child_node.is_end_of_word:
                break
            del parent_node.children[char]

    def _find_node(self, prefix: str) -> TrieNode[V] | None:
        """Находит узел, соответствующий заданной строке префикса.

        :param prefix: Нормализованный строковый префикс.
        :return: Узел дерева или None, если префикс не существует.
        """
        current: TrieNode[V] = self._root
        for char in prefix:
            if char not in current.children:
                return None
            current = current.children[char]
        return current

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

        normalized_prefix: str = self._normalize_key(prefix)
        start_node: TrieNode[V] | None = self._find_node(normalized_prefix)
        if start_node is None:
            return []

        return self._collect_words(start_node, normalized_prefix, limit)

    def find_words_with_prefix(self, prefix: str = "", limit: int | None = None) -> list[str]:
        """Псевдоним метода autocomplete для явного семантического поиска по префиксу.

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

        normalized_prefix: str = self._normalize_key(prefix)
        start_node: TrieNode[V] | None = self._find_node(normalized_prefix)
        if start_node is None:
            return []

        return self._collect_items(start_node, normalized_prefix, limit)

    def count_words_with_prefix(self, prefix: str) -> int:
        """Подсчитывает общее количество слов в дереве, начинающихся с префикса.

        :param prefix: Искомый префикс.
        :return: Количество слов с данным префиксом.
        :raises TypeError: Если префикс не является строкой.
        """
        normalized_prefix: str = self._normalize_key(prefix)
        start_node: TrieNode[V] | None = self._find_node(normalized_prefix)
        if start_node is None:
            return 0

        count: int = 0
        stack: list[TrieNode[V]] = [start_node]
        while stack:
            current: TrieNode[V] = stack.pop()
            if current.is_end_of_word:
                count += 1
            stack.extend(current.children.values())

        return count

    def longest_common_prefix(self) -> str:
        """Вычисляет наибольший общий префикс (LCP) среди всех слов в дереве.

        :return: Строка общего префикса или пустая строка, если дерево пусто
                 или общих начальных символов нет.
        """
        if self._size == 0:
            return ""

        prefix_chars: list[str] = []
        current: TrieNode[V] = self._root

        while len(current.children) == 1:
            if current.is_end_of_word:
                break
            char: str = next(iter(current.children))
            prefix_chars.append(char)
            current = current.children[char]

        return "".join(prefix_chars)

    def _collect_words(
        self,
        start_node: TrieNode[V],
        start_prefix: str,
        limit: int | None,
    ) -> list[str]:
        """Итеративно собирает слова в поддереве в лексикографическом порядке."""
        if limit is not None and limit == 0:
            return []

        results: list[str] = []
        stack: list[tuple[TrieNode[V], str]] = [(start_node, start_prefix)]

        while stack:
            node, current_word = stack.pop()
            if node.is_end_of_word:
                results.append(current_word)
                if limit is not None and len(results) >= limit:
                    break

            sorted_chars: list[str] = sorted(node.children.keys(), reverse=True)
            for char in sorted_chars:
                stack.append((node.children[char], current_word + char))

        return results

    def _collect_items(
        self,
        start_node: TrieNode[V],
        start_prefix: str,
        limit: int | None,
    ) -> list[tuple[str, V | None]]:
        """Итеративно собирает пары (слово, значение) в лексикографическом порядке."""
        if limit is not None and limit == 0:
            return []

        results: list[tuple[str, V | None]] = []
        stack: list[tuple[TrieNode[V], str]] = [(start_node, start_prefix)]

        while stack:
            node, current_word = stack.pop()
            if node.is_end_of_word:
                results.append((current_word, node.value))
                if limit is not None and len(results) >= limit:
                    break

            sorted_chars: list[str] = sorted(node.children.keys(), reverse=True)
            for char in sorted_chars:
                stack.append((node.children[char], current_word + char))

        return results

    def words(self) -> list[str]:
        """Возвращает отсортированный список всех сохраненных слов."""
        return self.autocomplete(prefix="")

    def items(self) -> list[tuple[str, V | None]]:
        """Возвращает отсортированный список всех пар (слово, значение)."""
        return self.find_items_with_prefix(prefix="")

    def values(self) -> list[V | None]:
        """Возвращает список всех значений для сохраненных слов."""
        return [value for _, value in self.items()]

    def clear(self) -> None:
        """Полностью очищает префиксное дерево."""
        self._root = TrieNode()
        self._size = 0

    def __contains__(self, key: str) -> bool:
        """Проверяет принадлежность слова дереву через оператор `in`."""
        return self.search(key)

    def __getitem__(self, key: str) -> V | None:
        """Возвращает ассоциированное со словом значение по индексу."""
        normalized_key: str = self._normalize_key(key)
        node: TrieNode[V] | None = self._find_node(normalized_key)
        if node is None or not node.is_end_of_word:
            raise KeyError(f"Ключ '{key}' не найден в префиксном дереве")
        return node.value

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
        """Строковое представление префиксного дерева."""
        return f"Trie(size={self._size}, case_sensitive={self._case_sensitive})"
