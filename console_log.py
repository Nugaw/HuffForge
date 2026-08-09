"""
Builds the human-readable "console" lines shown in the Compress/Decompress
page's log panel, using the REAL data from whatever was just compressed or
decompressed - not placeholder text. Kept as plain functions (no GUI code)
so they're easy to test on their own; gui.py handles coloring/rendering.

Each line is returned as (tag, text), where tag is "sys", "algo", or
"queue" and just picks which color the line is drawn in.

Note on the merge narrative: real compression always builds its tree with
the heap in huffman_tree.py (that's what actually determines the bytes
written to disk). The step-by-step merge lines below are generated with
huffman_steps.build_with_steps() instead - the same "two queue" method
used by the tree/steps view - purely because it produces a clean,
readable merge order for the log. Both methods produce a valid, equally
optimal Huffman tree; only the display order can differ.
"""

from huffman_steps import build_with_steps

MAX_MERGE_LINES = 24


def _label(node) -> str:
    if node.is_leaf():
        return f"{node.symbol}:{node.freq}"
    return f"Internal:{node.freq}"


def compress_log_lines(source_name, original_size, freq_table, output_path,
                        compressed_size, ratio_percent):
    lines = [
        ("sys", f"Loaded input file: {source_name} ({original_size:,} bytes)"),
        ("algo", "Computing byte frequency table..."),
        ("algo", f"Frequency map generated. {len(freq_table)} unique byte value(s) found."),
        ("queue", "Min-heap priority queue initialized. Inserting leaf nodes..."),
    ]

    _, steps = build_with_steps(freq_table)
    merge_steps = [s for s in steps if s["merged"] is not None]
    shown = merge_steps[:MAX_MERGE_LINES]
    for step in shown:
        merged = step["merged"]
        lines.append((
            "queue",
            f"Nodes merged: ({_label(merged.left)}) + ({_label(merged.right)}) "
            f"-> (Internal Node: {merged.freq})",
        ))
    remaining = len(merge_steps) - len(shown)
    if remaining > 0:
        lines.append(("queue", f"... {remaining} more merge(s) ..."))

    lines.append(("sys", "Binary tree encoding completed. Building code table..."))
    lines.append(("sys", f"Saved compressed archive: {output_path}"))
    lines.append((
        "sys",
        f"{original_size:,} -> {compressed_size:,} bytes ({ratio_percent:.1f}% saved).",
    ))
    return lines


def decompress_log_lines(source_name, compressed_size, tree_leaf_count,
                          output_path, output_size):
    return [
        ("sys", f"Loaded compressed archive: {source_name} ({compressed_size:,} bytes)"),
        ("algo", "Reading header and Huffman code table..."),
        ("algo", f"{tree_leaf_count} symbol code(s) loaded."),
        ("queue", "Rebuilding decode tree from stored codes..."),
        ("sys", "Decoding bitstream..."),
        ("sys", f"Decompression complete. Restored to: {output_path}"),
        ("sys", f"Output size: {output_size:,} bytes."),
    ]
