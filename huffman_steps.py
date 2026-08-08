"""
Step-by-step Huffman tree construction, for the GUI's "How Huffman Works"
visualizer. This is deliberately a SEPARATE build function from
huffman_tree.build_huffman_tree() (which uses the min-heap and is what
actually runs during real compression) - this one uses the classic
"two queue" method instead, because it's the one that naturally produces
the row-of-boxes merge order you'd see in a textbook walkthrough:

  Q1: the original leaves, sorted ascending by frequency (a plain list
      acting as a queue)
  Q2: the internal (merged) nodes created so far, oldest first

At every step, the two smallest available nodes - comparing only the
FRONT of each queue - are removed and merged into a new internal node,
which is appended to the back of Q2. Because Q1 starts sorted and every
new node appended to Q2 is the sum of the two smallest values still
available, Q2 stays sorted automatically, with no re-sorting needed.
This is a standard O(n log n) (just the initial sort) Huffman
construction technique, and it's what makes the "forest" at each step
display cleanly as [merged nodes in creation order] + [remaining leaves
in original order] - exactly like a textbook example.
"""

from collections import deque

from huffman_tree import Node


def build_with_steps(freq_table: dict):
    """
    Returns (root_node, steps).

    steps is a list of dicts, one per snapshot:
        {"forest": [Node, ...], "merged": Node or None}

    forest is the ordered list of surviving top-level nodes at that point
    (what should be drawn as the "row of boxes"). merged is the node that
    was just created in that step (None for the very first snapshot,
    which shows the starting leaves before any merging happens).
    """
    if not freq_table:
        return None, []

    leaves = [Node(symbol=s, freq=f) for s, f in freq_table.items()]
    leaves.sort(key=lambda n: n.freq)

    q1 = deque(leaves)  # original leaves, ascending
    q2 = deque()        # merged/internal nodes, stays ascending automatically

    def pop_smallest():
        if q1 and (not q2 or q1[0].freq <= q2[0].freq):
            return q1.popleft()
        return q2.popleft()

    steps = [{"forest": list(q1), "merged": None}]

    # Edge case: only one unique symbol - same fix as build_huffman_tree(),
    # a lone leaf can't become the root by itself (it would get an empty
    # code), so it's wrapped under one dummy parent.
    if len(leaves) == 1:
        only = q1.popleft()
        wrapped = Node(symbol=None, freq=only.freq, left=only)
        q2.append(wrapped)
        steps.append({"forest": list(q2) + list(q1), "merged": wrapped})

    while len(q1) + len(q2) > 1:
        n1 = pop_smallest()
        n2 = pop_smallest()
        merged = Node(symbol=None, freq=n1.freq + n2.freq, left=n1, right=n2)
        q2.append(merged)
        steps.append({"forest": list(q2) + list(q1), "merged": merged})

    root = q2[0] if q2 else q1[0]
    return root, steps
