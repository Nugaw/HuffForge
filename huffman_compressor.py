"""
File-level Huffman compression/decompression.

.huf file format:
    4 bytes   magic header, b"HUFZ"
    1 byte    length of the original file extension, e.g. len(".txt") = 4
    N bytes   the original file extension itself (utf-8), so decompress()
              can restore "photo.png" instead of a bare "photo"
    2 bytes   number of distinct byte values used (big-endian unsigned short)
    for each distinct byte value:
        1 byte    the byte value itself (0-255)
        1 byte    length of its Huffman code, in bits
        M bytes   the code packed into bits, right-padded with 0s to a
                   whole number of bytes (M = ceil(code_length / 8))
    1 byte    number of padding bits added to the very end of the encoded
              data below (0-7), so the reader knows exactly where the
              real data stops
    remaining bytes: the Huffman-encoded file content, packed 8 bits/byte

Why this format instead of the original one: your compressor.py wrote the
code dictionary out as Python's str(dict) representation, then decompressor()
read it back with eval(). That works for well-behaved input, but eval() will
happily execute arbitrary Python code if it's ever fed a crafted/corrupted
.bin file - never eval() bytes that came from a file (worth remembering for
CTF/forensics work too). The struct-based layout above stores exactly the
bytes needed and nothing gets executed while reading it.

The original code also worked on .txt files only, and called
`binaryfileText.rstrip()` on the raw file bytes before compressing - which
silently drops trailing whitespace/newline bytes. Fine for some text files,
but lossy (and outright file-corrupting) for anything else, including most
binary formats. This version doesn't strip anything, so it round-trips any
file exactly.
"""

import os
import struct

from huffman_tree import (
    build_frequency_table,
    build_huffman_tree,
    build_codes,
    rebuild_tree_from_codes,
    decode_with_tree,
    print_tree,
    tree_to_string,
)

MAGIC = b"HUFZ"


class HuffmanZipper:
    def __init__(self):
        self._last_tree = None       # kept around so visualize_last_tree() works
        self._last_freq_table = None  # from the last compress_bytes() call
        self._last_source_label = None  # filename, for the GUI to show

    # ---- in-memory API (bytes in, bytes out) --------------------------

    def compress_bytes(self, data: bytes, extension: str = "") -> bytes:
        if len(data) == 0:
            raise ValueError("Cannot compress an empty file.")

        freq_table = build_frequency_table(data)
        root = build_huffman_tree(freq_table)
        codes = build_codes(root)
        self._last_tree = root
        self._last_freq_table = freq_table

        ext_bytes = extension.encode("utf-8")
        if len(ext_bytes) > 255:
            raise ValueError("File extension is too long.")

        header = bytearray()
        header += MAGIC
        header += struct.pack("B", len(ext_bytes))
        header += ext_bytes
        header += struct.pack(">H", len(codes))
        for symbol, code in codes.items():
            header += struct.pack("BB", symbol, len(code))
            header += self._bits_to_bytes(code)

        bitstring = "".join(codes[b] for b in data)
        padding = (8 - len(bitstring) % 8) % 8
        bitstring += "0" * padding

        out = bytearray()
        out += header
        out += struct.pack("B", padding)
        out += self._bits_to_bytes(bitstring)
        return bytes(out)

    def decompress_bytes(self, blob: bytes) -> tuple[bytes, str]:
        """Returns (original_bytes, original_extension)."""
        if blob[:4] != MAGIC:
            raise ValueError("Not a .huf file (missing/incorrect header).")
        pos = 4

        ext_len = blob[pos]
        pos += 1
        extension = blob[pos:pos + ext_len].decode("utf-8")
        pos += ext_len

        num_symbols = struct.unpack(">H", blob[pos:pos + 2])[0]
        pos += 2

        codes = {}
        for _ in range(num_symbols):
            symbol, code_len = struct.unpack("BB", blob[pos:pos + 2])
            pos += 2
            n_bytes = (code_len + 7) // 8
            code_bytes = blob[pos:pos + n_bytes]
            pos += n_bytes
            bits = self._bytes_to_bits(code_bytes)[:code_len]
            codes[symbol] = bits

        padding = blob[pos]
        pos += 1

        bitstring = self._bytes_to_bits(blob[pos:])
        if padding:
            bitstring = bitstring[:-padding]

        root = rebuild_tree_from_codes(codes)
        self._last_tree = root
        return bytes(decode_with_tree(root, bitstring)), extension

    # ---- file API -------------------------------------------------------

    def compress_file(self, input_path: str, output_path: str = None) -> dict:
        with open(input_path, "rb") as f:
            data = f.read()

        extension = os.path.splitext(input_path)[1]
        compressed = self.compress_bytes(data, extension)
        self._last_source_label = os.path.basename(input_path)

        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + ".huf"
        with open(output_path, "wb") as f:
            f.write(compressed)

        original_size = len(data)
        compressed_size = len(compressed)
        ratio = (1 - compressed_size / original_size) * 100 if original_size else 0
        return {
            "output_path": output_path,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "ratio_percent": ratio,
        }

    def decompress_file(self, input_path: str, output_path: str = None) -> dict:
        with open(input_path, "rb") as f:
            blob = f.read()
        decompressed, extension = self.decompress_bytes(blob)

        if output_path is None:
            stem = input_path[:-4] if input_path.endswith(".huf") else input_path
            output_path = f"{stem}_decompressed{extension}"
        with open(output_path, "wb") as f:
            f.write(decompressed)

        return {
            "output_path": output_path,
            "output_size": len(decompressed),
        }

    def visualize_last_tree(self):
        if self._last_tree is None:
            print("No tree to show yet - run compress or decompress first.")
            return
        print_tree(self._last_tree)

    def get_last_tree_text(self) -> str:
        """Same tree view as visualize_last_tree(), but returned as a
        string instead of printed - used by the GUI's text tree view."""
        if self._last_tree is None:
            return "No tree to show yet - compress or decompress a file first."
        return tree_to_string(self._last_tree)

    def get_last_tree(self):
        """The last built tree's root Node (or None) - used by the GUI's
        graphical tree view."""
        return self._last_tree

    def get_last_top_frequencies(self, limit: int = 12) -> dict:
        """
        The last COMPRESSED file's most frequent bytes, trimmed to `limit`
        entries and relabeled with printable characters (e.g. 65 -> 'A').
        Used by the GUI's step-by-step visualizer: a real file can have up
        to 256 distinct byte values, which is too many to lay out
        readably as a row of boxes, so only the most frequent ones are
        shown. This does NOT affect actual compression/decompression,
        which always uses every byte.
        """
        if not self._last_freq_table:
            return {}
        top = sorted(self._last_freq_table.items(), key=lambda kv: -kv[1])[:limit]
        result = {}
        for byte_value, freq in top:
            label = chr(byte_value) if 32 <= byte_value <= 126 else f"0x{byte_value:02x}"
            # guard against two different byte values mapping to the same
            # printable label (shouldn't happen since keys are unique
            # byte values, but keep it defensive)
            while label in result:
                label += " "
            result[label] = freq
        return result

    # ---- bit-packing helpers --------------------------------------------

    @staticmethod
    def _bits_to_bytes(bitstring: str) -> bytes:
        pad = (8 - len(bitstring) % 8) % 8
        padded = bitstring + "0" * pad
        return bytes(int(padded[i:i + 8], 2) for i in range(0, len(padded), 8))

    @staticmethod
    def _bytes_to_bits(data: bytes) -> str:
        return "".join(f"{byte:08b}" for byte in data)
