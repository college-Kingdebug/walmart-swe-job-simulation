import java.util.Arrays;
import java.util.NoSuchElementException;

/**
 * A max heap in which every parent node has 2^childrenExponent children.
 *
 * Layout: a flat, 0-indexed int array (no boxing, no per-node objects).
 * With n = 2^childrenExponent children per node:
 *   parent(i)     = (i - 1) / n   ==  (i - 1) >>> childrenExponent
 *   firstChild(i) = n * i + 1     ==  (i << childrenExponent) + 1
 * Because n is a power of two, all index math is done with bit shifts.
 *
 * Complexity (N = size, n = children per node):
 *   insert : O(log_n N)      - shallower tree => faster as the exponent grows
 *   popMax : O(n * log_n N)  - each level scans up to n children
 */
public class PowerOfTwoMaxHeap {

    private static final int DEFAULT_CAPACITY = 16;
    // Some JVMs reserve header words in arrays; this is the safe maximum length.
    private static final int MAX_CAPACITY = Integer.MAX_VALUE - 8;

    /**
     * Exponents of 31 or more all behave identically: no array index can ever
     * reach a second level, so every element is a direct child of the root.
     * Clamping keeps the shifts valid (Java masks int shift counts to 5 bits,
     * so shifting by 32 or more would silently produce wrong results).
     */
    private static final int MAX_EFFECTIVE_EXPONENT = 31;

    private final int childrenExponent;   // effective (clamped) exponent
    private final long childrenPerNode;   // 2^childrenExponent, long so 2^31 fits

    private int[] heap;
    private int size;

    /**
     * @param childrenExponent each parent has 2^childrenExponent children; must be >= 0.
     *                         0 = 1 child (a sorted chain), 1 = binary heap, 2 = 4-ary, ...
     */
    public PowerOfTwoMaxHeap(int childrenExponent) {
        this(childrenExponent, DEFAULT_CAPACITY);
    }

    /**
     * @param initialCapacity pre-size the backing array to avoid resizes when the
     *                        expected number of elements is known.
     */
    public PowerOfTwoMaxHeap(int childrenExponent, int initialCapacity) {
        if (childrenExponent < 0) {
            throw new IllegalArgumentException(
                    "childrenExponent must be non-negative, got " + childrenExponent);
        }
        if (initialCapacity < 0 || initialCapacity > MAX_CAPACITY) {
            throw new IllegalArgumentException("Invalid initial capacity: " + initialCapacity);
        }
        this.childrenExponent = Math.min(childrenExponent, MAX_EFFECTIVE_EXPONENT);
        this.childrenPerNode = 1L << this.childrenExponent;
        this.heap = new int[Math.max(initialCapacity, 1)];
        this.size = 0;
    }

    /** Inserts a value, then sifts it up until the heap property holds. */
    public void insert(int value) {
        if (size == heap.length) {
            grow();
        }
        // "Hole" technique: move parents down into the hole instead of swapping,
        // then write the new value once at its final position.
        int hole = size++;
        while (hole > 0) {
            int parent = (hole - 1) >>> childrenExponent;
            int parentValue = heap[parent];
            if (value <= parentValue) {
                break;
            }
            heap[hole] = parentValue;
            hole = parent;
        }
        heap[hole] = value;
    }

    /** Removes and returns the maximum value. */
    public int popMax() {
        if (size == 0) {
            throw new NoSuchElementException("popMax called on an empty heap");
        }
        int max = heap[0];
        int last = heap[--size];
        if (size > 0) {
            siftDown(last);
        }
        return max;
    }

    /** Returns the maximum value without removing it. */
    public int peekMax() {
        if (size == 0) {
            throw new NoSuchElementException("peekMax called on an empty heap");
        }
        return heap[0];
    }

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }

    public int getChildrenExponent() {
        return childrenExponent;
    }

    // ------------------------------------------------------------------ internals

    /** Places {@code value} starting at the root and moves it down to its spot. */
    private void siftDown(int value) {
        int hole = 0;
        while (true) {
            // long arithmetic: (hole << 31) or (first + 2^31) would overflow an int.
            long first = ((long) hole << childrenExponent) + 1;
            if (first >= size) {
                break; // hole is a leaf
            }
            int end = (int) Math.min(first + childrenPerNode, size);

            // Find the largest child in [first, end).
            int maxChild = (int) first;
            int maxValue = heap[maxChild];
            for (int child = maxChild + 1; child < end; child++) {
                int childValue = heap[child];
                if (childValue > maxValue) {
                    maxValue = childValue;
                    maxChild = child;
                }
            }

            if (maxValue <= value) {
                break;
            }
            heap[hole] = maxValue;
            hole = maxChild;
        }
        heap[hole] = value;
    }

    /** Grows the backing array by ~1.5x, without overflowing past MAX_CAPACITY. */
    private void grow() {
        int oldCapacity = heap.length;
        if (oldCapacity >= MAX_CAPACITY) {
            throw new IllegalStateException("Heap is at maximum capacity");
        }
        long target = (long) oldCapacity + (oldCapacity >> 1) + 1;
        int newCapacity = (int) Math.min(target, MAX_CAPACITY);
        heap = Arrays.copyOf(heap, newCapacity);
    }
}
