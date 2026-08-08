"""
Desktop GUI for the Huffman zipper, built with customtkinter.

This replaces app.py. Same basic idea - a small window with compress /
decompress buttons and a light/dark toggle - but:
  - it no longer depends on image files that weren't included with the
    project (imgs/*.gif, *.png, *.ico), so it just runs
  - it accepts ANY file type to compress, not just .txt
  - it reports the actual compression ratio instead of a generic message
  - it shows a real error dialog instead of silently doing nothing if
    something goes wrong (e.g. decompressing a file that isn't a .huf file)
  - it can show the Huffman binary tree for the last file you processed,
    in its own window (previously only available via the CLI's --visualize)
  - it keeps a running activity log of what you've compressed/decompressed
    this session, with sizes and ratios
  - it has a "How Huffman Works" window that steps through the tree
    construction one merge at a time, drawn as the row-of-boxes forest
    you'd see in a textbook walkthrough
"""

import os
import time

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from huffman_compressor import HuffmanZipper
from huffman_steps import build_with_steps

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

zipper = HuffmanZipper()

TEXTBOOK_EXAMPLE = "A:7,B:9,C:11,D:14,E:18,F:21,G:27,H:29,I:35,J:40"


# ---------------------------------------------------------------------------
# Tree viewer window (text view of the final tree)
# ---------------------------------------------------------------------------

class TreeWindow(ctk.CTkToplevel):
    """A separate window that shows the Huffman tree for whichever file
    was most recently compressed or decompressed."""

    def __init__(self, master, tree_text: str):
        super().__init__(master)
        self.title("Huffman Tree")
        self.geometry("560x480")

        box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Courier", size=12))
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", tree_text)
        box.configure(state="disabled")


# ---------------------------------------------------------------------------
# "How Huffman Works" step-by-step visualizer
# ---------------------------------------------------------------------------

LEAF_W = 74      # horizontal space reserved per leaf, in pixels
LEVEL_H = 78     # vertical space per tree level
TOP_MARGIN = 40
LEAF_COLOR = "#e8e8e8"
MERGED_COLOR = "#bcdcff"
HIGHLIGHT_COLOR = "#ffcf7a"
LINE_COLOR = "#666666"


def _leaf_count(node) -> int:
    if node.is_leaf():
        return 1
    left = _leaf_count(node.left) if node.left else 0
    right = _leaf_count(node.right) if node.right else 0
    return max(left + right, 1)


def _draw_node(canvas, node, x_center, y, unit_w, highlight):
    if node.is_leaf():
        canvas.create_rectangle(
            x_center - 26, y - 18, x_center + 26, y + 18,
            fill=LEAF_COLOR, outline="#888888",
        )
        canvas.create_text(x_center, y - 5, text=str(node.symbol), font=("Courier", 11, "bold"))
        canvas.create_text(x_center, y + 9, text=str(node.freq), font=("Courier", 8))
        return

    fill = HIGHLIGHT_COLOR if highlight else MERGED_COLOR
    canvas.create_oval(
        x_center - 22, y - 22, x_center + 22, y + 22,
        fill=fill, outline="#444444", width=2,
    )
    canvas.create_text(x_center, y, text=str(node.freq), font=("Courier", 10, "bold"))

    children = [c for c in (node.left, node.right) if c is not None]
    counts = [_leaf_count(c) for c in children]
    total = sum(counts) or 1
    start_x = x_center - unit_w / 2
    cursor = 0.0
    for child, count in zip(children, counts):
        child_w = unit_w * (count / total)
        child_center = start_x + cursor + child_w / 2
        canvas.create_line(x_center, y + 22, child_center, y + LEVEL_H - 18,
                            fill=LINE_COLOR)
        _draw_node(canvas, child, child_center, y + LEVEL_H, child_w, False)
        cursor += child_w


def draw_forest(canvas, forest, merged_node):
    """Draw the current row of boxes/circles, with each surviving node's
    already-built subtree hanging beneath it - this is what makes it look
    like the textbook slide instead of just a flat list."""
    canvas.delete("all")
    if not forest:
        return

    counts = [_leaf_count(n) for n in forest]
    total_units = sum(counts)
    total_width = max(total_units * LEAF_W, 400)
    canvas.configure(scrollregion=(0, 0, total_width, 420))

    x = 20
    for node, count in zip(forest, counts):
        w = count * LEAF_W
        center = x + w / 2
        _draw_node(canvas, node, center, TOP_MARGIN, w, node is merged_node)
        x += w


class StepsWindow(ctk.CTkToplevel):
    """
    The 'How Huffman Works' window: builds a Huffman tree one merge at a
    time and lets you click through it, either on a small example you
    type in yourself or on the most frequent bytes from the last file
    you compressed.
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("How Huffman Works")
        self.geometry("880x640")
        self.minsize(640, 480)

        self.steps = []
        self.index = 0

        # -- mode / input controls -----------------------------------
        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(controls, text="Custom example (symbol:freq, comma separated):",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, columnspan=3,
                                                       sticky="w", padx=8, pady=(8, 2))

        self.entry = ctk.CTkEntry(controls, width=420)
        self.entry.insert(0, TEXTBOOK_EXAMPLE)
        self.entry.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")

        ctk.CTkButton(controls, text="Build from text", width=140,
                      command=self.build_from_entry).grid(row=1, column=1, padx=4)

        ctk.CTkButton(controls, text="Load textbook example", width=170,
                      command=self.load_textbook_example).grid(row=1, column=2, padx=4)

        ctk.CTkButton(controls, text="Visualize my last compressed file (top 12 bytes)",
                      command=self.build_from_last_file).grid(
            row=2, column=0, columnspan=3, padx=8, pady=(0, 8), sticky="w")

        # -- canvas + scrollbar ----------------------------------------
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.canvas = tk.Canvas(canvas_frame, bg="#fafafa", highlightthickness=0)
        hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hbar.set)
        self.canvas.pack(fill="both", expand=True)
        hbar.pack(fill="x")

        # -- step caption + nav buttons ----------------------------------
        self.caption = ctk.CTkLabel(self, text="Enter frequencies above and click "
                                                 "\"Build from text\" to start.",
                                     font=ctk.CTkFont(size=13))
        self.caption.pack(pady=(4, 2))

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(pady=(0, 12))

        self.back_btn = ctk.CTkButton(nav, text="< Back", width=100,
                                       command=self.go_back, state="disabled")
        self.back_btn.grid(row=0, column=0, padx=8)

        self.step_label = ctk.CTkLabel(nav, text="Step 0 of 0", width=120)
        self.step_label.grid(row=0, column=1, padx=8)

        self.next_btn = ctk.CTkButton(nav, text="Next >", width=100,
                                       command=self.go_next, state="disabled")
        self.next_btn.grid(row=0, column=2, padx=8)

    # -- building ------------------------------------------------------

    def load_textbook_example(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, TEXTBOOK_EXAMPLE)
        self.build_from_entry()

    def build_from_entry(self):
        text = self.entry.get().strip()
        freq_table = {}
        try:
            for part in text.split(","):
                part = part.strip()
                if not part:
                    continue
                symbol, freq = part.split(":")
                freq_table[symbol.strip()] = int(freq.strip())
        except (ValueError, IndexError):
            messagebox.showerror(
                "Couldn't read that",
                "Use the format symbol:freq, separated by commas - "
                "e.g. A:7,B:9,C:11",
            )
            return
        if not freq_table:
            messagebox.showerror("Nothing to build", "Type at least one symbol:freq pair.")
            return
        self._build(freq_table)

    def build_from_last_file(self):
        freq_table = zipper.get_last_top_frequencies(limit=12)
        if not freq_table:
            messagebox.showinfo(
                "No file yet",
                "Compress a file first (from the main window), then come back "
                "and click this again.",
            )
            return
        self._build(freq_table)
        source = zipper._last_source_label or "the last file"
        self.caption.configure(
            text=f"Showing the {len(freq_table)} most frequent bytes from "
                 f"{source} (full file still uses every byte when compressed)."
        )

    def _build(self, freq_table):
        _, self.steps = build_with_steps(freq_table)
        self.index = 0
        self.back_btn.configure(state="normal")
        self.next_btn.configure(state="normal")
        self._render()

    # -- navigation ------------------------------------------------------

    def go_next(self):
        if self.index < len(self.steps) - 1:
            self.index += 1
            self._render()

    def go_back(self):
        if self.index > 0:
            self.index -= 1
            self._render()

    def _render(self):
        if not self.steps:
            return
        step = self.steps[self.index]
        draw_forest(self.canvas, step["forest"], step["merged"])

        self.step_label.configure(text=f"Step {self.index} of {len(self.steps) - 1}")
        self.back_btn.configure(state=("normal" if self.index > 0 else "disabled"))
        self.next_btn.configure(state=("normal" if self.index < len(self.steps) - 1 else "disabled"))

        merged = step["merged"]
        if merged is None:
            self.caption.configure(
                text=f"Starting forest: {len(step['forest'])} nodes, "
                     "none merged yet."
            )
        else:
            left, right = merged.left, merged.right
            left_label = left.symbol if left.is_leaf() else f"a node (freq {left.freq})"
            right_label = right.symbol if right.is_leaf() else f"a node (freq {right.freq})"
            if left_label == right_label:
                self.caption.configure(
                    text=f"Merged the two smallest nodes into a new node "
                         f"(freq {merged.freq})."
                )
            else:
                self.caption.configure(
                    text=f"Merged '{left_label}' (freq {left.freq}) and "
                         f"'{right_label}' (freq {right.freq}) into a new "
                         f"node (freq {merged.freq})."
                )


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Huffman File Zipper")
        self.geometry("480x600")
        self.resizable(False, False)

        title = ctk.CTkLabel(
            self, text="Huffman File Zipper",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(25, 5))

        subtitle = ctk.CTkLabel(
            self,
            text="Compress any file using a Huffman binary tree,\n"
                 "or restore one from a .huf archive.",
            font=ctk.CTkFont(size=13),
            justify="center",
        )
        subtitle.pack(pady=(0, 20))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=4)

        ctk.CTkButton(
            button_row, text="Compress a file", width=220, height=45,
            command=self.compress_file,
        ).grid(row=0, column=0, padx=6, pady=6)

        ctk.CTkButton(
            button_row, text="Decompress a .huf file", width=220, height=45,
            command=self.decompress_file,
        ).grid(row=0, column=1, padx=6, pady=6)

        second_row = ctk.CTkFrame(self, fg_color="transparent")
        second_row.pack(pady=(4, 15))

        self.tree_button = ctk.CTkButton(
            second_row, text="View Huffman Tree", width=220, height=38,
            fg_color="transparent", border_width=1,
            command=self.show_tree, state="disabled",
        )
        self.tree_button.grid(row=0, column=0, padx=6, pady=4)

        ctk.CTkButton(
            second_row, text="How Huffman Works", width=220, height=38,
            fg_color="transparent", border_width=1,
            command=self.show_steps,
        ).grid(row=0, column=1, padx=6, pady=4)

        log_label = ctk.CTkLabel(self, text="Activity", anchor="w",
                                  font=ctk.CTkFont(size=13, weight="bold"))
        log_label.pack(fill="x", padx=20)

        self.log_box = ctk.CTkTextbox(self, height=220,
                                       font=ctk.CTkFont(family="Courier", size=11))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.log_box.configure(state="disabled")

        self.theme_switch = ctk.CTkSwitch(
            self, text="Dark mode", command=self.toggle_theme,
        )
        self.theme_switch.pack(pady=(0, 15))

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def show_tree(self):
        TreeWindow(self, zipper.get_last_tree_text())

    def show_steps(self):
        StepsWindow(self)

    def compress_file(self):
        path = filedialog.askopenfilename(title="Select a file to compress")
        if not path:
            return
        try:
            result = zipper.compress_file(path)
        except Exception as exc:
            messagebox.showerror("Compression failed", str(exc))
            self.log(f"FAILED to compress {os.path.basename(path)}: {exc}")
            return

        self.tree_button.configure(state="normal")
        self.log(
            "Compressed {} -> {} ({:,} -> {:,} bytes, {:.1f}% saved)".format(
                os.path.basename(path),
                os.path.basename(result["output_path"]),
                result["original_size"], result["compressed_size"],
                result["ratio_percent"],
            )
        )
        messagebox.showinfo(
            "Compression complete",
            "Saved to:\n{}\n\nOriginal:   {:,} bytes\nCompressed: {:,} bytes\nSaved:      {:.1f}%".format(
                result["output_path"], result["original_size"],
                result["compressed_size"], result["ratio_percent"],
            ),
        )

    def decompress_file(self):
        path = filedialog.askopenfilename(
            title="Select a .huf file to decompress",
            filetypes=(("Huffman archives", "*.huf"), ("all files", "*.*")),
        )
        if not path:
            return
        try:
            result = zipper.decompress_file(path)
        except Exception as exc:
            messagebox.showerror("Decompression failed", str(exc))
            self.log(f"FAILED to decompress {os.path.basename(path)}: {exc}")
            return

        self.tree_button.configure(state="normal")
        self.log(
            "Decompressed {} -> {} ({:,} bytes)".format(
                os.path.basename(path),
                os.path.basename(result["output_path"]),
                result["output_size"],
            )
        )
        messagebox.showinfo(
            "Decompression complete",
            "Saved to:\n{}\n\nSize: {:,} bytes".format(
                result["output_path"], result["output_size"],
            ),
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
