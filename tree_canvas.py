"""
Shared Canvas drawing code for the tree/step visualizer on the Tree
Visualizer page. Colors and fonts come from theme.py so this stays
visually consistent with the rest of the app.
"""

import theme

# --- Layout Constants ---
LEAF_W = 140
LEVEL_H = 120       # Reduced from 130 so branch lines aren't flat
TOP_MARGIN = 50

LEAF_HALF_W, LEAF_HALF_H = 50, 44  # Reduced box height to avoid text clipping
NODE_RADIUS = 40                   # Reduced circle size from 50 to 28
EDGE_LABEL_RADIUS = 20              # Scaled down label badges


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
    # --- 1. LEAF NODE RENDERING ---
    if node.is_leaf():
        # Outer card box
        canvas.create_rectangle(
            x - LEAF_HALF_W, y - LEAF_HALF_H, 
            x + LEAF_HALF_W, y + LEAF_HALF_H,
            fill=theme.CARD_BG_LIGHT, 
            outline=theme.CYAN, 
            width=2,
        )
        # Symbol label (Shifted higher to prevent overlapping)
        canvas.create_text(
            x, y - 20, 
            text=format_label(node.symbol),
            font=theme.canvas_font(10, "bold"), 
            fill=theme.TEXT_PRIMARY
        )
        # Frequency label (Shifted lower with clean spacing)
        canvas.create_text(
            x, y + 15, 
            text=f"f: {node.freq}",
            font=theme.canvas_font(9), 
            fill=theme.CYAN
        )
        return

    # --- 2. INTERNAL NODE RENDERING ---
    fill = theme.CARD_BG_LIGHT
    outline = theme.GREEN if highlight else theme.PURPLE
    text_color = theme.GREEN if highlight else theme.TEXT_PRIMARY
    ring_width = 3 if highlight else 2
    r = NODE_RADIUS

    canvas.create_oval(
        x - r, y - r, x + r, y + r,
        fill=fill, outline=outline, width=ring_width
    )
    canvas.create_text(
        x, y, 
        text=str(node.freq), 
        font=theme.canvas_font(12, "bold"),
        fill=text_color
    )
    
    if highlight:
        canvas.create_text(
            x, y - r - 14, 
            text="merged",
            font=theme.canvas_font(5, "italic"), 
            fill=theme.GREEN
        )

    # --- 3. CHILD BRANCHES & RECURSION ---
    children = [(bit, c) for bit, c in (("0", node.left), ("1", node.right)) if c is not None]
    counts = [leaf_count(c) for _, c in children]
    total = sum(counts) or 1
    start_x = x - unit_w / 2
    cursor = 0.0

    for (bit, child), count in zip(children, counts):
        child_w = unit_w * (count / total)
        child_x = start_x + cursor + child_w / 2
        
        # Calculate line endpoints dynamically based on target node shape
        top_y = y + r
        child_offset = LEAF_HALF_H if child.is_leaf() else NODE_RADIUS
        bottom_y = y + LEVEL_H - child_offset

        # Branch connection line
        canvas.create_line(x, top_y, child_x, bottom_y, fill=theme.BORDER_LIGHT, width=3)

        # Edge direction badges ('0' / '1')
        if show_edge_labels:
            mid_x, mid_y = (x + child_x) / 2, (top_y + bottom_y) / 2
            label_color = theme.CYAN if bit == "0" else theme.GREEN
            lr = EDGE_LABEL_RADIUS
            canvas.create_oval(
                mid_x - lr, mid_y - lr, mid_x + lr, mid_y + lr,
                fill=theme.BG, outline=theme.BORDER_LIGHT
            )
            canvas.create_text(
                mid_x, mid_y, text=bit,
                font=theme.canvas_font(10, "bold"), fill=label_color
            )

        # Recursive call
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
    total_width = max(sum(counts) * LEAF_W, 500)
    max_depth = max((tree_depth(n) for n in forest), default=1)
    total_height = TOP_MARGIN + max_depth * LEVEL_H + 40
    canvas.configure(scrollregion=(0, 0, total_width, total_height))

    x = 30
    for node, count in zip(forest, counts):
        w = count * LEAF_W
        center = x + w / 2
        _draw_node(canvas, node, center, TOP_MARGIN, w, node is merged_node, show_edge_labels)
        x += w

    return total_width, total_height