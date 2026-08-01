"""
Command-line interface for the Huffman zipper. Works on any file type.

Usage:
    python cli.py compress   <input_file>     [-o output.huf]   [--visualize]
    python cli.py decompress <input_file.huf> [-o output_file]  [--visualize]

Examples:
    python cli.py compress sample.txt
    python cli.py decompress sample.huf
    python cli.py compress photo.png --visualize
"""

import argparse

from huffman_compressor import HuffmanZipper


def main():
    parser = argparse.ArgumentParser(
        description="Huffman-coding file compressor/decompressor."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("compress", help="Compress a file into a .huf archive")
    c.add_argument("input", help="Path to the file to compress")
    c.add_argument("-o", "--output",
                    help="Output .huf path (default: same name with .huf extension)")
    c.add_argument("--visualize", action="store_true",
                    help="Print the Huffman tree after compressing")

    d = sub.add_parser("decompress", help="Restore a file from a .huf archive")
    d.add_argument("input", help="Path to the .huf file")
    d.add_argument("-o", "--output",
                    help="Output path (default: <name>_decompressed.<original extension>)")
    d.add_argument("--visualize", action="store_true",
                    help="Print the Huffman tree after decompressing")

    args = parser.parse_args()
    zipper = HuffmanZipper()

    if args.command == "compress":
        result = zipper.compress_file(args.input, args.output)
        print(f"Compressed: {args.input}")
        print(f"  -> {result['output_path']}")
        print(f"  original:   {result['original_size']:,} bytes")
        print(f"  compressed: {result['compressed_size']:,} bytes")
        print(f"  saved:      {result['ratio_percent']:.1f}%")
    else:
        result = zipper.decompress_file(args.input, args.output)
        print(f"Decompressed: {args.input}")
        print(f"  -> {result['output_path']}")
        print(f"  size: {result['output_size']:,} bytes")

    if args.visualize:
        print("\nHuffman tree:")
        zipper.visualize_last_tree()


if __name__ == "__main__":
    main()
