"""
Huffman Studio - the dark, tabbed desktop GUI for the Huffman zipper.

One window, three pages switched by a top nav bar (Dashboard,
Compress/Decompress, Tree Visualizer) instead of separate popup windows.
Shares one HuffmanZipper instance across pages so "View the tree" and
"visualize my last file" always reflect whatever was most recently
compressed or decompressed.
"""

import os
import time

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

import theme
from huffman_compressor import HuffmanZipper
from huffman_steps import build_with_steps
from huffman_tree import build_codes
from tree_canvas import draw_forest, leaf_count
import console_log

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

zipper = HuffmanZipper()
TEXTBOOK_EXAMPLE = "A:7,B:9,C:11,D:14,E:18,F:21,G:27,H:29,I:35,J:40"


def _scrollable_canvas(parent, bg=theme.BG):
    """A tk.Canvas with both scrollbars, packed into a themed frame.
    Returns (frame, canvas) - pack/grid the frame, draw on the canvas."""
    frame = ctk.CTkFrame(parent, fg_color=theme.CARD_BG, corner_radius=14)
    canvas = tk.Canvas(frame, bg=bg, highlightthickness=0)
    vbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    hbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

    canvas.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))
    vbar.grid(row=0, column=1, sticky="ns", pady=(12, 0))
    hbar.grid(row=1, column=0, sticky="ew", padx=(12, 0))
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    return frame, canvas


def _card(parent, **kw):
    kw.setdefault("fg_color", theme.CARD_BG)
    kw.setdefault("corner_radius", 14)
    return ctk.CTkFrame(parent, **kw)


def _section_label(parent, text):
    return ctk.CTkLabel(parent, text=text, font=theme.font(11, "bold"),
                         text_color=theme.TEXT_SECONDARY, anchor="w")


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(expand=True, fill="both", padx=40, pady=30)

        ctk.CTkLabel(
            wrapper, text="  DATA STRUCTURES & ALGORITHMS PROJECT  ",
            font=theme.font(10, "bold"), text_color=theme.CYAN,
            fg_color=theme.CARD_BG, corner_radius=12,
        ).pack(pady=(6, 22))

        ctk.CTkLabel(wrapper, text="Compress & Visualize",
                     font=theme.font(32, "bold"), text_color=theme.TEXT_PRIMARY).pack()
        ctk.CTkLabel(wrapper, text="with Huffman Coding",
                     font=theme.font(32, "bold"), text_color=theme.CYAN).pack(pady=(0, 16))

        ctk.CTkLabel(
            wrapper,
            text="An interactive simulator for Huffman's optimal prefix coding "
                 "algorithm. Reduce file sizes losslessly while watching the\n"
                 "greedy, queue-based tree construction happen.",
            font=theme.font(13), text_color=theme.TEXT_SECONDARY, justify="center",
        ).pack(pady=(0, 30))

        cards = ctk.CTkFrame(wrapper, fg_color="transparent")
        cards.pack(pady=(0, 34))

        self._feature_card(
            cards, col=0, icon="\U0001F4C2", icon_color=theme.GREEN,
            title="File Encoder & Decoder",
            body="Compress any file and restore it exactly, with real "
                 "compression metrics and a live console log.",
            button_text="Launch Encoder Tool  \u2192",
            button_color=theme.GREEN, button_hover=theme.GREEN_HOVER,
            button_text_color="#062e13",
            target="compress",
        )
        self._feature_card(
            cards, col=1, icon="\U0001F333", icon_color=theme.CYAN,
            title="Tree Graph Visualizer",
            body="Watch the priority queue combine weights step by step, "
                 "rendering the binary tree with a 0/1 code for every leaf.",
            button_text="Visualize Algorithm  \U0001F441",
            button_color=theme.CYAN, button_hover=theme.CYAN_HOVER,
            button_text_color="#04212b",
            target="tree", bordered=True,
        )

        features = ctk.CTkFrame(wrapper, fg_color="transparent")
        features.pack(fill="x")
        for col, (title, body) in enumerate([
            ("OPTIMAL PREFIX CODING",
             "No code is a prefix of another, keeping decompression unambiguous."),
            ("VARIABLE-LENGTH CODES",
             "Frequent bytes get shorter codes, yielding maximum efficiency."),
            ("GREEDY CONSTRUCTION",
             "A min-heap priority queue guarantees an optimal tree every time."),
        ]):
            block = ctk.CTkFrame(features, fg_color="transparent")
            block.grid(row=0, column=col, sticky="nw", padx=(0 if col == 0 else 30, 0))
            ctk.CTkLabel(block, text=title, font=theme.font(10, "bold"),
                         text_color=theme.CYAN, anchor="w").pack(fill="x")
            ctk.CTkLabel(block, text=body, font=theme.font(11), wraplength=260,
                         text_color=theme.TEXT_SECONDARY, justify="left", anchor="w"
                         ).pack(fill="x", pady=(4, 0))

    def _feature_card(self, parent, col, icon, icon_color, title, body,
                       button_text, button_color, button_hover, button_text_color,
                       target, bordered=False):
        card = _card(parent, width=360, height=240,
                     border_width=1 if bordered else 0,
                     border_color=theme.CYAN_DIM if bordered else None)
        card.grid(row=0, column=col, padx=12)
        card.grid_propagate(False)

        ctk.CTkLabel(card, text=icon, font=theme.font(20), text_color=icon_color,
                     fg_color=theme.CARD_BG_LIGHT, corner_radius=10,
                     width=46, height=46).place(x=22, y=20)

        ctk.CTkLabel(card, text=title, font=theme.font(16, "bold"),
                     text_color=theme.TEXT_PRIMARY, anchor="w"
                     ).place(x=22, y=80)
        ctk.CTkLabel(card, text=body, font=theme.font(11), wraplength=310,
                     text_color=theme.TEXT_SECONDARY, justify="left", anchor="nw"
                     ).place(x=22, y=112, width=310, height=60)

        ctk.CTkButton(card, text=button_text, fg_color=button_color,
                      hover_color=button_hover, text_color=button_text_color,
                      font=theme.font(12, "bold"), height=36,
                      command=lambda: self.app.show_page(target)
                      ).place(x=22, y=188)


# ---------------------------------------------------------------------------
# Compress / Decompress page
# ---------------------------------------------------------------------------

class CompressPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app
        self.mode = "compress"
        self.last_result = None

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=30, pady=24)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)
        wrapper.grid_rowconfigure(2, weight=0)

        # -- mode toggle -----------------------------------------------
        mode_card = _card(wrapper)
        mode_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        _section_label(mode_card, "OPERATION MODE").pack(anchor="w", padx=18, pady=(14, 6))
        self.mode_switch = ctk.CTkSegmentedButton(
            mode_card, values=["Compress Mode", "Decompress Mode"],
            font=theme.font(12, "bold"), selected_color=theme.CYAN,
            selected_hover_color=theme.CYAN_HOVER, unselected_color=theme.CARD_BG_LIGHT,
            command=self._on_mode_change, height=38,
        )
        self.mode_switch.set("Compress Mode")
        self.mode_switch.pack(fill="x", padx=18, pady=(0, 18))

        # -- input card --------------------------------------------------
        input_card = _card(wrapper)
        input_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        _section_label(input_card, "INPUT FILE SOURCE").pack(anchor="w", padx=18, pady=(14, 6))

        self.drop_canvas = tk.Canvas(input_card, bg=theme.CARD_BG, highlightthickness=0)
        self.drop_canvas.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.drop_canvas.bind("<Configure>", lambda e: self._draw_drop_zone())
        self.drop_canvas.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_canvas.configure(cursor="hand2")

        # -- metrics card --------------------------------------------------
        self.metrics_card = _card(wrapper)
        self.metrics_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        self._build_metrics_panel()

        # -- console log --------------------------------------------------
        log_card = _card(wrapper)
        log_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(log_header, text="\u25CF", text_color=theme.GREEN,
                     font=theme.font(10)).pack(side="left")
        ctk.CTkLabel(log_header, text=" CONSOLE STEPS LOG", font=theme.font(11, "bold"),
                     text_color=theme.TEXT_SECONDARY).pack(side="left")

        self.console = tk.Text(log_card, height=10, bg="#080b12", fg=theme.TEXT_SECONDARY,
                                insertbackground=theme.TEXT_SECONDARY, relief="flat",
                                font=(theme.MONO, 10), wrap="none", padx=12, pady=8)
        self.console.tag_configure("sys", foreground=theme.TEXT_PRIMARY)
        self.console.tag_configure("algo", foreground=theme.CYAN)
        self.console.tag_configure("queue", foreground=theme.GREEN)
        self.console.tag_configure("num", foreground=theme.TEXT_MUTED)
        self.console.configure(state="disabled")
        self.console.pack(fill="x", padx=18, pady=(0, 18))

        self._draw_drop_zone()

    # -- mode handling ------------------------------------------------

    def _on_mode_change(self, choice):
        self.mode = "compress" if choice == "Compress Mode" else "decompress"
        self.last_result = None
        self._draw_drop_zone()
        self._build_metrics_panel()
        self._clear_console()

    def _draw_drop_zone(self):
        c = self.drop_canvas
        c.delete("all")
        w = max(c.winfo_width(), 200)
        h = max(c.winfo_height(), 200)
        c.create_rectangle(6, 6, w - 6, h - 6, outline=theme.CYAN_DIM,
                            dash=(6, 4), width=2)
        icon = "\u2601" if self.mode == "compress" else "\U0001F4E4"
        c.create_text(w / 2, h / 2 - 40, text=icon, font=(theme.SANS, 30),
                      fill=theme.CYAN)
        if self.mode == "compress":
            main_text, sub_text = "Drop your file here", "Any file type - click to browse"
        else:
            main_text, sub_text = "Drop your .huf archive here", "Click to browse for a .huf file"
        c.create_text(w / 2, h / 2, text=main_text, font=(theme.SANS, 14, "bold"),
                      fill=theme.TEXT_PRIMARY)
        c.create_text(w / 2, h / 2 + 20, text=sub_text, font=(theme.SANS, 10),
                      fill=theme.TEXT_MUTED)

    # -- metrics panel --------------------------------------------------

    def _build_metrics_panel(self):
        for child in self.metrics_card.winfo_children():
            child.destroy()

        _section_label(self.metrics_card,
                       "COMPRESSION OUTPUT METRICS" if self.mode == "compress"
                       else "DECOMPRESSION OUTPUT").pack(anchor="w", padx=18, pady=(14, 10))

        body = ctk.CTkFrame(self.metrics_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18)
        body.grid_columnconfigure(0, weight=1)

        rows = ctk.CTkFrame(body, fg_color="transparent")
        rows.grid(row=0, column=0, sticky="nw")
        self.metric_labels = {}
        row_defs = (
            [("Original Size", "original"), ("Compressed Size", "compressed"),
             ("Savings Ratio", "ratio")] if self.mode == "compress" else
            [("Archive Size", "original"), ("Restored Size", "compressed"),
             ("Status", "ratio")]
        )
        for r, (label, key) in enumerate(row_defs):
            ctk.CTkLabel(rows, text=label, font=theme.font(11),
                         text_color=theme.TEXT_SECONDARY, anchor="w"
                         ).grid(row=r, column=0, sticky="w", pady=6)
            value_label = ctk.CTkLabel(rows, text="--", font=theme.font(12, "bold"),
                                        text_color=theme.TEXT_PRIMARY, anchor="e")
            value_label.grid(row=r, column=1, sticky="e", padx=(30, 0), pady=6)
            self.metric_labels[key] = value_label

        if self.mode == "compress":
            self.ring_canvas = tk.Canvas(body, width=150, height=150,
                                         bg=theme.CARD_BG, highlightthickness=0)
            self.ring_canvas.grid(row=0, column=1, padx=(20, 0), sticky="n")
            self._draw_ring(0)
        else:
            self.ring_canvas = None

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=1, column=0, columnspan=2, sticky="w", pady=(20, 10))
        self.save_as_btn = ctk.CTkButton(
            actions, text="Save output as...", fg_color=theme.CYAN,
            hover_color=theme.CYAN_HOVER, text_color="#04212b",
            font=theme.font(12, "bold"), state="disabled", command=self.save_output_as,
        )
        self.save_as_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Clear", fg_color="transparent",
                      border_width=1, border_color=theme.BORDER_LIGHT,
                      text_color=theme.TEXT_SECONDARY, font=theme.font(12),
                      command=self._reset_metrics).pack(side="left")

    def _reset_metrics(self):
        for key, lbl in self.metric_labels.items():
            lbl.configure(text="--")
        if self.ring_canvas is not None:
            self._draw_ring(0)
        self.save_as_btn.configure(state="disabled")
        self.last_result = None
        self._clear_console()

    def _clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _draw_ring(self, percent):
        c = self.ring_canvas
        c.delete("all")
        cx, cy, r, w = 75, 75, 58, 12
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=theme.BORDER_LIGHT, width=w)
        clipped = max(0.0, min(percent, 100.0))
        if clipped > 0:
            extent = -clipped * 3.6
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=extent,
                         style="arc", outline=theme.CYAN, width=w)
        c.create_text(cx, cy - 6, text=f"{percent:.1f}%", font=(theme.SANS, 17, "bold"),
                      fill=theme.TEXT_PRIMARY)
        c.create_text(cx, cy + 16, text="SPACE SAVED", font=(theme.SANS, 8, "bold"),
                      fill=theme.TEXT_SECONDARY)

    # -- console log --------------------------------------------------

    def _write_log(self, lines):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        for i, (tag, text) in enumerate(lines, start=1):
            self.console.insert("end", f"{i:02d}  ", "num")
            self.console.insert("end", text + "\n", tag)
        self.console.configure(state="disabled")
        self.console.see("end")

    # -- actions ------------------------------------------------------

    def browse_file(self):
        if self.mode == "compress":
            self._do_compress()
        else:
            self._do_decompress()

    def _do_compress(self):
        path = filedialog.askopenfilename(title="Select a file to compress")
        if not path:
            return
        try:
            result = zipper.compress_file(path)
        except Exception as exc:
            messagebox.showerror("Compression failed", str(exc))
            return
        self.last_result = result
        self.metric_labels["original"].configure(text=f"{result['original_size']:,} Bytes")
        self.metric_labels["compressed"].configure(
            text=f"{result['compressed_size']:,} Bytes", text_color=theme.GREEN)
        self.metric_labels["ratio"].configure(
            text=f"{result['ratio_percent']:.1f}% Efficiency", text_color=theme.CYAN)
        self._draw_ring(result["ratio_percent"])
        self.save_as_btn.configure(state="normal")

        freq_table = zipper.get_last_top_frequencies(None)
        self._write_log(console_log.compress_log_lines(
            os.path.basename(path), result["original_size"], freq_table,
            result["output_path"], result["compressed_size"], result["ratio_percent"],
        ))
        self.app.enable_tree_page(f"Compressed {os.path.basename(path)}")

    def _do_decompress(self):
        path = filedialog.askopenfilename(
            title="Select a .huf file to decompress",
            filetypes=(("Huffman archives", "*.huf"), ("all files", "*.*")),
        )
        if not path:
            return
        try:
            compressed_size = os.path.getsize(path)
            result = zipper.decompress_file(path)
        except Exception as exc:
            messagebox.showerror("Decompression failed", str(exc))
            return
        self.last_result = result
        self.metric_labels["original"].configure(text=f"{compressed_size:,} Bytes")
        self.metric_labels["compressed"].configure(
            text=f"{result['output_size']:,} Bytes", text_color=theme.GREEN)
        self.metric_labels["ratio"].configure(text="Restored", text_color=theme.GREEN)
        self.save_as_btn.configure(state="normal")

        self._write_log(console_log.decompress_log_lines(
            os.path.basename(path), compressed_size,
            leaf_count(zipper.get_last_tree()), result["output_path"], result["output_size"],
        ))
        self.app.enable_tree_page(f"Decompressed {os.path.basename(path)}")

    def save_output_as(self):
        if not self.last_result:
            return
        src = self.last_result["output_path"]
        default_name = os.path.basename(src)
        dest = filedialog.asksaveasfilename(initialfile=default_name)
        if not dest:
            return
        try:
            with open(src, "rb") as f_in, open(dest, "wb") as f_out:
                f_out.write(f_in.read())
        except OSError as exc:
            messagebox.showerror("Couldn't save file", str(exc))
            return
        messagebox.showinfo("Saved", f"Saved a copy to:\n{dest}")


# ---------------------------------------------------------------------------
# Tree Visualizer page
# ---------------------------------------------------------------------------

class TreePage(ctk.CTkFrame):
    AUTOPLAY_DELAY_MS = 900

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app
        self.steps = []
        self.index = 0
        self.playing = False
        self.final_root = None

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=30, pady=24)

        # -- header row ------------------------------------------------
        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(header, text="\U0001F333  Greedy Decision Tree Representation",
                     font=theme.font(16, "bold"), text_color=theme.TEXT_PRIMARY
                     ).pack(side="left")
        self.status_label = ctk.CTkLabel(header, text="No tree loaded yet",
                                          font=theme.font(11), text_color=theme.TEXT_MUTED)
        self.status_label.pack(side="right")

        # -- input controls ----------------------------------------------
        controls = _card(wrapper)
        controls.pack(fill="x", pady=(0, 12))
        row1 = ctk.CTkFrame(controls, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(row1, text="Custom example (symbol:freq, comma separated):",
                     font=theme.font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")

        row2 = ctk.CTkFrame(controls, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))
        self.entry = ctk.CTkEntry(row2, width=380, height=32,
                                   fg_color=theme.CARD_BG_LIGHT, border_color=theme.BORDER_LIGHT)
        self.entry.insert(0, TEXTBOOK_EXAMPLE)
        self.entry.pack(side="left", padx=(0, 6))
        ctk.CTkButton(row2, text="Build", width=90, height=32,
                      fg_color=theme.CYAN, hover_color=theme.CYAN_HOVER,
                      text_color="#04212b", font=theme.font(12, "bold"),
                      command=self.build_from_entry).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Textbook example", width=140, height=32,
                      fg_color=theme.CARD_BG_LIGHT, hover_color=theme.BORDER_LIGHT,
                      text_color=theme.TEXT_PRIMARY, font=theme.font(12),
                      command=self.load_textbook_example).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Visualize my last file", width=170, height=32,
                      fg_color=theme.CARD_BG_LIGHT, hover_color=theme.BORDER_LIGHT,
                      text_color=theme.TEXT_PRIMARY, font=theme.font(12),
                      command=self.build_from_last_file).pack(side="left", padx=4)

        # -- canvas -------------------------------------------------------
        self.canvas_frame, self.canvas = _scrollable_canvas(wrapper)
        self.canvas_frame.pack(fill="both", expand=True)

        # -- playback controls ----------------------------------------
        nav = ctk.CTkFrame(wrapper, fg_color="transparent")
        nav.pack(fill="x", pady=(10, 4))

        self.back_btn = ctk.CTkButton(nav, text="< Back", width=80, height=30,
                                       fg_color=theme.CARD_BG_LIGHT, hover_color=theme.BORDER_LIGHT,
                                       text_color=theme.TEXT_PRIMARY, state="disabled",
                                       command=self.go_back)
        self.back_btn.pack(side="left", padx=4)

        self.play_btn = ctk.CTkButton(nav, text="Play", width=80, height=30,
                                       fg_color=theme.CYAN_DIM, hover_color=theme.CYAN_HOVER,
                                       text_color=theme.TEXT_PRIMARY, state="disabled",
                                       command=self.toggle_play)
        self.play_btn.pack(side="left", padx=4)

        self.next_btn = ctk.CTkButton(nav, text="Next >", width=80, height=30,
                                       fg_color=theme.CARD_BG_LIGHT, hover_color=theme.BORDER_LIGHT,
                                       text_color=theme.TEXT_PRIMARY, state="disabled",
                                       command=self.go_next)
        self.next_btn.pack(side="left", padx=4)

        self.step_label = ctk.CTkLabel(nav, text="Step 0 of 0", width=100,
                                        font=theme.font(11), text_color=theme.TEXT_SECONDARY)
        self.step_label.pack(side="left", padx=(12, 6))

        self.slider = ctk.CTkSlider(nav, from_=0, to=1, number_of_steps=1, width=260,
                                     progress_color=theme.CYAN, button_color=theme.CYAN,
                                     button_hover_color=theme.CYAN_HOVER,
                                     command=self._on_slider, state="disabled")
        self.slider.set(0)
        self.slider.pack(side="left", padx=4)

        self.caption = ctk.CTkLabel(wrapper, text="Load an example above, or compress a "
                                                    "file on the previous page first.",
                                     font=theme.font(12), text_color=theme.TEXT_SECONDARY,
                                     wraplength=900)
        self.caption.pack(fill="x", pady=(6, 10))

        # -- codes table ----------------------------------------------
        table_wrap = _card(wrapper)
        table_wrap.pack(fill="x")
        _section_label(table_wrap, "RESULTING PREFIX CODES TABLE").pack(
            anchor="w", padx=16, pady=(12, 6))
        self.codes_frame = ctk.CTkFrame(table_wrap, fg_color="transparent")
        self.codes_frame.pack(fill="x", padx=16, pady=(0, 14))

    def on_show(self):
        pass  # nav bar calls this; nothing extra needed on tab switch

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
                "Use the format symbol:freq, separated by commas - e.g. A:7,B:9,C:11",
            )
            return
        if not freq_table:
            messagebox.showerror("Nothing to build", "Type at least one symbol:freq pair.")
            return
        self._build(freq_table, "custom example")

    def build_from_last_file(self):
        freq_table = zipper.get_last_top_frequencies(limit=12)
        if not freq_table:
            messagebox.showinfo(
                "No file yet",
                "Compress a file first, on the Compress / Decompress page, then "
                "come back and click this again.",
            )
            return
        source = zipper._last_source_label or "the last file"
        self._build(freq_table, f"top {len(freq_table)} bytes of {source}")

    def _build(self, freq_table, status_text):
        self.playing = False
        self.play_btn.configure(text="Play")
        self.final_root, self.steps = build_with_steps(freq_table)
        self.index = len(self.steps) - 1  # default to the fully-built tree

        self.back_btn.configure(state="normal")
        self.next_btn.configure(state="normal")
        self.play_btn.configure(state="normal")
        self.slider.configure(state="normal", from_=0, to=max(len(self.steps) - 1, 1),
                               number_of_steps=max(len(self.steps) - 1, 1))
        self.status_label.configure(text=f"Showing: {status_text}", text_color=theme.CYAN)
        self._render()
        self._render_codes_table()

    def _render_codes_table(self):
        for child in self.codes_frame.winfo_children():
            child.destroy()
        if self.final_root is None:
            return
        codes = build_codes(self.final_root)
        items = sorted(codes.items(), key=lambda kv: kv[1])
        per_row = 6
        for i, (symbol, code) in enumerate(items):
            r, c = divmod(i, per_row)
            pill = ctk.CTkLabel(
                self.codes_frame, text=f"  {symbol} = {code}  ",
                font=(theme.MONO, 11, "bold"), text_color=theme.GREEN,
                fg_color=theme.CARD_BG_LIGHT, corner_radius=8,
            )
            pill.grid(row=r, column=c, padx=4, pady=4, sticky="w")

    # -- navigation ------------------------------------------------------

    def go_next(self):
        if self.index < len(self.steps) - 1:
            self.index += 1
            self._render()
        else:
            self.playing = False
            self.play_btn.configure(text="Play")

    def go_back(self):
        self.playing = False
        self.play_btn.configure(text="Play")
        if self.index > 0:
            self.index -= 1
            self._render()

    def _on_slider(self, value):
        self.playing = False
        self.play_btn.configure(text="Play")
        self.index = int(round(value))
        self._render()

    def toggle_play(self):
        if not self.steps:
            return
        self.playing = not self.playing
        self.play_btn.configure(text="Pause" if self.playing else "Play")
        if self.playing:
            if self.index >= len(self.steps) - 1:
                self.index = 0
                self._render()
            self._auto_step()

    def _auto_step(self):
        if not self.playing or not self.winfo_exists():
            return
        if self.index < len(self.steps) - 1:
            self.index += 1
            self._render()
            self.after(self.AUTOPLAY_DELAY_MS, self._auto_step)
        else:
            self.playing = False
            self.play_btn.configure(text="Play")

    def _render(self):
        if not self.steps:
            return
        step = self.steps[self.index]
        draw_forest(self.canvas, step["forest"], step["merged"], show_edge_labels=True)

        self.step_label.configure(text=f"Step {self.index} of {len(self.steps) - 1}")
        self.back_btn.configure(state=("normal" if self.index > 0 else "disabled"))
        self.next_btn.configure(state=("normal" if self.index < len(self.steps) - 1 else "disabled"))
        self.slider.set(self.index)

        merged = step["merged"]
        if merged is None:
            self.caption.configure(
                text=f"Starting forest: {len(step['forest'])} nodes, none merged yet.")
        elif self.index == len(self.steps) - 1:
            self.caption.configure(
                text="Fully built tree. Rewind with Back or the slider to replay "
                     "how it was constructed, merge by merge.")
        else:
            left, right = merged.left, merged.right
            left_label = left.symbol if left.is_leaf() else f"a node (freq {left.freq})"
            right_label = right.symbol if right.is_leaf() else f"a node (freq {right.freq})"
            self.caption.configure(
                text=f"Merged '{left_label}' (freq {left.freq}) and '{right_label}' "
                     f"(freq {right.freq}) into a new node (freq {merged.freq}).")


# ---------------------------------------------------------------------------
# Main app: nav bar + page switching
# ---------------------------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Huffman Studio")
        self.geometry("1200x820")
        self.minsize(960, 680)
        self.configure(fg_color=theme.BG)

        self.nav_buttons = {}
        self._build_navbar()

        container = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        for name, PageClass in [("dashboard", DashboardPage),
                                 ("compress", CompressPage),
                                 ("tree", TreePage)]:
            page = PageClass(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self.show_page("dashboard")

    def _build_navbar(self):
        nav = ctk.CTkFrame(self, fg_color=theme.CARD_BG, height=58, corner_radius=0)
        nav.pack(fill="x", side="top")
        nav.pack_propagate(False)

        brand_badge = ctk.CTkLabel(nav, text="H", font=theme.font(15, "bold"),
                                    text_color="white", fg_color=theme.PURPLE,
                                    corner_radius=8, width=34, height=34)
        brand_badge.pack(side="left", padx=(20, 8), pady=12)

        ctk.CTkLabel(nav, text="HUFFMAN STUDIO", font=theme.font(14, "bold"),
                     text_color=theme.TEXT_PRIMARY).pack(side="left", padx=(0, 30))

        tabs_frame = ctk.CTkFrame(nav, fg_color="transparent")
        tabs_frame.pack(side="left")
        for key, label in [("dashboard", "Dashboard"),
                            ("compress", "Compress / Decompress"),
                            ("tree", "Tree Visualizer")]:
            btn = ctk.CTkButton(
                tabs_frame, text=label, fg_color="transparent",
                hover_color=theme.CARD_BG_LIGHT, text_color=theme.TEXT_SECONDARY,
                font=theme.font(12, "bold"), corner_radius=8, height=34,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(side="left", padx=4)
            self.nav_buttons[key] = btn

    def show_page(self, name):
        for key, btn in self.nav_buttons.items():
            active = key == name
            btn.configure(text_color=theme.CYAN if active else theme.TEXT_SECONDARY,
                          fg_color=theme.CARD_BG_LIGHT if active else "transparent")
        self.pages[name].tkraise()
        on_show = getattr(self.pages[name], "on_show", None)
        if on_show:
            on_show()

    def enable_tree_page(self, status_text):
        """Called after a compress/decompress so the Tree page's status
        hint reflects that a real tree is now available, without forcing
        a switch to that tab."""
        self.pages["tree"].status_label.configure(
            text=f"Ready: {status_text} (use 'Visualize my last file')",
            text_color=theme.TEXT_MUTED,
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
