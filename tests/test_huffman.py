"""
Round-trip correctness checks for the Huffman zipper.

Run with:
    python -m pytest tests/          (from the project root, if pytest is installed)
or just:
    python tests/test_huffman.py     (no extra dependencies needed)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from huffman_compressor import HuffmanZipper


def test_round_trip_text():
    zipper = HuffmanZipper()
    original = b"the quick brown fox jumps over the lazy dog. " * 20
    compressed = zipper.compress_bytes(original)
    restored, _ = zipper.decompress_bytes(compressed)
    assert restored == original
    assert len(compressed) < len(original)


def test_round_trip_single_symbol():
    """Edge case the original project's code didn't handle: a file made
    of only one unique byte value. Without the fix in build_huffman_tree,
    this raises/produces garbage instead of round-tripping."""
    zipper = HuffmanZipper()
    original = b"a" * 500
    compressed = zipper.compress_bytes(original)
    restored, _ = zipper.decompress_bytes(compressed)
    assert restored == original


def test_round_trip_binary_data():
    """Arbitrary (non-text) bytes, including ones that look like
    whitespace - the original project's rstrip() call would have
    corrupted data like this."""
    zipper = HuffmanZipper()
    original = bytes(range(256)) * 4 + b"\t\n \r"
    compressed = zipper.compress_bytes(original)
    restored, _ = zipper.decompress_bytes(compressed)
    assert restored == original


def test_extension_round_trip():
    zipper = HuffmanZipper()
    compressed = zipper.compress_bytes(b"hello world" * 10, extension=".txt")
    _, ext = zipper.decompress_bytes(compressed)
    assert ext == ".txt"


def test_rejects_bad_header():
    zipper = HuffmanZipper()
    try:
        zipper.decompress_bytes(b"not a real huf file")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    test_round_trip_text()
    test_round_trip_single_symbol()
    test_round_trip_binary_data()
    test_extension_round_trip()
    test_rejects_bad_header()
    print("All tests passed.")
