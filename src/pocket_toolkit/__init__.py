"""Pocket Toolkit — коллекция легковесных структур данных и утилит."""

from pocket_toolkit.algorithms.binary_search import (
    binary_search,
    binary_search_last,
    binary_search_rotated,
    equal_range,
    lower_bound,
    upper_bound,
)
from pocket_toolkit.algorithms.dijkstra import (
    ShortestPathResult,
    dijkstra,
    find_shortest_path,
)
from pocket_toolkit.algorithms.hashing import (
    crc32,
    crc32_hex,
    fnv1a_32,
    fnv1a_32_hex,
    fnv1a_64,
    fnv1a_64_hex,
    hash_stream_crc32,
)
from pocket_toolkit.algorithms.huffman import (
    HuffmanNode,
    HuffmanTree,
    huffman_decode,
    huffman_encode,
)
from pocket_toolkit.algorithms.intervals import (
    Interval,
    common_intersection,
    insert_interval,
    intersect_interval_lists,
    merge_intervals,
)
from pocket_toolkit.algorithms.kmp import (
    compute_prefix_function,
    kmp_count,
    kmp_find_first,
    kmp_search,
    kmp_search_iter,
    kmp_search_sequence,
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
from pocket_toolkit.algorithms.modular import (
    chinese_remainder_theorem,
    extended_gcd,
    fast_power,
    is_coprime,
    mod_add,
    mod_div,
    mod_mul,
    mod_sub,
    modular_inverse,
)
from pocket_toolkit.algorithms.rle import (
    RLERun,
    calculate_compression_ratio,
    calculate_space_saving,
    rle_decode,
    rle_decode_bytes,
    rle_decode_iter,
    rle_decode_str,
    rle_encode,
    rle_encode_bytes,
    rle_encode_iter,
    rle_encode_str,
)
from pocket_toolkit.algorithms.sampling import (
    fisher_yates_shuffle,
    reservoir_sample,
    shuffled,
    weighted_reservoir_sample,
)
from pocket_toolkit.algorithms.sliding_window import (
    SlidingWindowAggregator,
    sliding_window_extrema,
)
from pocket_toolkit.algorithms.topological_sort import (
    CyclicDependencyError,
    calculate_in_degrees,
    is_dag,
    topological_sort,
    topological_sort_dfs,
)
from pocket_toolkit.cli.arg_parser import (
    ArgumentError,
    ArgumentParser,
    Namespace,
)
from pocket_toolkit.cli.colors import (
    are_colors_enabled,
    blue,
    bold,
    colorize,
    cyan,
    green,
    magenta,
    red,
    set_colors_enabled,
    strip_ansi,
    underline,
    yellow,
)
from pocket_toolkit.cli.progress import (
    ProgressBar,
    track_progress,
)
from pocket_toolkit.cli.table import (
    Table,
    TableBorderStyle,
    format_table,
)
from pocket_toolkit.data.csv_stream import (
    CSVParseError,
    generate_csv_from_dicts,
    generate_csv_line,
    generate_csv_stream,
    parse_csv_dicts,
    parse_csv_stream,
)
from pocket_toolkit.data.diff import (
    DictDiff,
    diff_dict,
    find_dict_delta,
)
from pocket_toolkit.data.flatten import (
    flatten_dict,
    unflatten_dict,
)
from pocket_toolkit.data.math_eval import (
    MathEvaluationError,
    MathSecurityError,
    UndefinedSymbolError,
    evaluate_math,
)
from pocket_toolkit.data.merge import (
    DELETE_FIELD,
    deep_merge,
    deep_patch,
)
from pocket_toolkit.decorators.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)
from pocket_toolkit.decorators.contracts import (
    deprecated,
    validate_types,
)
from pocket_toolkit.decorators.debounce import debounce
from pocket_toolkit.decorators.lazy_property import lazy_property
from pocket_toolkit.decorators.leaky_bucket import (
    LeakyBucket,
    LeakyBucketOverflowError,
    leaky_bucket_limit,
)
from pocket_toolkit.decorators.profiler import (
    ProfileStats,
    profile_time,
)
from pocket_toolkit.decorators.rate_limiter import (
    RateLimitExceededError,
    TokenBucket,
    rate_limit,
)
from pocket_toolkit.decorators.retry import (
    RetryExhaustedError,
    calculate_backoff_delay,
    retry,
)
from pocket_toolkit.decorators.throttle import throttle
from pocket_toolkit.decorators.timed_cache import (
    CacheInfo,
    timed_cache,
)
from pocket_toolkit.functional.compose import (
    Pipeline,
    compose,
    compose_left,
    pipe,
)
from pocket_toolkit.functional.curry import (
    Curried,
    curry,
    uncurry,
)
from pocket_toolkit.strings.bytes import (
    IEC_UNITS,
    SI_UNITS,
    format_bytes,
    parse_bytes,
)
from pocket_toolkit.strings.case import (
    split_words,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_screaming_snake_case,
    to_snake_case,
    to_title_case,
)
from pocket_toolkit.strings.duration import (
    format_duration,
    parse_duration,
)
from pocket_toolkit.strings.query_string import (
    QueryParams,
    build_query,
    parse_query,
)
from pocket_toolkit.strings.semver import (
    SemanticVersion,
    is_valid_semver,
)
from pocket_toolkit.strings.slugify import (
    slugify,
    transliterate,
)
from pocket_toolkit.strings.template import (
    Template,
    TemplateError,
    TemplateSyntaxError,
    render_template,
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
    "DELETE_FIELD",
    "IEC_UNITS",
    "SI_UNITS",
    "AlignmentStep",
    "ArgumentError",
    "ArgumentParser",
    "BloomFilter",
    "BoundedDeque",
    "CSVParseError",
    "CacheInfo",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "Comparable",
    "Curried",
    "CyclicDependencyError",
    "DictDiff",
    "DisjointSet",
    "DoublyLinkedList",
    "DoublyNode",
    "EditOperation",
    "HuffmanNode",
    "HuffmanTree",
    "Interval",
    "LFUCache",
    "LRUCache",
    "LeakyBucket",
    "LeakyBucketOverflowError",
    "LinkedList",
    "MathEvaluationError",
    "MathSecurityError",
    "Namespace",
    "Node",
    "Pipeline",
    "PriorityItem",
    "PriorityQueue",
    "ProfileStats",
    "ProgressBar",
    "QueryParams",
    "RLERun",
    "RadixNode",
    "RadixTree",
    "RateLimitExceededError",
    "RetryExhaustedError",
    "RingBuffer",
    "SemanticVersion",
    "ShortestPathResult",
    "SlidingWindowAggregator",
    "SparseMatrix",
    "Table",
    "TableBorderStyle",
    "Template",
    "TemplateError",
    "TemplateSyntaxError",
    "TokenBucket",
    "Trie",
    "TrieNode",
    "UndefinedSymbolError",
    "are_colors_enabled",
    "binary_search",
    "binary_search_last",
    "binary_search_rotated",
    "blue",
    "bold",
    "build_query",
    "calculate_backoff_delay",
    "calculate_compression_ratio",
    "calculate_in_degrees",
    "calculate_space_saving",
    "chinese_remainder_theorem",
    "colorize",
    "common_intersection",
    "compose",
    "compose_left",
    "compute_prefix_function",
    "crc32",
    "crc32_hex",
    "curry",
    "cyan",
    "damerau_levenshtein_distance",
    "debounce",
    "deep_merge",
    "deep_patch",
    "deprecated",
    "diff_dict",
    "dijkstra",
    "equal_range",
    "evaluate_math",
    "extended_gcd",
    "fast_power",
    "find_closest_matches",
    "find_dict_delta",
    "find_shortest_path",
    "fisher_yates_shuffle",
    "flatten_dict",
    "fnv1a_32",
    "fnv1a_32_hex",
    "fnv1a_64",
    "fnv1a_64_hex",
    "format_bytes",
    "format_duration",
    "format_table",
    "generate_csv_from_dicts",
    "generate_csv_line",
    "generate_csv_stream",
    "green",
    "hash_stream_crc32",
    "huffman_decode",
    "huffman_encode",
    "insert_interval",
    "intersect_interval_lists",
    "is_coprime",
    "is_dag",
    "is_valid_semver",
    "kmp_count",
    "kmp_find_first",
    "kmp_search",
    "kmp_search_iter",
    "kmp_search_sequence",
    "lazy_property",
    "leaky_bucket_limit",
    "levenshtein_alignment",
    "levenshtein_distance",
    "levenshtein_matrix",
    "levenshtein_similarity",
    "lower_bound",
    "magenta",
    "merge_intervals",
    "mod_add",
    "mod_div",
    "mod_mul",
    "mod_sub",
    "modular_inverse",
    "parse_bytes",
    "parse_csv_dicts",
    "parse_csv_stream",
    "parse_duration",
    "parse_query",
    "pipe",
    "profile_time",
    "rate_limit",
    "red",
    "render_template",
    "reservoir_sample",
    "retry",
    "rle_decode",
    "rle_decode_bytes",
    "rle_decode_iter",
    "rle_decode_str",
    "rle_encode",
    "rle_encode_bytes",
    "rle_encode_iter",
    "rle_encode_str",
    "set_colors_enabled",
    "shuffled",
    "sliding_window_extrema",
    "slugify",
    "split_words",
    "strip_ansi",
    "throttle",
    "timed_cache",
    "to_camel_case",
    "to_kebab_case",
    "to_pascal_case",
    "to_screaming_snake_case",
    "to_snake_case",
    "to_title_case",
    "topological_sort",
    "topological_sort_dfs",
    "track_progress",
    "transliterate",
    "uncurry",
    "underline",
    "unflatten_dict",
    "upper_bound",
    "validate_types",
    "weighted_reservoir_sample",
    "yellow",
]
