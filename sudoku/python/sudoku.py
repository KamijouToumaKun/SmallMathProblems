"""Sudoku solver: constraint propagation + backtracking.

Techniques:
  - Naked / hidden singles
  - Naked pairs & triples
  - Hidden pairs & triples
  - Pointing pairs / box-line reduction (claiming)
  - X-Wing
  - Search: MRV + degree heuristic, LCV value order
"""

from __future__ import annotations

import argparse
import json
import time
from itertools import combinations
from pathlib import Path
from typing import Iterator, Optional


BoxId = int  # 0..8
Digit = int  # 1..9


def box_of(r: int, c: int) -> BoxId:
    return (r // 3) * 3 + (c // 3)


def box_cells(b: BoxId) -> Iterator[tuple[int, int]]:
    br, bc = divmod(b, 3)
    for i in range(br * 3, br * 3 + 3):
        for j in range(bc * 3, bc * 3 + 3):
            yield i, j


def _all_units() -> list[list[tuple[int, int]]]:
    units: list[list[tuple[int, int]]] = []
    for r in range(9):
        units.append([(r, c) for c in range(9)])
    for c in range(9):
        units.append([(r, c) for r in range(9)])
    for b in range(9):
        units.append(list(box_cells(b)))
    return units


UNITS = _all_units()


class Sudoku:
    def __init__(self, grid: list[list[int]]) -> None:
        # value[r][c]: 0 empty, else 1..9
        self.value = [row[:] for row in grid]
        # candidates[r][c]: set of possible digits for empty cells
        self.candidates: list[list[Optional[set[Digit]]]] = [
            [None] * 9 for _ in range(9)
        ]
        self._init_candidates()

    def _init_candidates(self) -> None:
        for r in range(9):
            for c in range(9):
                if self.value[r][c]:
                    self.candidates[r][c] = None
                else:
                    used: set[Digit] = set()
                    for k in range(9):
                        if self.value[r][k]:
                            used.add(self.value[r][k])
                        if self.value[k][c]:
                            used.add(self.value[k][c])
                    for i, j in box_cells(box_of(r, c)):
                        if self.value[i][j]:
                            used.add(self.value[i][j])
                    self.candidates[r][c] = set(range(1, 10)) - used

    def clone(self) -> Sudoku:
        other = Sudoku.__new__(Sudoku)
        other.value = [row[:] for row in self.value]
        other.candidates = [
            [None if s is None else set(s) for s in row] for row in self.candidates
        ]
        return other

    def place(self, r: int, c: int, n: Digit) -> None:
        """Fill (r, c) with n and eliminate n from peers."""
        self.value[r][c] = n
        self.candidates[r][c] = None
        for k in range(9):
            if self.candidates[r][k] is not None:
                self.candidates[r][k].discard(n)
            if self.candidates[k][c] is not None:
                self.candidates[k][c].discard(n)
        for i, j in box_cells(box_of(r, c)):
            if self.candidates[i][j] is not None:
                self.candidates[i][j].discard(n)

    def is_contradiction(self) -> bool:
        for r in range(9):
            for c in range(9):
                s = self.candidates[r][c]
                if s is not None and not s:
                    return True
        return False

    def is_solved(self) -> bool:
        return all(self.value[r][c] for r in range(9) for c in range(9))

    # --- constraint techniques ---

    def naked_single(self) -> bool:
        """Cell with exactly one candidate -> place it."""
        for r in range(9):
            for c in range(9):
                s = self.candidates[r][c]
                if s is not None and len(s) == 1:
                    self.place(r, c, next(iter(s)))
                    return True
        return False

    def hidden_single(self) -> bool:
        """Digit that can only appear in one cell of a unit -> place it."""
        for r in range(9):
            for n in range(1, 10):
                spots = [
                    c
                    for c in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if len(spots) == 1:
                    self.place(r, spots[0], n)
                    return True
        for c in range(9):
            for n in range(1, 10):
                spots = [
                    r
                    for r in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if len(spots) == 1:
                    self.place(spots[0], c, n)
                    return True
        for b in range(9):
            for n in range(1, 10):
                spots = [
                    (i, j)
                    for i, j in box_cells(b)
                    if self.candidates[i][j] is not None and n in self.candidates[i][j]
                ]
                if len(spots) == 1:
                    i, j = spots[0]
                    self.place(i, j, n)
                    return True
        return False

    def naked_tuple(self, size: int) -> bool:
        """
        Naked pair/triple: size cells whose candidate union has size digits
        -> remove those digits from other cells in the unit.
        """
        for unit in UNITS:
            empties = [(r, c) for r, c in unit if self.candidates[r][c] is not None]
            pool = [(r, c) for r, c in empties if len(self.candidates[r][c]) <= size]
            if len(pool) < size:
                continue
            for combo in combinations(pool, size):
                union: set[Digit] = set()
                for r, c in combo:
                    union |= self.candidates[r][c]
                if len(union) != size:
                    continue
                changed = False
                combo_set = set(combo)
                for r, c in empties:
                    if (r, c) in combo_set:
                        continue
                    before = len(self.candidates[r][c])
                    self.candidates[r][c] -= union
                    if len(self.candidates[r][c]) < before:
                        changed = True
                if changed:
                    return True
        return False

    def hidden_tuple(self, size: int) -> bool:
        """
        Hidden pair/triple: size digits that only appear in size cells of a unit
        -> those cells keep only those digits.
        """
        for unit in UNITS:
            empties = [(r, c) for r, c in unit if self.candidates[r][c] is not None]
            if len(empties) <= size:
                continue
            positions: dict[Digit, list[tuple[int, int]]] = {d: [] for d in range(1, 10)}
            for r, c in empties:
                for d in self.candidates[r][c]:
                    positions[d].append((r, c))
            digits = [d for d in range(1, 10) if 1 <= len(positions[d]) <= size]
            if len(digits) < size:
                continue
            for combo in combinations(digits, size):
                cells: set[tuple[int, int]] = set()
                for d in combo:
                    cells.update(positions[d])
                if len(cells) != size:
                    continue
                keep = set(combo)
                changed = False
                for r, c in cells:
                    before = len(self.candidates[r][c])
                    self.candidates[r][c] &= keep
                    if len(self.candidates[r][c]) < before:
                        changed = True
                if changed:
                    return True
        return False

    def pointing_and_claiming(self) -> bool:
        """Box-line reduction: pointing pairs and claiming."""
        changed = False
        # Pointing: digit confined to one row/col inside a box -> eliminate elsewhere in that line
        for b in range(9):
            cells = list(box_cells(b))
            for n in range(1, 10):
                spots = [
                    (r, c)
                    for r, c in cells
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if not spots:
                    continue
                rows = {r for r, _ in spots}
                cols = {c for _, c in spots}
                if len(rows) == 1:
                    r = next(iter(rows))
                    for c in range(9):
                        if box_of(r, c) == b:
                            continue
                        s = self.candidates[r][c]
                        if s is not None and n in s:
                            s.discard(n)
                            changed = True
                if len(cols) == 1:
                    c = next(iter(cols))
                    for r in range(9):
                        if box_of(r, c) == b:
                            continue
                        s = self.candidates[r][c]
                        if s is not None and n in s:
                            s.discard(n)
                            changed = True
        # Claiming: digit confined to one box inside a row/col -> eliminate elsewhere in that box
        for r in range(9):
            for n in range(1, 10):
                spots = [
                    c
                    for c in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if not spots:
                    continue
                boxes = {box_of(r, c) for c in spots}
                if len(boxes) != 1:
                    continue
                b = next(iter(boxes))
                for i, j in box_cells(b):
                    if i == r:
                        continue
                    s = self.candidates[i][j]
                    if s is not None and n in s:
                        s.discard(n)
                        changed = True
        for c in range(9):
            for n in range(1, 10):
                spots = [
                    r
                    for r in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if not spots:
                    continue
                boxes = {box_of(r, c) for r in spots}
                if len(boxes) != 1:
                    continue
                b = next(iter(boxes))
                for i, j in box_cells(b):
                    if j == c:
                        continue
                    s = self.candidates[i][j]
                    if s is not None and n in s:
                        s.discard(n)
                        changed = True
        return changed

    def x_wing(self) -> bool:
        """X-Wing on rows and columns."""
        changed = False
        for n in range(1, 10):
            # rows: digit n appears in exactly two cols in a row
            row_cols: list[Optional[frozenset[int]]] = [None] * 9
            for r in range(9):
                cols = [
                    c
                    for c in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if len(cols) == 2:
                    row_cols[r] = frozenset(cols)
            for r1, r2 in combinations(range(9), 2):
                if row_cols[r1] is None or row_cols[r1] != row_cols[r2]:
                    continue
                cols = row_cols[r1]
                for c in cols:
                    for r in range(9):
                        if r in (r1, r2):
                            continue
                        s = self.candidates[r][c]
                        if s is not None and n in s:
                            s.discard(n)
                            changed = True
            # columns: digit n appears in exactly two rows in a col
            col_rows: list[Optional[frozenset[int]]] = [None] * 9
            for c in range(9):
                rows = [
                    r
                    for r in range(9)
                    if self.candidates[r][c] is not None and n in self.candidates[r][c]
                ]
                if len(rows) == 2:
                    col_rows[c] = frozenset(rows)
            for c1, c2 in combinations(range(9), 2):
                if col_rows[c1] is None or col_rows[c1] != col_rows[c2]:
                    continue
                rows = col_rows[c1]
                for r in rows:
                    for c in range(9):
                        if c in (c1, c2):
                            continue
                        s = self.candidates[r][c]
                        if s is not None and n in s:
                            s.discard(n)
                            changed = True
        return changed

    def propagate(self) -> bool:
        """Apply deduction rules until stuck. Returns False on contradiction."""
        while True:
            if self.naked_single() or self.hidden_single():
                if self.is_contradiction():
                    return False
                continue
            if (
                self.naked_tuple(2)
                or self.naked_tuple(3)
                or self.hidden_tuple(2)
                or self.hidden_tuple(3)
                or self.pointing_and_claiming()
                or self.x_wing()
            ):
                if self.is_contradiction():
                    return False
                continue
            break
        return not self.is_contradiction()

    def _empty_peer_count(self, r: int, c: int) -> int:
        """Degree heuristic: how many empty peers this cell constrains."""
        seen: set[tuple[int, int]] = set()
        for k in range(9):
            if self.candidates[r][k] is not None:
                seen.add((r, k))
            if self.candidates[k][c] is not None:
                seen.add((k, c))
        for i, j in box_cells(box_of(r, c)):
            if self.candidates[i][j] is not None:
                seen.add((i, j))
        seen.discard((r, c))
        return len(seen)

    def choose_cell(self) -> Optional[tuple[int, int]]:
        """MRV, ties broken by highest degree."""
        best: Optional[tuple[int, int]] = None
        best_len = 10
        best_deg = -1
        for r in range(9):
            for c in range(9):
                s = self.candidates[r][c]
                if s is None:
                    continue
                n = len(s)
                if n > best_len:
                    continue
                deg = self._empty_peer_count(r, c)
                if n < best_len or deg > best_deg:
                    best_len = n
                    best_deg = deg
                    best = (r, c)
                    if best_len == 1:
                        return best
        return best

    def order_values(self, r: int, c: int) -> list[Digit]:
        """LCV: try values that eliminate the fewest peer candidates first."""

        def disruptions(n: Digit) -> int:
            count = 0
            for k in range(9):
                s = self.candidates[r][k]
                if s is not None and n in s:
                    count += 1
                s = self.candidates[k][c]
                if s is not None and n in s:
                    count += 1
            for i, j in box_cells(box_of(r, c)):
                if (i, j) == (r, c):
                    continue
                s = self.candidates[i][j]
                if s is not None and n in s:
                    count += 1
            return count

        return sorted(self.candidates[r][c], key=disruptions)

    def solve(self, find_all: bool = False) -> list[list[list[int]]]:
        """Return solutions. By default only the first; set find_all for every one."""
        solutions: list[list[list[int]]] = []
        self._search(solutions, find_all)
        return solutions

    def _search(self, solutions: list[list[list[int]]], find_all: bool) -> bool:
        """DFS. Returns True when search should stop (one solution found and not find_all)."""
        if not self.propagate():
            return False
        if self.is_solved():
            solutions.append([row[:] for row in self.value])
            return not find_all

        cell = self.choose_cell()
        if cell is None:
            solutions.append([row[:] for row in self.value])
            return not find_all

        r, c = cell
        for n in self.order_values(r, c):
            trial = self.clone()
            trial.place(r, c, n)
            if trial._search(solutions, find_all):
                return True
        return False


def parse_board(raw) -> list[list[int]]:
    """Accept a 9x9 int grid, a list of dotted rows, or one multi-line string."""
    if isinstance(raw, str):
        rows = [line for line in raw.splitlines() if line.strip()]
        return parse_board(rows)

    if not isinstance(raw, list) or not raw:
        raise ValueError("board must be a 9x9 grid or dotted row strings")

    # Already numeric 9x9
    if isinstance(raw[0], list):
        if len(raw) != 9 or any(len(row) != 9 for row in raw):
            raise ValueError("numeric board must be 9x9")
        return [[int(x) for x in row] for row in raw]

    # Dotted / spaced row strings, e.g. "8.. ... ..." or "8........"
    if isinstance(raw[0], str):
        grid: list[list[int]] = []
        for line in raw:
            cells: list[int] = []
            for ch in line:
                if ch in ".0":
                    cells.append(0)
                elif ch.isdigit():
                    cells.append(int(ch))
                # ignore spaces and other separators
            if cells:
                grid.append(cells)
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            raise ValueError(
                f"dotted board must yield 9x9 cells, got "
                f"{len(grid)}x{[len(r) for r in grid]}"
            )
        return grid

    raise ValueError("unsupported board format")


def load_puzzles(path: Path) -> list[list[list[int]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "puzzles" in data:
        return [parse_board(p) for p in data["puzzles"]]
    if isinstance(data, dict) and "board" in data:
        return [parse_board(data["board"])]
    if isinstance(data, str):
        return [parse_board(data)]
    if isinstance(data, list) and data:
        # list of boards, or a single board (numeric / dotted rows)
        first = data[0]
        if isinstance(first, list) and first and isinstance(first[0], list):
            return [parse_board(p) for p in data]
        return [parse_board(data)]
    raise ValueError(
        'JSON must be {"board": [...]} / {"puzzles": [...]}, '
        "a bare 9x9 grid, or dotted row strings ('.' = empty)."
    )


def format_board(board: list[list[int]]) -> str:
    lines = []
    for r, row in enumerate(board):
        if r in (3, 6):
            lines.append("------+-------+------")
        chunks = ["".join(str(x) if x else "." for x in row[c : c + 3]) for c in (0, 3, 6)]
        lines.append(" | ".join(" ".join(ch) for ch in chunks))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sudoku solver (JSON input)")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent / "tests" / "puzzle.json",
        help="path to puzzle JSON (default: tests/puzzle.json)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="find all solutions instead of stopping at the first",
    )
    args = parser.parse_args()

    puzzles = load_puzzles(args.input)
    t0 = time.perf_counter()

    for idx, grid in enumerate(puzzles, 1):
        solutions = Sudoku(grid).solve(find_all=args.all)
        print(f"Puzzle #{idx}")
        if not solutions:
            print("No solution.")
        elif not args.all:
            for row in solutions[0]:
                print(" ".join(str(x) for x in row))
        else:
            print(f"{len(solutions)} solution(s).")
            for sidx, solution in enumerate(solutions, 1):
                print(f"--- Solution #{sidx} ---")
                for row in solution:
                    print(" ".join(str(x) for x in row))
        print()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(f"Time: {elapsed_ms:.2f}ms.")


if __name__ == "__main__":
    main()
