"""
Minimum binary heap (priority queue), implemented as a plain Python list.

This is your original heaps.py - the shift_up / shift_down logic was
already correct, so the algorithm itself is untouched. Comments are added
below to explain *why* it works, since this heap is what makes Huffman
tree construction efficient: without it, finding the two least-frequent
nodes at every step would cost O(n) instead of O(log n).

Array representation of a binary tree:
    - the root lives at index 0
    - for any node at index i:
        left child  -> index 2*i + 1
        right child -> index 2*i + 2
        parent      -> index (i - 1) // 2
"""


def swap(heapqueue, i, j):
    """Swap two elements in the heap list - used to restore the heap
    invariant after an insert or removal."""
    heapqueue[i], heapqueue[j] = heapqueue[j], heapqueue[i]


def shift_up(heapqueue, i):
    """
    Move the element at index i upward until its parent is <= it (or it
    reaches the root at index 0). Called right after appending a new
    element to the end of the list (see heappush) - the new element may
    be smaller than its ancestors, so it has to "bubble up".
    """
    while i > 0 and heapqueue[i] < heapqueue[(i - 1) // 2]:
        swap(heapqueue, i, (i - 1) // 2)
        i = (i - 1) // 2


def shift_down(heapqueue, i):
    """
    Move the element at index i downward, always swapping with its
    smaller child, until both children are >= it (or it has no children
    left). Called after moving the last element into the root position
    (see heappop) - it's very likely too big to stay at the root.
    """
    while 2 * i + 1 < len(heapqueue):
        left = 2 * i + 1
        # if there's no right child, treat left as both, so the
        # comparison below always ends up picking `left`
        right = left + 1 if left + 1 < len(heapqueue) else left
        smaller = left if heapqueue[left] < heapqueue[right] else right
        if heapqueue[i] < heapqueue[smaller]:
            break
        swap(heapqueue, i, smaller)
        i = smaller


def heappush(heapqueue, item):
    """Insert item at the end, then shift it up to restore the heap
    invariant. O(log n)."""
    heapqueue.append(item)
    shift_up(heapqueue, len(heapqueue) - 1)


def heappop(heapqueue):
    """
    Remove and return the smallest item (always the root, index 0).
    The last item is moved into the root's place first, then shifted
    down - this keeps the whole operation O(log n) instead of O(n).
    """
    if not heapqueue:
        return None
    swap(heapqueue, 0, len(heapqueue) - 1)
    item = heapqueue.pop()
    shift_down(heapqueue, 0)
    return item
