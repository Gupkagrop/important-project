"""Pocket Toolkit — коллекция легковесных структур данных и утилит."""

from pocket_toolkit.algorithms.binary_search import (
    binary_search,
    binary_search_last,
    binary_search_rotated,
    equal_range,
    lower_bound,
    upper_bound,
)
from pocket_toolkit.algorithms.levenshtein import (
    AlignmentStep,
    EditOperation,
    damerau_levenshtein_distance,
    find_closest_matches,
    levenshtein_alignment,
    levenshtein_distance,
    levenshtein_matrix,
    levenshtein_similarity,
)
from pocket_toolkit.structures.bloom_filter import BloomFilter
from pocket_toolkit.structures.bounded_deque import BoundedDeque
from pocket_toolkit.structures.disjoint_set import DisjointSet
from pocket_toolkit.structures.doubly_linked_list import DoublyLinkedList, DoublyNode
from pocket_toolkit.structures.lfu_cache import LFUCache
from pocket_toolkit.structures.linked_list import LinkedList, Node
from pocket_toolkit.structures.lru_cache import LRUCache
from pocket_toolkit.structures.priority_queue import (
    Comparable,
    PriorityItem,
    PriorityQueue,
)
from pocket_toolkit.structures.radix_tree import RadixNode, RadixTree
from pocket_toolkit.structures.ring_buffer import RingBuffer
from pocket_toolkit.structures.sparse_matrix import SparseMatrix
from pocket_toolkit.structures.trie import Trie, TrieNode

__all__: list[str] = [
    "AlignmentStep",
    "BloomFilter",
    "BoundedDeque",
    "Comparable",
    "DisjointSet",
    "DoublyLinkedList",
    "DoublyNode",
    "EditOperation",
    "LFUCache",
    "LRUCache",
    "LinkedList",
    "Node",
    "PriorityItem",
    "PriorityQueue",
    "RadixNode",
    "RadixTree",
    "RingBuffer",
    "SparseMatrix",
    "Trie",
    "TrieNode",
    "binary_search",
    "binary_search_last",
    "binary_search_rotated",
    "damerau_levenshtein_distance",
    "equal_range",
    "find_closest_matches",
    "levenshtein_alignment",
    "levenshtein_distance",
    "levenshtein_matrix",
    "levenshtein_similarity",
    "lower_bound",
    "upper_bound",
]
