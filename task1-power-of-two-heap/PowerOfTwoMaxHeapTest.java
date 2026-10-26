import java.util.Collections;
import java.util.NoSuchElementException;
import java.util.PriorityQueue;
import java.util.Random;

/** Run with: javac *.java && java PowerOfTwoMaxHeapTest */
public class PowerOfTwoMaxHeapTest {

    private static final int[] EXPONENTS = {0, 1, 2, 3, 4, 5, 8, 10, 16, 20, 30, 31, 32, 63, 1000, Integer.MAX_VALUE};
    private static int checks = 0;

    public static void main(String[] args) {
        testInvalidExponent();
        testEmptyHeap();
        for (int exponent : EXPONENTS) {
            testSingleElement(exponent);
            testDuplicates(exponent);
            testExtremeValues(exponent);
            testSortedInputs(exponent);
            testRandomAgainstPriorityQueue(exponent, 5_000, 42L + exponent);
            testInterleavedOps(exponent, 20_000, 7L + exponent);
            testRefillAfterEmpty(exponent);
        }
        testZeroInitialCapacity();
        benchmark();
        System.out.println("All " + checks + " checks passed.");
    }

    // ---------------------------------------------------------------- edge cases

    static void testInvalidExponent() {
        expectThrows(IllegalArgumentException.class, () -> new PowerOfTwoMaxHeap(-1));
        expectThrows(IllegalArgumentException.class, () -> new PowerOfTwoMaxHeap(Integer.MIN_VALUE));
        expectThrows(IllegalArgumentException.class, () -> new PowerOfTwoMaxHeap(2, -5));
    }

    static void testEmptyHeap() {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(2);
        check(heap.isEmpty() && heap.size() == 0, "new heap is empty");
        expectThrows(NoSuchElementException.class, heap::popMax);
        expectThrows(NoSuchElementException.class, heap::peekMax);
    }

    static void testSingleElement(int exponent) {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        heap.insert(7);
        check(heap.peekMax() == 7, "peek single");
        check(heap.popMax() == 7, "pop single");
        check(heap.isEmpty(), "empty after single pop");
        expectThrows(NoSuchElementException.class, heap::popMax);
    }

    static void testDuplicates(int exponent) {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        for (int i = 0; i < 100; i++) heap.insert(5);
        heap.insert(9);
        heap.insert(5);
        check(heap.popMax() == 9, "max among duplicates");
        for (int i = 0; i < 101; i++) check(heap.popMax() == 5, "duplicate value");
        check(heap.isEmpty(), "empty after duplicates");
    }

    static void testExtremeValues(int exponent) {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        int[] values = {0, Integer.MIN_VALUE, Integer.MAX_VALUE, -1, 1, Integer.MAX_VALUE, Integer.MIN_VALUE};
        for (int v : values) heap.insert(v);
        int[] expected = {Integer.MAX_VALUE, Integer.MAX_VALUE, 1, 0, -1, Integer.MIN_VALUE, Integer.MIN_VALUE};
        for (int e : expected) check(heap.popMax() == e, "extreme values order");
    }

    static void testSortedInputs(int exponent) {
        PowerOfTwoMaxHeap ascending = new PowerOfTwoMaxHeap(exponent);
        PowerOfTwoMaxHeap descending = new PowerOfTwoMaxHeap(exponent);
        int n = 2_000;
        for (int i = 0; i < n; i++) {
            ascending.insert(i);
            descending.insert(n - 1 - i);
        }
        for (int i = n - 1; i >= 0; i--) {
            check(ascending.popMax() == i, "ascending input");
            check(descending.popMax() == i, "descending input");
        }
    }

    static void testRandomAgainstPriorityQueue(int exponent, int count, long seed) {
        Random random = new Random(seed);
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        PriorityQueue<Integer> reference = new PriorityQueue<>(Collections.reverseOrder());
        for (int i = 0; i < count; i++) {
            int v = random.nextInt();
            heap.insert(v);
            reference.add(v);
        }
        while (!reference.isEmpty()) {
            check(heap.popMax() == reference.poll(), "random order, exponent " + exponent);
        }
        check(heap.isEmpty(), "drained");
    }

    static void testInterleavedOps(int exponent, int ops, long seed) {
        Random random = new Random(seed);
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        PriorityQueue<Integer> reference = new PriorityQueue<>(Collections.reverseOrder());
        for (int i = 0; i < ops; i++) {
            if (reference.isEmpty() || random.nextInt(3) != 0) {
                int v = random.nextInt(1000) - 500; // narrow range => many duplicates
                heap.insert(v);
                reference.add(v);
            } else {
                check(heap.popMax() == reference.poll(), "interleaved, exponent " + exponent);
            }
            check(heap.size() == reference.size(), "size tracks");
        }
    }

    static void testRefillAfterEmpty(int exponent) {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent);
        for (int round = 0; round < 3; round++) {
            for (int i = 0; i < 50; i++) heap.insert(i * 3 % 17);
            int previous = Integer.MAX_VALUE;
            while (!heap.isEmpty()) {
                int v = heap.popMax();
                check(v <= previous, "non-increasing after refill");
                previous = v;
            }
        }
    }

    static void testZeroInitialCapacity() {
        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(1, 0);
        for (int i = 0; i < 1000; i++) heap.insert(i);
        check(heap.popMax() == 999, "grows from zero capacity");
    }

    // ---------------------------------------------------------------- benchmark

    static void benchmark() {
        int n = 2_000_000;
        int[] data = new Random(1).ints(n).toArray();
        System.out.println("Benchmark: " + n + " inserts then " + n + " pops");
        for (int exponent : new int[]{0, 1, 2, 3, 4, 6, 8}) {
            if (exponent == 0) {
                System.out.printf("  2^0  (1 child)  : skipped - O(N) per op, degenerates to a chain%n");
                continue;
            }
            PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent, n);
            long start = System.nanoTime();
            for (int v : data) heap.insert(v);
            long mid = System.nanoTime();
            long sink = 0;
            while (!heap.isEmpty()) sink += heap.popMax();
            long end = System.nanoTime();
            System.out.printf("  2^%-2d (%3d kids) : insert %5d ms, popMax %5d ms  (%d)%n",
                    exponent, 1 << exponent, (mid - start) / 1_000_000, (end - mid) / 1_000_000, sink & 1);
        }
    }

    // ---------------------------------------------------------------- helpers

    static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError("FAILED: " + message);
    }

    static void expectThrows(Class<? extends Throwable> type, Runnable action) {
        checks++;
        try {
            action.run();
        } catch (Throwable t) {
            if (type.isInstance(t)) return;
            throw new AssertionError("Expected " + type.getSimpleName() + " but got " + t);
        }
        throw new AssertionError("Expected " + type.getSimpleName() + " but nothing was thrown");
    }
}
