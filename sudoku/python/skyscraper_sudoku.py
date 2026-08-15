"""Skyscraper Sudoku solver.

Standard Sudoku rules, plus edge clues: each number is a building height;
looking into a row/column from that side, the clue is how many buildings
are visible (a building is visible iff it is taller than all in front of it).

Inherits sudoku.py techniques (naked/hidden tuples, pointing, X-Wing, MRV+LCV),
and adds skyscraper-specific pruning:
  - clue 1 / N extreme placements
  - position bounds for the tallest building
  - candidate elimination via single-line feasibility
  - partial visibility bounds

JSON example
------------
{
  "board": ["...", ...],
  "skyscrapers": {
    "top":    [2, 3, 0, 4, 2, 1, 3, 5, 3],
    "bottom": [3, 2, 1, 2, 3, 4, 4, 3, 3],
    "left":   [6, 1, 2, 2, 3, 4, 5, 3, 3],
    "right":  [3, 3, 2, 2, 3, 1, 2, 3, 4]
  }
}

Use 0 for a missing clue (no constraint on that side of that line).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sudoku import Digit, Sudoku, parse_board


def visible_count(heights: list[int]) -> int:
    """How many buildings are seen looking along `heights` from index 0."""
    seen = tallest = 0
    for h in heights:
        if h > tallest:
            tallest = h
            seen += 1
    return seen


def normalize_clues(raw, n: int = 9) -> list[int]:
    if raw is None:
        return [0] * n
    if len(raw) != n:
        raise ValueError(f"skyscraper clue list must have length {n}, got {len(raw)}")
    clues = [int(x) for x in raw]
    for c in clues:
        if c < 0 or c > n:
            raise ValueError(f"skyscraper clue out of range 0..{n}: {c}")
    return clues


def _line_feasible(
    fixed: list[int],
    cands: list[set[int] | None],
    front: int,
    back: int,
    n: int,
) -> bool:
    """Whether some assignment of remaining digits satisfies front/back clues."""
    used = {h for h in fixed if h}
    remaining = [d for d in range(1, n + 1) if d not in used]
    empties = [i for i, h in enumerate(fixed) if h == 0]
    if len(empties) != len(remaining):
        return False

    # Fast reject: tallest already placed with impossible visibility prefix.
    if not front and not back:
        return True

    def ok(seq: list[int]) -> bool:
        if front and visible_count(seq) != front:
            return False
        if back and visible_count(list(reversed(seq))) != back:
            return False
        return True

    if not empties:
        return ok(fixed)

    # Bound search: only try when few empties (called from elimination with cap).
    order = sorted(empties, key=lambda i: len(cands[i] or remaining))

    def dfs(seq: list[int], left: set[int]) -> bool:
        if not left:
            return ok(seq)
        # Partial visibility prune from front
        if front:
            seen = tallest = 0
            blocked = False
            for h in seq:
                if h == 0:
                    blocked = True
                    break
                if h > tallest:
                    tallest = h
                    seen += 1
                    if seen > front:
                        return False
            if not blocked and tallest == n and seen != front:
                return False
        if back:
            seen = tallest = 0
            blocked = False
            for h in reversed(seq):
                if h == 0:
                    blocked = True
                    break
                if h > tallest:
                    tallest = h
                    seen += 1
                    if seen > back:
                        return False
            if not blocked and tallest == n and seen != back:
                return False

        i = next(i for i in order if seq[i] == 0)
        options = (cands[i] & left) if cands[i] is not None else left
        for d in sorted(options):
            seq[i] = d
            left.remove(d)
            if dfs(seq, left):
                return True
            left.add(d)
            seq[i] = 0
        return False

    return dfs(list(fixed), set(remaining))


class SkyscraperSudoku(Sudoku):
    def __init__(
        self,
        grid: list[list[int]],
        top: list[int] | None = None,
        bottom: list[int] | None = None,
        left: list[int] | None = None,
        right: list[int] | None = None,
    ) -> None:
        self.n = len(grid)
        self.top = normalize_clues(top, self.n)
        self.bottom = normalize_clues(bottom, self.n)
        self.left = normalize_clues(left, self.n)
        self.right = normalize_clues(right, self.n)
        super().__init__(grid)
        self._apply_extreme_clues()
        self._eliminate_tallest_positions()

    def clone(self) -> SkyscraperSudoku:
        other = SkyscraperSudoku.__new__(SkyscraperSudoku)
        other.n = self.n
        other.top = self.top
        other.bottom = self.bottom
        other.left = self.left
        other.right = self.right
        other.value = [row[:] for row in self.value]
        other.candidates = [
            [None if s is None else set(s) for s in row] for row in self.candidates
        ]
        return other

    def _force(self, r: int, c: int, n: Digit) -> None:
        """Place n if empty; reject if conflicting given/candidate."""
        if self.value[r][c]:
            if self.value[r][c] != n:
                raise ValueError(f"clue conflicts at ({r},{c}): want {n}")
            return
        if self.candidates[r][c] is None or n not in self.candidates[r][c]:
            raise ValueError(f"clue impossible at ({r},{c}): {n}")
        self.place(r, c, n)

    def _apply_extreme_clues(self) -> None:
        """clue 1 => nearest cell is N; clue N => 1..N in sight order."""
        n = self.n
        for c, clue in enumerate(self.top):
            if clue == 1:
                self._force(0, c, n)
            elif clue == n:
                for r in range(n):
                    self._force(r, c, r + 1)
        for c, clue in enumerate(self.bottom):
            if clue == 1:
                self._force(n - 1, c, n)
            elif clue == n:
                for r in range(n):
                    self._force(n - 1 - r, c, r + 1)
        for r, clue in enumerate(self.left):
            if clue == 1:
                self._force(r, 0, n)
            elif clue == n:
                for c in range(n):
                    self._force(r, c, c + 1)
        for r, clue in enumerate(self.right):
            if clue == 1:
                self._force(r, n - 1, n)
            elif clue == n:
                for c in range(n):
                    self._force(r, n - 1 - c, c + 1)

    def _eliminate_tallest_positions(self) -> None:
        """
        If clue is c from a side, the tallest (N) must be at index i with i >= c-1
        (at most i buildings can stand in front, so max visibles is i+1).
        """
        n = self.n

        def ban_n_outside(positions: list[tuple[int, int]], clue: int) -> None:
            if clue <= 0:
                return
            lo = clue - 1
            for idx, (r, c) in enumerate(positions):
                if idx >= lo:
                    continue
                s = self.candidates[r][c]
                if s is not None and n in s:
                    s.discard(n)
                elif self.value[r][c] == n:
                    raise ValueError("tallest position contradicts skyscraper clue")

        for c, clue in enumerate(self.top):
            ban_n_outside([(r, c) for r in range(n)], clue)
        for c, clue in enumerate(self.bottom):
            ban_n_outside([(r, c) for r in range(n - 1, -1, -1)], clue)
        for r, clue in enumerate(self.left):
            ban_n_outside([(r, c) for c in range(n)], clue)
        for r, clue in enumerate(self.right):
            ban_n_outside([(r, c) for c in range(n - 1, -1, -1)], clue)

    def _line_ok(self, seq: list[int], front: int, back: int) -> bool:
        if 0 in seq:
            if front:
                seen = tallest = 0
                for h in seq:
                    if h == 0:
                        break
                    if h > tallest:
                        tallest = h
                        seen += 1
                        if seen > front:
                            return False
                else:
                    if front and visible_count(seq) != front:
                        return False
            if back:
                seen = tallest = 0
                for h in reversed(seq):
                    if h == 0:
                        break
                    if h > tallest:
                        tallest = h
                        seen += 1
                        if seen > back:
                            return False
                else:
                    if back and visible_count(list(reversed(seq))) != back:
                        return False
            return True
        if front and visible_count(seq) != front:
            return False
        if back and visible_count(list(reversed(seq))) != back:
            return False
        return True

    def skyscraper_ok(self) -> bool:
        n = self.n
        for r in range(n):
            if not self._line_ok(self.value[r], self.left[r], self.right[r]):
                return False
        for c in range(n):
            col = [self.value[r][c] for r in range(n)]
            if not self._line_ok(col, self.top[c], self.bottom[c]):
                return False
        return True

    def _row_cands(self, r: int) -> list[set[int] | None]:
        return [
            None if self.value[r][c] else self.candidates[r][c] for c in range(self.n)
        ]

    def _col_cands(self, c: int) -> list[set[int] | None]:
        return [
            None if self.value[r][c] else self.candidates[r][c] for r in range(self.n)
        ]

    def eliminate_skyscraper_candidates(self) -> bool:
        """Drop candidates that make a line impossible under its clues."""
        n = self.n
        changed = False
        max_empty = 6  # feasibility search cost grows with empties

        def scrub_line(
            get_val: list[int],
            get_cands: list[set[int] | None],
            set_discard,
            front: int,
            back: int,
        ) -> bool:
            nonlocal changed
            if not front and not back:
                return False
            empties = sum(1 for h in get_val if h == 0)
            if empties == 0 or empties > max_empty:
                return False
            local = False
            for i in range(n):
                if get_val[i] != 0:
                    continue
                s = get_cands[i]
                if not s:
                    continue
                for d in list(s):
                    trial_val = get_val[:]
                    trial_val[i] = d
                    trial_cands = [None if v else (set(c) if c else set()) for v, c in zip(get_val, get_cands)]
                    trial_cands[i] = None
                    # digit d is used
                    for j in range(n):
                        if trial_cands[j] is not None:
                            trial_cands[j].discard(d)
                    if not _line_feasible(trial_val, trial_cands, front, back, n):
                        set_discard(i, d)
                        local = True
                        changed = True
            return local

        for r in range(n):
            vals = self.value[r][:]
            cands = self._row_cands(r)

            def discard_row(i: int, d: int, row=r) -> None:
                if self.candidates[row][i] is not None:
                    self.candidates[row][i].discard(d)

            scrub_line(vals, cands, discard_row, self.left[r], self.right[r])

        for c in range(n):
            vals = [self.value[r][c] for r in range(n)]
            cands = self._col_cands(c)

            def discard_col(i: int, d: int, col=c) -> None:
                if self.candidates[i][col] is not None:
                    self.candidates[i][col].discard(d)

            scrub_line(vals, cands, discard_col, self.top[c], self.bottom[c])

        return changed

    def propagate(self) -> bool:
        while True:
            if not super().propagate():
                return False
            if not self.skyscraper_ok():
                return False
            if self.eliminate_skyscraper_candidates():
                if self.is_contradiction():
                    return False
                continue
            break
        return self.skyscraper_ok() and not self.is_contradiction()

    def _search(self, solutions: list[list[list[int]]], find_all: bool) -> bool:
        if not self.propagate():
            return False
        if self.is_solved():
            if not self.skyscraper_ok():
                return False
            solutions.append([row[:] for row in self.value])
            return not find_all

        cell = self.choose_cell()
        if cell is None:
            if self.skyscraper_ok():
                solutions.append([row[:] for row in self.value])
                return not find_all
            return False

        r, c = cell
        for n in self.order_values(r, c):
            trial = self.clone()
            trial.place(r, c, n)
            if trial._search(solutions, find_all):
                return True
        return False


def load_skyscraper_puzzle(path: Path) -> tuple[list[list[int]], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "board" not in data:
        raise ValueError('skyscraper JSON must be {"board": ..., "skyscrapers": {...}}')
    board = parse_board(data["board"])
    sky = data.get("skyscrapers") or data.get("skyscraper") or {}
    if not isinstance(sky, dict):
        raise ValueError("skyscrapers must be an object with top/bottom/left/right")
    clues = {
        "top": sky.get("top"),
        "bottom": sky.get("bottom"),
        "left": sky.get("left"),
        "right": sky.get("right"),
    }
    return board, clues


def main() -> None:
    parser = argparse.ArgumentParser(description="Skyscraper Sudoku solver")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent / "tests" / "skyscraper_puzzle1.json",
        help="path to skyscraper puzzle JSON (default: tests/skyscraper_puzzle1.json)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="find all solutions instead of stopping at the first",
    )
    args = parser.parse_args()

    board, clues = load_skyscraper_puzzle(args.input)
    t0 = time.perf_counter()
    try:
        solver = SkyscraperSudoku(board, **clues)
    except ValueError as e:
        print(f"Invalid puzzle: {e}")
        return

    solutions = solver.solve(find_all=args.all)
    elapsed_ms = (time.perf_counter() - t0) * 1000

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
    print(f"\nTime: {elapsed_ms:.2f}ms.")


if __name__ == "__main__":
    main()
