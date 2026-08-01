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
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from huffman_compressor import HuffmanZipper

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

zipper = HuffmanZipper()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Huffman File Zipper")
        self.geometry("480x360")
        self.resizable(False, False)

        title = ctk.CTkLabel(
            self, text="Huffman File Zipper",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(30, 5))

        subtitle = ctk.CTkLabel(
            self,
            text="Compress any file using a Huffman binary tree,\n"
                 "or restore one from a .huf archive.",
            font=ctk.CTkFont(size=13),
            justify="center",
        )
        subtitle.pack(pady=(0, 25))

        ctk.CTkButton(
            self, text="Compress a file", width=220, height=45,
            command=self.compress_file,
        ).pack(pady=8)

        ctk.CTkButton(
            self, text="Decompress a .huf file", width=220, height=45,
            command=self.decompress_file,
        ).pack(pady=8)

        self.theme_switch = ctk.CTkSwitch(
            self, text="Dark mode", command=self.toggle_theme,
        )
        self.theme_switch.pack(pady=(25, 0))

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")

    def compress_file(self):
        path = filedialog.askopenfilename(title="Select a file to compress")
        if not path:
            return
        try:
            result = zipper.compress_file(path)
        except Exception as exc:
            messagebox.showerror("Compression failed", str(exc))
            return
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
            return
        messagebox.showinfo(
            "Decompression complete",
            "Saved to:\n{}\n\nSize: {:,} bytes".format(
                result["output_path"], result["output_size"],
            ),
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
