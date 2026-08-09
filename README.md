# Huffman File Zipper

A general-purpose file compressor built around a Huffman binary tree and a
hand-written min-heap — a working upgrade of your original tkinter Huffman
project, with the bugs fixed and extended to be an actual usable "zipper".

It compresses **any** file (not just `.txt`), restores the original file
extension automatically on decompress, and comes with both a CLI and a
GUI, plus a way to print the Huffman tree itself so you can see the data
structure you built.

---

## 1. Project structure

```
huffman_zipper/
├── heap.py                  # your min-heap (priority queue), documented
├── huffman_tree.py          # Node class, tree building, codes, tree text-view
├── huffman_steps.py         # step-by-step tree builder used by the visualizer
├── huffman_compressor.py    # file format + compress/decompress engine
├── theme.py                  # shared dark color palette + fonts for the GUI
├── tree_canvas.py             # shared tree-drawing code (Tree page + step playback)
├── console_log.py             # generates the Compress page's console log lines
├── cli.py                    # command-line interface
├── gui.py                    # Huffman Studio - the tabbed dark-themed GUI
├── sample.txt                 # a file to try compression on immediately
├── tests/
│   └── test_huffman.py       # round-trip, step-builder, and console-log tests
├── requirements.txt
├── .gitignore
└── README.md
```

**How the pieces fit together:** `heap.py` is a plain min-heap used as a
priority queue. `huffman_tree.py` uses it to build a Huffman **binary
tree** out of byte frequencies, then walks that tree to generate codes
(and, on the way back, to decode them) - this is what actually runs
during compression. `huffman_steps.py` builds the *same kind* of tree a
different way (the classic "two queue" method) purely so the GUI's Tree
Visualizer can record and replay construction one merge at a time.
`huffman_compressor.py` wraps the real tree logic with file I/O and a
binary file format. `theme.py`, `tree_canvas.py`, and `console_log.py`
are all GUI support modules - colors/fonts, tree drawing, and log-line
generation, respectively - kept separate from `gui.py` so the page
layout code doesn't get tangled up with drawing/styling logic. `cli.py`
and `gui.py` are two different front ends for the same underlying engine.

---

## 2. Setup

### Windows (10/11)

```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Ubuntu / Linux (e.g. your Ubuntu 24.04 side of the dual-boot)

tkinter isn't always bundled with the system Python on Debian/Ubuntu, so
install it once via apt, then set up a venv as usual:

```
sudo apt update
sudo apt install python3-tk python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Both give you the one real dependency, `customtkinter` (only needed for
the GUI — the CLI has no dependencies beyond the standard library).

---

## 3. Running it

### Command line (works with any file type)

```
python cli.py compress sample.txt
python cli.py decompress sample.huf
```

Add `--visualize` to either command to print the Huffman tree it built:

```
python cli.py compress sample.txt --visualize
```

Custom output paths:

```
python cli.py compress myphoto.png -o myphoto_compressed.huf
python cli.py decompress myphoto_compressed.huf -o restored.png
```

### GUI

```
python gui.py
```

**Huffman Studio** is one window with a top nav bar switching between
three pages (no more separate popup windows):

- **Dashboard** — an overview with two entry points ("Launch Encoder
  Tool" and "Visualize Algorithm") plus a short explanation of what makes
  Huffman coding work, for context.
- **Compress / Decompress** — toggle between Compress Mode and
  Decompress Mode, click the dashed drop zone to browse for a file (any
  file type, or a `.huf` archive in decompress mode), and see real
  results: original/compressed size, a live "space saved" progress ring,
  a "Save output as..." button, and a **console log** that narrates what
  actually happened during that run (frequency table size, each merge,
  final size) - generated from the real data, not placeholder text.
- **Tree Visualizer** — shows the completed Huffman tree by default
  (matching the closed-form textbook diagram: leaves as bordered cards,
  each edge labeled with its 0/1 bit, the root highlighted), plus a
  Back/Next/Play/slider row if you want to rewind and watch it get built
  merge by merge. Feed it data by typing your own `symbol:freq` pairs,
  loading the classic textbook example, or clicking "Visualize my last
  file" to use the 12 most frequent bytes from whatever you just
  compressed. A **prefix codes table** underneath lists every symbol's
  final code.

Note: the "drop zone" is a styled click target (opens the normal file
picker), not literal OS drag-and-drop - that would need an extra
third-party package (`tkinterdnd2`) that isn't in `requirements.txt`.

### Tests

```
python tests/test_huffman.py
```

Covers a normal text round-trip, a single-repeated-byte file (an edge
case that crashed the original code), arbitrary binary data, extension
restoration, rejecting a corrupted/non-`.huf` file, the step-builder's
merge order, and that the console log reflects real compression numbers.

---

## 4. What changed from your original code, and why

Your `heaps.py` logic was already correct — it's carried over almost
unchanged (as `heap.py`), just documented. Everything below lived in
`app.py` / `compressor.py`:

| Bug in the original | Why it mattered | Fix |
|---|---|---|
| `calcFrequency()` set a character's *first* occurrence to `0` instead of `1` | Every stored frequency was one less than the real count — didn't crash anything, but made the tree slightly non-optimal | `build_frequency_table()` uses `freq.get(byte, 0) + 1` |
| `binaryfileText.rstrip()` before compressing | Silently drops trailing whitespace/newline-like bytes — lossy for text, outright corrupts many binary files | Removed entirely; nothing is stripped, so every file round-trips exactly |
| No handling for a file with only **one** unique byte value | A single-leaf tree gets an empty string `""` as its code, which breaks both encoding and decoding | `build_huffman_tree()` wraps the lone leaf under a dummy parent so it gets a real 1-bit code |
| Code table written as `str(dict)` and read back with `eval()` | `eval()` on bytes read from a file will run arbitrary Python code if that file is ever corrupted or crafted maliciously — worth remembering generally, especially for CTF/forensics-style input handling | Header is now a fixed binary layout (`struct`-packed symbol/code-length/code-bits), parsed without ever executing anything |
| GUI only accepted `.txt` in, `.bin` out, and needed image files (`imgs/*.gif`, `.png`, `.ico`) that weren't included | Not really a "zipper" if it only works on one file type, and the app couldn't even launch without missing assets | `gui.py` accepts any file, uses `.huf` as its own format extension, and needs no external image files |
| No error handling in the GUI | Decompressing a bad file just failed silently | Both GUI buttons now show a real error dialog via `messagebox.showerror` |
| Original `.bin` files couldn't remember their real extension | Decompressing `photo.png` → `photo.bin` → back would leave you with a bare `photo`, extension lost | `.huf` files store the original extension in their header, so `decompress` writes `..._decompressed.png` automatically |

---

## 5. The `.huf` file format

```
4 bytes    magic header, b"HUFZ"
1 byte     length of the original file extension
N bytes    the extension itself, e.g. ".png" (utf-8)
2 bytes    number of distinct byte values used (big-endian uint16)
for each distinct byte value:
    1 byte     the byte value (0-255)
    1 byte     length of its Huffman code, in bits
    M bytes    the code, packed into bits, right-padded to a whole byte
1 byte     number of padding bits added to the very end of the data
remaining  the Huffman-encoded file content, packed 8 bits per byte
```

Storing the code table directly (rather than re-deriving it from
frequencies) means decompression doesn't need to reconstruct tie-breaks
from the original compression run — it just walks the stored codes
straight back into a tree (`rebuild_tree_from_codes` in
`huffman_tree.py`) and decodes bit by bit.

**Worth trying:** compress a file of genuinely random bytes
(`os.urandom(...)`) and you'll see the "compressed" output is actually
*larger* than the original. That's not a bug — Huffman coding only helps
when byte frequencies are skewed (like in text, where `e` and space show
up constantly and `q` and `x` barely do). Random data has no skew to
exploit, and the header itself (storing up to 256 codes) adds overhead.
Already-compressed formats (jpg, mp3, zip, png) behave similarly for the
same reason — they're closer to random-looking at the byte level.

---

## 6. Where this could go next (roadmap)

Roughly in order of how much they'd add for how much effort:

1. **Canonical Huffman codes** — store just the code *lengths* instead of
   the full code strings, and derive the actual codes from those lengths
   on both ends. Shrinks the header, and is the standard approach real
   formats (like DEFLATE/zip) use.
2. **Chunked/streaming compression** — right now the whole file is read
   into memory at once. For very large files, process it in blocks and
   write output incrementally instead.
3. **A drag-and-drop GUI target** and a progress bar for large files
   (customtkinter supports both without new dependencies).
4. **A real archive mode**: compress *multiple* files/a whole folder into
   one `.huf`-like container, the way a real zip file does.
5. **Benchmark against `zlib`/`gzip`** (both in the standard library) on
   the same files, and compare compression ratios and speed — a natural
   next step for the "binary tree" theory-to-practice angle of the
   project, and an easy way to show *why* real-world tools use more
   involved algorithms (LZ77 + Huffman, in DEFLATE's case) on top of
   plain Huffman coding.
6. **Visualize the tree graphically** instead of as ASCII — e.g. render
   it with `graphviz` or `matplotlib` and export a PNG alongside the
   `.huf` file.
