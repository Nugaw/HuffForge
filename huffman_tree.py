"""
Huffman tree construction and code generation.

This is the "binary tree" half of the project. Every compressed file gets
its own Huffman tree, built bottom-up from a min-heap of nodes (heap.py):
each leaf holds one byte value (0-255) and how often it appeared; each
internal node just holds the combined frequency of its two children.
Walking left/right from the root down to a leaf gives that byte a unique
bit-string code (shorter codes for common bytes, longer for rare ones) -
that's the whole compression trick. Walking the *same* tree bit-by-bit in
reverse is how decoding works (see decode_with_tree below).
"""

from heap import heappush, heappop


class Node:
    """A node in the Huffman tree. Leaves store a symbol (a byte value,
    0-255); internal nodes have symbol=None and exist only to hold their
    two children together."""

    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.left is None and self.right is None

    def __lt__(self, other):
        # Only frequency matters for heap ordering - this is what your
        # original heap_node.__lt__ did too.
        return self.freq < other.freq


def build_frequency_table(data: bytes) -> dict:
    """Count how many times each byte value appears in data."""
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    return freq
    # Bug fixed here: your original calcFrequency() did
    #     frequencyDict[character] = 0   (on first sighting)
    #     frequencyDict[character] += 1  (on every sighting after that)
    # which means a character's very first occurrence was never counted -
    # every stored frequency was one less than the real count. It never
    # crashed anything, but it made the tree slightly less optimal.
    # freq.get(byte, 0) + 1 counts the first occurrence too.


def build_huffman_tree(freq_table: dict) -> Node:
    """Build the Huffman tree from a frequency table and return its root."""
    heap = []
    for symbol, freq in freq_table.items():
        heappush(heap, Node(symbol=symbol, freq=freq))

    if not heap:
        return None

    # Edge case your original code didn't handle: a file with only ONE
    # unique byte value (e.g. a file full of the same character). The
    # merge loop below needs at least 2 nodes to run at all, so without
    # this the lone node would become the root by itself - and a leaf
    # sitting at the root gets an empty string "" as its code, which
    # breaks both encoding (nothing gets written) and decoding. Wrapping
    # it under one dummy parent gives it the code "0" instead.
    if len(heap) == 1:
        only = heappop(heap)
        heappush(heap, Node(symbol=None, freq=only.freq, left=only))

    while len(heap) > 1:
        left = heappop(heap)
        right = heappop(heap)
        merged = Node(symbol=None, freq=left.freq + right.freq,
                       left=left, right=right)
        heappush(heap, merged)

    return heappop(heap)


def build_codes(root: Node) -> dict:
    """Walk the tree to assign every leaf a bit-string code: '0' for every
    left turn taken to reach it, '1' for every right turn. Returns
    {byte_value: code_string}."""
    codes = {}

    def _walk(node, path):
        if node is None:
            return
        if node.is_leaf():
            codes[node.symbol] = path
            return
        _walk(node.left, path + "0")
        _walk(node.right, path + "1")

    _walk(root, "")
    return codes


def rebuild_tree_from_codes(codes: dict) -> Node:
    """
    The inverse of build_codes(): given {byte_value: code_string}, rebuild
    the same tree shape by walking each code bit-by-bit and creating nodes
    on demand. The decompressor uses this instead of re-running Huffman on
    a frequency table, because the codes themselves are stored directly in
    the compressed file's header (see huffman_compressor.py) - so decoding
    doesn't need to guess how any ties were broken during compression.
    """
    root = Node()
    for symbol, code in codes.items():
        node = root
        for bit in code:
            if bit == "0":
                if node.left is None:
                    node.left = Node()
                node = node.left
            else:
                if node.right is None:
                    node.right = Node()
                node = node.right
        node.symbol = symbol
    return root


def decode_with_tree(root: Node, bitstring: str) -> bytearray:
    """Walk the tree left/right, one bit at a time. Every time a leaf is
    reached, emit its byte and jump back to the root for the next code.
    This mirrors build_codes() - same tree, opposite direction."""
    decoded = bytearray()
    node = root
    for bit in bitstring:
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            decoded.append(node.symbol)
            node = root
    return decoded


def tree_to_string(node: Node, prefix: str = "", is_last: bool = True,
                    is_root: bool = True) -> str:
    """Build an indented ASCII view of the tree as a single string, purely
    so you can *see* the binary tree you just built. Leaves show the byte
    and its frequency; internal nodes show only the combined frequency.
    Used by both the CLI (print_tree, below) and the GUI's "View Huffman
    Tree" window, so the two front ends stay in sync automatically."""
    if node is None:
        return ""
    connector = "" if is_root else ("`-- " if is_last else "|-- ")
    lines = []
    if node.is_leaf():
        printable = chr(node.symbol) if 32 <= node.symbol <= 126 else f"0x{node.symbol:02x}"
        lines.append(f"{prefix}{connector}Leaf(byte={printable!r}, freq={node.freq})")
    else:
        lines.append(f"{prefix}{connector}Node(freq={node.freq})")
        extension = "    " if is_last else "|   "
        new_prefix = prefix if is_root else prefix + extension
        left_str = tree_to_string(node.left, new_prefix, False, False)
        right_str = tree_to_string(node.right, new_prefix, True, False)
        if left_str:
            lines.append(left_str)
        if right_str:
            lines.append(right_str)
    return "\n".join(lines)


def print_tree(node: Node) -> None:
    """Print the ASCII tree view to stdout (used by the CLI)."""
    text = tree_to_string(node)
    if text:
        print(text)
