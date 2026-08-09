"""
Shared Canvas drawing code for the tree/step visualizer on the Tree
Visualizer page. Colors and fonts come from theme.py so this stays
visually consistent with the rest of the app rather than picking its
own palette.
"""

import theme

LEAF_W = 84
LEVEL_H = 92
TOP_MARGIN = 40


def format_label(symbol) -> str:
    """A byte value (int, from a real compressed file) or a custom
    example's symbol (str, already printable) -> a short display label."""
    if isinstance(symbol, int):
        return chr(symbol) if 32 <= symbol <= 126 else f"0x{symbol:02x}"
    return str(symbol)


def leaf_count(node) -> int:
    if node.is_leaf():
        return 1
    left = leaf_count(node.left) if node.left else 0
    right = leaf_count(node.right) if node.right else 0
    return max(left + right, 1)


def tree_depth(node) -> int:
    if node.is_leaf():
        return 1
    depths = [tree_depth(c) for c in (node.left, node.right) if c is not None]
    return 1 + (max(depths) if depths else 0)


def _draw_node(canvas, node, x, y, unit_w, highlight, show_edge_labels):
    if node.is_leaf():
        canvas.create_rectangle(
            x - 29, y - 19, x + 29, y + 19,
            fill=theme.CARD_BG_LIGHT, outline=theme.CYAN, width=2,
        )
        canvas.create_text(x, y - 5, text=format_label(node.symbol),
                            font=(theme.SANS, 12, "bold"), fill=theme.TEXT_PRIMARY)
        canvas.create_text(x, y + 10, text=str(node.freq),
                            font=(theme.SANS, 8), fill=theme.TEXT_MUTED)
        return

    fill = theme.CARD_BG_LIGHT
    outline = theme.GREEN if highlight else theme.PURPLE
    text_color = theme.GREEN if highlight else theme.TEXT_PRIMARY
    ring_width = 3 if highlight else 2
    canvas.create_oval(x - 24, y - 24, x + 24, y + 24,
                        fill=fill, outline=outline, width=ring_width)
    canvas.create_text(x, y, text=str(node.freq), font=(theme.SANS, 10, "bold"),
                        fill=text_color)
    if highlight:
        canvas.create_text(x, y - 36, text="merged",
                            font=(theme.SANS, 8, "italic"), fill=theme.GREEN)

    children = [(bit, c) for bit, c in (("0", node.left), ("1", node.right)) if c is not None]
    counts = [leaf_count(c) for _, c in children]
    total = sum(counts) or 1
    start_x = x - unit_w / 2
    cursor = 0.0
    for (bit, child), count in zip(children, counts):
        child_w = unit_w * (count / total)
        child_x = start_x + cursor + child_w / 2
        top_y, bottom_y = y + 24, y + LEVEL_H - 20
        canvas.create_line(x, top_y, child_x, bottom_y, fill=theme.BORDER_LIGHT, width=2)
        if show_edge_labels:
            mid_x, mid_y = (x + child_x) / 2, (top_y + bottom_y) / 2
            label_color = theme.CYAN if bit == "0" else theme.GREEN
            canvas.create_oval(mid_x - 9, mid_y - 9, mid_x + 9, mid_y + 9,
                                fill=theme.BG, outline=theme.BORDER_LIGHT)
            canvas.create_text(mid_x, mid_y, text=bit,
                                font=(theme.SANS, 8, "bold"), fill=label_color)
        _draw_node(canvas, child, child_x, y + LEVEL_H, child_w, False, show_edge_labels)
        cursor += child_w


def draw_forest(canvas, forest, merged_node=None, show_edge_labels=True):
    """
    Draw a left-to-right row of (sub)trees onto a tkinter Canvas.
    Pass forest=[root] to draw a single complete tree. `merged_node`, if
    given, gets a highlighted ring (used by the step visualizer to show
    which node was just created). Returns (width, height) so callers can
    size the canvas's scroll region.
    """
    canvas.delete("all")
    canvas.configure(bg=theme.BG)
    if not forest:
        return 0, 0

    counts = [leaf_count(n) for n in forest]
    total_width = max(sum(counts) * LEAF_W, 400)
    max_depth = max((tree_depth(n) for n in forest), default=1)
    total_height = TOP_MARGIN + max_depth * LEVEL_H + 30
    canvas.configure(scrollregion=(0, 0, total_width, total_height))

    x = 20
    for node, count in zip(forest, counts):
        w = count * LEAF_W
        center = x + w / 2
        _draw_node(canvas, node, center, TOP_MARGIN, w, node is merged_node, show_edge_labels)
        x += w

    return total_width, total_height
