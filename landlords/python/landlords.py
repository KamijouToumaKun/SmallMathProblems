#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斗地主 1v1 残局求解（记忆化搜索）
牌面编码: A=14, 2=15, 小王s=16, 大王b=17
牌型:
  0 要不起/自由出牌
  1 单  2 对  3 三张  4 三带一  5 三带二
  6 单顺  7 双顺  8 三顺  9 飞机带单  10 飞机带对
  11 炸弹/王炸  12 四带二（num=1 带两单，num=2 带两对）
规则参考：竞技二打一 / 常见官方玩法（顺子不含2与王等）
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------- 常量 ----------
RANK_MIN, RANK_MAX = 3, 17
STRAIGHT_MAX_RANK = 14  # 顺子/连对/飞机机身最大到 A，不含 2、王
TYPE_NAMES = {
    1: "单张",
    2: "对子",
    3: "三张",
    4: "三带一",
    5: "三带二",
    6: "单顺",
    7: "双顺",
    8: "三顺",
    9: "飞机带单",
    10: "飞机带对",
    11: "炸弹",
    12: "四带二",
}
RULE_KEYS = [
    "single",
    "pair",
    "triple",
    "triple_one",
    "triple_two",
    "straight",
    "double_straight",
    "triple_straight",
    "plane_with_singles",
    "plane_with_pairs",
    "bomb",
    "four_with_two",
]
# 连续最少张数（下标对应牌型-5）
LEAST_SERIES = [0, 5, 3, 2, 2, 2]
# 自由出牌时尝试的最大长度：单顺12，双顺12，三顺/飞机12
MAX_SERIES = [0, 12, 12, 12, 12, 12]

RANK_TO_STR = {
    11: "J", 12: "Q", 13: "K", 14: "A", 15: "2", 16: "s", 17: "b",
}
STR_TO_RANK = {
    "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13, "A": 14, "2": 15, "s": 16, "b": 17,
    "j": 11, "q": 12, "k": 13, "a": 14,
}


def rank_to_str(rank: int) -> str:
    if rank <= 10:
        return str(rank)
    return RANK_TO_STR[rank]


def parse_card_token(token: str) -> int:
    token = token.strip()
    if token not in STR_TO_RANK:
        raise ValueError(f"无法识别的牌面: {token!r}（可用 3-10/J/Q/K/A/2/s/b）")
    return STR_TO_RANK[token]


def tokenize_hand(text: str) -> List[str]:
    """解析手牌字符串。支持空格分隔，或连写（10 优先于 1+0）。"""
    text = text.strip()
    if not text:
        return []
    if any(ch.isspace() for ch in text):
        return text.split()
    tokens: List[str] = []
    i = 0
    while i < len(text):
        if text.startswith("10", i):
            tokens.append("10")
            i += 2
            continue
        ch = text[i]
        if ch not in STR_TO_RANK:
            raise ValueError(f"无法识别的牌面字符: {ch!r}（在 {text!r} 位置 {i}）")
        tokens.append(ch)
        i += 1
    return tokens


def parse_hand_field(value) -> List[str]:
    """JSON 中 computer/player：字符串（推荐）或旧版字符串数组。"""
    if isinstance(value, str):
        return tokenize_hand(value)
    if isinstance(value, list):
        return [str(x) for x in value]
    raise TypeError("computer/player 须为字符串或字符串数组")


def ranks_to_counts(ranks: Sequence[int]) -> List[int]:
    counts = [0] * 18
    for r in ranks:
        counts[r] += 1
    return counts


def format_counts(counts: Sequence[int]) -> str:
    parts: List[str] = []
    for i in range(RANK_MAX, RANK_MIN - 1, -1):
        parts.extend([rank_to_str(i)] * counts[i])
    return " ".join(parts) if parts else "（空）"


@dataclass(frozen=True)
class Move:
    """一次出牌。main 为主牌点数（顺子/飞机为起点）；length 为连续长度或四带二形态。"""
    card_type: int
    main: int
    length: int = 1

    @property
    def is_rocket(self) -> bool:
        return self.card_type == 11 and self.main == 16

    @property
    def is_bomb(self) -> bool:
        return self.card_type == 11

    def describe(self) -> str:
        name = TYPE_NAMES.get(self.card_type, str(self.card_type))
        if self.is_rocket:
            return "王炸"
        if self.card_type == 12:
            wing = "带两单" if self.length == 1 else "带两对"
            return f"{name}({wing}) 主牌{rank_to_str(self.main)}"
        if self.card_type >= 6 and self.card_type <= 10:
            end = self.main + self.length - 1
            return f"{name} {rank_to_str(self.main)}-{rank_to_str(end)}（长{self.length}）"
        return f"{name} {rank_to_str(self.main)}"

    def to_constraint(self) -> Tuple[int, int, int]:
        """转为 determine() 所用的 (card_type, beg, num)。beg 为对方需压过的下限。"""
        if self.is_rocket:
            # 王炸之后 beg=17：普通炸与王炸皆不可再压（勿用 16，会与「炸2」混淆）
            return 11, 17, 1
        if self.card_type == 12:
            return 12, self.main + 1, self.length
        if self.card_type >= 6:
            return self.card_type, self.main + 1, self.length
        return self.card_type, self.main + 1, self.length


def is_consecutive(ranks: Sequence[int]) -> bool:
    if not ranks:
        return False
    rs = sorted(ranks)
    return all(rs[i] + 1 == rs[i + 1] for i in range(len(rs) - 1))


def recognize_moves(
    counts: Sequence[int],
    type_allowed: Sequence[bool],
    *,
    allow_four_two_singles: Optional[bool] = None,
    allow_four_two_pairs: Optional[bool] = None,
) -> List[Move]:
    """识别一手牌的全部合法牌型解释（按官方常见规则）。"""
    counts = list(counts)
    total = sum(counts)
    moves: List[Move] = []
    if total == 0:
        return moves

    def allow(t: int) -> bool:
        return bool(type_allowed[t])

    if allow_four_two_singles is None:
        allow_four_two_singles = allow(12)
    if allow_four_two_pairs is None:
        allow_four_two_pairs = False

    # 王炸
    if total == 2 and counts[16] == 1 and counts[17] == 1 and allow(11):
        moves.append(Move(11, 16, 1))
        return moves

    nonzero = [r for r in range(RANK_MIN, RANK_MAX + 1) if counts[r]]

    # 炸弹：恰好四张且同一点数
    if total == 4 and len(nonzero) == 1 and counts[nonzero[0]] == 4 and allow(11):
        moves.append(Move(11, nonzero[0], 1))
        return moves

    # 单张
    if total == 1 and allow(1):
        moves.append(Move(1, nonzero[0], 1))
        return moves

    # 对子（不含王）
    if total == 2 and len(nonzero) == 1 and counts[nonzero[0]] == 2:
        if nonzero[0] <= 15 and allow(2):
            moves.append(Move(2, nonzero[0], 1))
        return moves

    # 三张
    if total == 3 and len(nonzero) == 1 and counts[nonzero[0]] == 3 and allow(3):
        moves.append(Move(3, nonzero[0], 1))
        return moves

    # 三带一：三张 + 另一点数的一张（不能是四个同一点；带牌点数不同）
    if total == 4 and allow(4):
        triples = [r for r in nonzero if counts[r] == 3]
        singles = [r for r in nonzero if counts[r] == 1]
        if len(triples) == 1 and len(singles) == 1 and len(nonzero) == 2:
            moves.append(Move(4, triples[0], 1))

    # 三带二：三张 + 另一点数的对子（对子不能是王）
    if total == 5 and allow(5):
        triples = [r for r in nonzero if counts[r] == 3]
        pairs = [r for r in nonzero if counts[r] == 2 and r <= 15]
        if len(triples) == 1 and len(pairs) == 1 and len(nonzero) == 2:
            moves.append(Move(5, triples[0], 1))

    # 单顺：>=5 张连续单牌，仅 3..A
    if allow(6) and total >= 5 and all(counts[r] == 1 for r in nonzero):
        if max(nonzero) <= STRAIGHT_MAX_RANK and min(nonzero) >= 3 and is_consecutive(nonzero):
            if len(nonzero) == total:
                moves.append(Move(6, min(nonzero), total))

    # 双顺：>=3 连续对，仅 3..A
    if allow(7) and total >= 6 and total % 2 == 0:
        if all(counts[r] == 2 for r in nonzero) and max(nonzero) <= STRAIGHT_MAX_RANK:
            if min(nonzero) >= 3 and is_consecutive(nonzero) and len(nonzero) >= 3:
                moves.append(Move(7, min(nonzero), len(nonzero)))

    # 三顺（飞机不带翼）
    if allow(8) and total >= 6 and total % 3 == 0:
        if all(counts[r] == 3 for r in nonzero) and max(nonzero) <= STRAIGHT_MAX_RANK:
            if min(nonzero) >= 3 and is_consecutive(nonzero) and len(nonzero) >= 2:
                moves.append(Move(8, min(nonzero), len(nonzero)))

    # 飞机带单 / 带对
    moves.extend(_recognize_planes(counts, type_allowed))

    # 四带二：带两单 / 带两对 可分别开关；带牌不含王、不含炸弹
    if allow_four_two_singles or allow_four_two_pairs:
        moves.extend(
            _recognize_four_with_two(
                counts,
                allow_singles=bool(allow_four_two_singles),
                allow_pairs=bool(allow_four_two_pairs),
            )
        )

    return _unique_moves(moves)


def _unique_moves(moves: Sequence[Move]) -> List[Move]:
    seen = set()
    out: List[Move] = []
    for m in moves:
        key = (m.card_type, m.main, m.length)
        if key not in seen:
            seen.add(key)
            out.append(m)
    return out


def _recognize_planes(counts: Sequence[int], type_allowed: Sequence[bool]) -> List[Move]:
    """飞机带翅膀。翅膀不含王、炸弹；不把可接上的连续三张拆进翅膀（机身取最长合理划分时枚举）。"""
    result: List[Move] = []
    counts = list(counts)
    total = sum(counts)

    # 可能的机身：连续 >=2 的三张，范围 3..A
    candidates: List[Tuple[int, int]] = []
    for beg in range(3, STRAIGHT_MAX_RANK + 1):
        for length in range(2, STRAIGHT_MAX_RANK - beg + 2):
            if all(counts[beg + i] >= 3 for i in range(length)):
                candidates.append((beg, length))

    for beg, length in candidates:
        body = list(counts)
        for i in range(length):
            body[beg + i] -= 3
        wing_cards = sum(body)
        # 带单：length 张单牌
        if type_allowed[9] and wing_cards == length:
            if _valid_single_wings(body, beg, length):
                result.append(Move(9, beg, length))
        # 带对：length 个对子
        if type_allowed[10] and wing_cards == 2 * length:
            if _valid_pair_wings(body, beg, length):
                result.append(Move(10, beg, length))

    return result


def _valid_single_wings(wing_counts: Sequence[int], beg: int, length: int) -> bool:
    """单翅膀：恰好 length 张；无王；无四张炸弹当翅膀；不把与机身相邻的「整组三张」当翅膀。"""
    if wing_counts[16] or wing_counts[17]:
        return False
    total = sum(wing_counts)
    if total != length:
        return False
    for r in range(RANK_MIN, RANK_MAX + 1):
        if wing_counts[r] >= 4:
            return False
    # 禁止用与机身连续的三张作为翅膀（应并入更长飞机）
    for adj in (beg - 1, beg + length):
        if 3 <= adj <= STRAIGHT_MAX_RANK and wing_counts[adj] == 3:
            return False
    return True


def _valid_pair_wings(wing_counts: Sequence[int], beg: int, length: int) -> bool:
    if wing_counts[16] or wing_counts[17]:
        return False
    pairs = 0
    for r in range(RANK_MIN, 16):
        if wing_counts[r] == 0:
            continue
        if wing_counts[r] == 2:
            pairs += 1
        elif wing_counts[r] == 4:
            # 四张可视为两个对，但属于炸弹作翅膀，禁止
            return False
        else:
            return False
    if pairs != length:
        return False
    for adj in (beg - 1, beg + length):
        if 3 <= adj <= STRAIGHT_MAX_RANK and wing_counts[adj] >= 3:
            return False
    return True


def _recognize_four_with_two(
    counts: Sequence[int],
    *,
    allow_singles: bool = True,
    allow_pairs: bool = True,
) -> List[Move]:
    result: List[Move] = []
    total = sum(counts)
    fours = [r for r in range(RANK_MIN, 16) if counts[r] == 4]
    if len(fours) != 1:
        return result
    main = fours[0]
    rest = list(counts)
    rest[main] = 0

    # 带两单：剩余恰好 2 张，不能含王，不能是另一炸弹
    if allow_singles and total == 6:
        if rest[16] == 0 and rest[17] == 0 and sum(rest) == 2:
            if not any(rest[r] == 4 for r in range(RANK_MIN, 16)):
                result.append(Move(12, main, 1))
    # 带两对：剩余 4 张，恰好两个不同点数的对，不含王/炸弹
    if allow_pairs and total == 8:
        if rest[16] == 0 and rest[17] == 0:
            pair_ranks = [r for r in range(RANK_MIN, 16) if rest[r] == 2]
            if len(pair_ranks) == 2 and sum(rest) == 4:
                result.append(Move(12, main, 2))
    return result


def beats(challenger: Move, previous: Move) -> bool:
    """challenger 是否压过 previous。"""
    if challenger.is_rocket:
        return not previous.is_rocket
    if previous.is_rocket:
        return False
    if challenger.is_bomb:
        if previous.is_bomb:
            return challenger.main > previous.main
        return True
    if previous.is_bomb:
        return False
    if challenger.card_type != previous.card_type:
        return False
    if challenger.length != previous.length:
        return False
    return challenger.main > previous.main


class Landlords:
    def __init__(self) -> None:
        self.card = [[0] * 18 for _ in range(2)]
        self.new_card = [[0] * 18 for _ in range(2)]
        self.type_allowed = [False] * 13
        self.flag_series = [
            [[[False] * 16 for _ in range(18)] for _ in range(4)]
            for _ in range(2)
        ]
        # 全局面记忆化（含跟牌）
        self.memo: dict = {}
        self.verbose_root = True
        self.nodes = 0
        # 四带二细分：带两单 / 带两对（默认均关闭，由 JSON 显式打开）
        self.allow_four_two_singles = False
        self.allow_four_two_pairs = False

    # ---------- 牌面工具 ----------
    def is_empty(self, player: int) -> bool:
        return all(self.card[player][i] == 0 for i in range(RANK_MIN, RANK_MAX + 1))

    def hand_total(self, player: int) -> int:
        return sum(self.card[player][i] for i in range(RANK_MIN, RANK_MAX + 1))

    def pack_hand(self, player: int) -> int:
        h = 0
        for r in range(RANK_MIN, RANK_MAX + 1):
            h |= self.card[player][r] << (3 * (r - RANK_MIN))
        return h

    def longest_run(self, player: int, need: int) -> int:
        best = cur = 0
        for r in range(3, STRAIGHT_MAX_RANK + 1):
            if self.card[player][r] >= need:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best

    def has_series(self, player: int, card_num: int, beg: int, num: int) -> bool:
        if beg <= STRAIGHT_MAX_RANK and beg + num - 1 > STRAIGHT_MAX_RANK:
            return False
        if not self.flag_series[player][card_num][beg][num]:
            return False
        for i in range(num):
            if self.card[player][beg + i] < card_num:
                return False
        return True

    def sub_series(self, player: int, card_num: int, beg: int, num: int) -> None:
        for i in range(num):
            self.card[player][beg + i] -= card_num

    def add_series(self, player: int, card_num: int, beg: int, num: int) -> None:
        for i in range(num):
            self.card[player][beg + i] += card_num

    def new_card_record(self) -> None:
        for p in range(2):
            for j in range(RANK_MIN, RANK_MAX + 1):
                self.new_card[p][j] = self.card[p][j]

    def hand_str(self, player: int) -> str:
        return format_counts(self.card[player])

    def print_hands(self, title: Optional[str] = None) -> None:
        if title:
            print(title)
        print(f"电脑: {self.hand_str(0)}")
        print(f"玩家: {self.hand_str(1)}")

    def flag_init(self) -> None:
        for player in range(2):
            for card_type in range(6, 9):
                card_num = card_type - 5
                for i in range(3, STRAIGHT_MAX_RANK + 1):
                    for num in range(STRAIGHT_MAX_RANK - i + 1, 1, -1):
                        self.flag_series[player][card_num][i][num] = True
                        self.flag_series[player][card_num][i][num] = self.has_series(
                            player, card_num, i, num
                        )
            self.flag_series[player][1][16][2] = True

    def load_cards(self, tokens: List[str], player: int) -> None:
        for t in tokens:
            r = parse_card_token(t)
            self.card[player][r] += 1

    def load_config(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
        rules = cfg.get("rules", {})
        if isinstance(rules, list):
            if len(rules) != 12:
                raise ValueError("rules 数组须为 12 个布尔值（第12项为四带两单；四带两对请用对象写法）")
            for i, v in enumerate(rules, start=1):
                self.type_allowed[i] = bool(v)
            self.allow_four_two_singles = self.type_allowed[12]
            self.allow_four_two_pairs = False
        else:
            for i, key in enumerate(RULE_KEYS, start=1):
                # 四带两单默认 false；其余牌型默认 true
                default = False if key == "four_with_two" else True
                self.type_allowed[i] = bool(rules.get(key, default))
            self.allow_four_two_singles = bool(rules.get("four_with_two", False))
            self.allow_four_two_pairs = bool(rules.get("four_with_two_pairs", False))
            self.type_allowed[12] = self.allow_four_two_singles or self.allow_four_two_pairs
        self.load_cards(parse_hand_field(cfg["computer"]), 0)
        self.load_cards(parse_hand_field(cfg["player"]), 1)
        return cfg

    def recognize(self, counts: Sequence[int]) -> List[Move]:
        return recognize_moves(
            counts,
            self.type_allowed,
            allow_four_two_singles=self.allow_four_two_singles,
            allow_four_two_pairs=self.allow_four_two_pairs,
        )

    def _memo_key(
        self, player: int, card_type: int, beg: int, num: int, can_pass: bool
    ) -> Tuple:
        if card_type == 0:
            beg = num = 0
            can_pass = True
        return (
            self.pack_hand(0),
            self.pack_hand(1),
            player,
            card_type,
            beg,
            num,
            1 if can_pass else 0,
        )

    def _after_play(
        self, depth: int, player: int, next_type: int, next_beg: int, next_num: int
    ) -> bool:
        if self.is_empty(player):
            if depth == 0:
                self.new_card_record()
            return True
        ans = not self.determine(depth + 1, next_type, next_beg, next_num)
        if ans and depth == 0:
            self.new_card_record()
        return ans

    # ---------- 核心搜索 ----------
    def determine(
        self,
        depth: int,
        card_type: int,
        beg: int,
        num: int,
        can_pass: bool = True,
    ) -> bool:
        player = depth % 2
        self.nodes += 1
        if self.is_empty(1 - player):
            return False

        key = self._memo_key(player, card_type, beg, num, can_pass)
        if depth > 0:
            cached = self.memo.get(key)
            if cached is not None:
                return cached

        if card_type == 0:
            ans = self._determine_free(depth, player)
        else:
            ans = self._determine_follow(depth, player, card_type, beg, num, can_pass)

        if depth > 0 or card_type == 0:
            self.memo[key] = ans
        return ans

    def _try_full_hand_win(self, depth: int, player: int) -> Optional[bool]:
        moves = self.recognize(self.card[player])
        if not moves:
            return None
        for m in moves:
            if m.is_rocket:
                ok = self.determine(depth, 11, 3, 1, False)
            elif m.card_type == 11:
                ok = self.determine(depth, 11, m.main, 1, False)
            elif m.card_type == 12:
                if m.length == 1 and not self.allow_four_two_singles:
                    continue
                if m.length == 2 and not self.allow_four_two_pairs:
                    continue
                ok = self.determine(depth, 12, m.main, m.length, False)
            elif m.card_type >= 6:
                ok = self.determine(depth, m.card_type, m.main, m.length, False)
            else:
                ok = self.determine(depth, m.card_type, m.main, 1, False)
            if ok:
                return True
        return None

    def _determine_free(self, depth: int, player: int) -> bool:
        instant = self._try_full_hand_win(depth, player)
        if instant is not None:
            return instant

        total = self.hand_total(player)

        for i in range(10, 5, -1):
            if not self.type_allowed[i]:
                continue
            need = 3 if i >= 8 else (i - 5)
            run = self.longest_run(player, need)
            least = LEAST_SERIES[i - 5]
            max_len = min(MAX_SERIES[i - 5], run)
            if max_len < least:
                continue
            for j in range(max_len, least - 1, -1):
                if 3 * j > total and i >= 8:
                    continue
                if need * j > total:
                    continue
                if self.determine(depth, i, 3, j, False):
                    return True
            if depth == 0 and self.verbose_root:
                print(f"（牌型 {i} {TYPE_NAMES[i]}）无必胜出法。")

        for i in (5, 4, 3, 2, 1):
            if not self.type_allowed[i]:
                continue
            need_cards = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}[i]
            if total < need_cards:
                continue
            if self.determine(depth, i, 3, 1, False):
                return True
            if depth == 0 and self.verbose_root:
                print(f"（牌型 {i} {TYPE_NAMES[i]}）无必胜出法。")

        for i in (12, 11):
            if i == 11:
                if not self.type_allowed[11]:
                    continue
                if self.determine(depth, 11, 3, 1, False):
                    return True
                if depth == 0 and self.verbose_root:
                    print(f"（牌型 {i} {TYPE_NAMES[i]}）无必胜出法。")
                continue
            # 四带二：按开关分别尝试带两单 / 带两对
            variants = []
            if self.allow_four_two_singles:
                variants.append(1)
            if self.allow_four_two_pairs:
                variants.append(2)
            if not variants:
                continue
            for n in variants:
                need_cards = 6 if n == 1 else 8
                if total < need_cards:
                    continue
                if self.determine(depth, 12, 3, n, False):
                    return True
            if depth == 0 and self.verbose_root:
                print(f"（牌型 {i} {TYPE_NAMES[i]}）无必胜出法。")

        return False

    def _determine_follow(
        self,
        depth: int,
        player: int,
        card_type: int,
        beg: int,
        num: int,
        can_pass: bool,
    ) -> bool:
        ans = False

        if card_type <= 3:
            upper = RANK_MAX if card_type == 1 else 15
            for i in range(upper, beg - 1, -1):
                if card_type == 2 and i >= 16:
                    continue
                if self.card[player][i] >= card_type:
                    self.card[player][i] -= card_type
                    ans = self._after_play(depth, player, card_type, i + 1, num)
                    self.card[player][i] += card_type
                    if ans:
                        return True
            return self.determine(depth, 11, 3, 1) if can_pass else False

        if card_type <= 5:
            need = card_type - 3
            for i in range(RANK_MAX, beg - 1, -1):
                if self.card[player][i] < 3:
                    continue
                self.card[player][i] -= 3
                for j in range(RANK_MIN, RANK_MAX + 1):
                    if j == i:
                        continue
                    if need == 2 and j >= 16:
                        continue
                    if self.card[player][j] >= need:
                        self.card[player][j] -= need
                        ans = self._after_play(depth, player, card_type, i + 1, num)
                        self.card[player][j] += need
                        if ans:
                            break
                self.card[player][i] += 3
                if ans:
                    return True
            return self.determine(depth, 11, 3, 1) if can_pass else False

        if card_type <= 8:
            last_start = STRAIGHT_MAX_RANK - num + 1
            for i in range(last_start, beg - 1, -1):
                if self.has_series(player, card_type - 5, i, num):
                    self.sub_series(player, card_type - 5, i, num)
                    ans = self._after_play(depth, player, card_type, i + 1, num)
                    self.add_series(player, card_type - 5, i, num)
                    if ans:
                        return True
            return self.determine(depth, 11, 3, 1) if can_pass else False

        if card_type <= 10:
            last_start = STRAIGHT_MAX_RANK - num + 1
            for i in range(last_start, beg - 1, -1):
                if self.has_series(player, 3, i, num):
                    self.sub_series(player, 3, i, num)
                    ans = self.attach_finder(
                        depth, card_type, i + 1, num, 3, num, i, num, []
                    )
                    self.add_series(player, 3, i, num)
                    if ans:
                        return True
            return self.determine(depth, 11, 3, 1) if can_pass else False

        if card_type == 11:
            # 普通炸弹：点数须 >= beg；炸 2 之后 beg=16
            for i in range(15, beg - 1, -1):
                if self.card[player][i] >= 4:
                    self.card[player][i] -= 4
                    ans = self._after_play(depth, player, card_type, i + 1, num)
                    self.card[player][i] += 4
                    if ans:
                        return True
            # 王炸可压任何普通炸弹（含炸2，此时 beg=16）；不可压王炸（beg>=17）
            if beg <= 16 and self.has_series(player, 1, 16, 2):
                self.sub_series(player, 1, 16, 2)
                ans = self._after_play(depth, player, card_type, 17, num)
                self.add_series(player, 1, 16, 2)
                if ans:
                    return True
            if can_pass:
                if depth == 0:
                    self.new_card_record()
                return not self.determine(depth + 1, 0, 0, 0)
            return False

        # card_type == 12 四带二
        if num == 1 and not self.allow_four_two_singles:
            return self.determine(depth, 11, 3, 1) if can_pass else False
        if num == 2 and not self.allow_four_two_pairs:
            return self.determine(depth, 11, 3, 1) if can_pass else False

        for i in range(15, beg - 1, -1):
            if self.card[player][i] < 4:
                continue
            self.card[player][i] -= 4
            found = False
            if num == 1:
                for j in range(RANK_MIN, 16):
                    if j == i or self.card[player][j] < 1:
                        continue
                    for k in range(j, 16):
                        if k == i:
                            continue
                        ok = (
                            (j != k and self.card[player][k] >= 1)
                            or (j == k and self.card[player][j] >= 2)
                        )
                        if not ok:
                            continue
                        self.card[player][j] -= 1
                        self.card[player][k] -= 1
                        ans = self._after_play(depth, player, card_type, i + 1, num)
                        self.card[player][j] += 1
                        self.card[player][k] += 1
                        if ans:
                            found = True
                            break
                    if found:
                        break
            else:
                for j in range(RANK_MIN, 16):
                    if j == i or self.card[player][j] < 2:
                        continue
                    for k in range(j + 1, 16):
                        if k == i or self.card[player][k] < 2:
                            continue
                        self.card[player][j] -= 2
                        self.card[player][k] -= 2
                        ans = self._after_play(depth, player, card_type, i + 1, num)
                        self.card[player][j] += 2
                        self.card[player][k] += 2
                        if ans:
                            found = True
                            break
                    if found:
                        break
            self.card[player][i] += 4
            if ans:
                return True
        return self.determine(depth, 11, 3, 1) if can_pass else False

    def attach_finder(
        self,
        depth: int,
        card_type: int,
        beg: int,
        num: int,
        index: int,
        rest: int,
        body_beg: int,
        body_len: int,
        wing_ranks: List[int],
    ) -> bool:
        player = depth % 2
        need = card_type - 8
        if rest == 0:
            tmp = [0] * 18
            for r in wing_ranks:
                tmp[r] += need
            ok = (
                _valid_single_wings(tmp, body_beg, body_len)
                if need == 1
                else _valid_pair_wings(tmp, body_beg, body_len)
            )
            if not ok:
                return False
            return self._after_play(depth, player, card_type, beg, num)

        remain_cards = need * rest
        avail = 0
        for i in range(index, 16):
            if body_beg <= i < body_beg + body_len:
                continue
            avail += (self.card[player][i] // need) * need
        if avail < remain_cards:
            return False

        for i in range(index, 16):
            if body_beg <= i < body_beg + body_len:
                continue
            if self.card[player][i] >= need:
                self.card[player][i] -= need
                wing_ranks.append(i)
                ans = self.attach_finder(
                    depth, card_type, beg, num, i, rest - 1,
                    body_beg, body_len, wing_ranks,
                )
                wing_ranks.pop()
                self.card[player][i] += need
                if ans:
                    return True
        return False

    # ---------- 对弈交互 ----------
    def played_counts_from_diff(self) -> List[int]:
        counts = [0] * 18
        for i in range(RANK_MIN, RANK_MAX + 1):
            counts[i] = self.card[0][i] - self.new_card[0][i]
        return counts

    def apply_computer_move(self) -> Optional[Move]:
        counts = self.played_counts_from_diff()
        total = sum(counts)
        if total == 0:
            print("电脑出牌: 要不起（过牌）")
            for i in range(RANK_MIN, RANK_MAX + 1):
                self.card[0][i] = self.new_card[0][i]
            self.print_hands("电脑出牌后:")
            return None

        print(f"电脑出牌: {format_counts(counts)}")
        for i in range(RANK_MIN, RANK_MAX + 1):
            self.card[0][i] = self.new_card[0][i]
        self.print_hands("电脑出牌后:")

        moves = self.recognize(counts)
        if not moves:
            print("警告: 电脑出牌未能按规则识别，将按搜索约束继续。")
            return None
        if len(moves) > 1:
            # 搜索生成的着法若有歧义，取牌型编号较大者（炸弹优先于四带等已在识别阶段分流）
            moves.sort(key=lambda m: (m.card_type, m.main, m.length), reverse=True)
        move = moves[0]
        print(f"电脑牌型: {move.describe()}")
        return move

    def read_player_move(self, must_beat: Optional[Move]) -> Tuple[int, int, int]:
        """读入玩家出牌并自动识别；返回 determine 约束 (type, beg, num)。"""
        if self.is_empty(0):
            print("电脑已经出完——你输了！")
            sys.exit(0)

        while True:
            if must_beat is None:
                print("请出牌（自由出牌，回车确认；可空格分隔或连写）:")
                print("  例: 9    或    34567    或    3 4 5 6 7    或    AA10")
            else:
                print(f"请跟牌或要不起（需压过: {must_beat.describe()}）:")
                print("  出牌例: 9 / 34567 / AA10；要不起请直接回车（或输入 过）")

            line = sys.stdin.readline()
            if not line:
                sys.exit(0)
            raw = line.strip()

            # 要不起：空行，或过/pass/p/要不起
            pass_words = {"过", "pass", "p", "要不起", "不出"}
            if not raw or raw.lower() in pass_words:
                if must_beat is None:
                    print("自由出牌不能要不起，请重新出牌。")
                    continue
                self.print_hands("你要不起之后:")
                return 0, 0, 0

            try:
                tokens = tokenize_hand(raw)
            except ValueError as e:
                print(e)
                continue

            played_ranks: List[int] = []
            err = None
            for t in tokens:
                try:
                    r = parse_card_token(t)
                except ValueError as e:
                    err = str(e)
                    break
                played_ranks.append(r)

            if err:
                print(err)
                continue

            if not played_ranks:
                print("未解析到任何牌，请重新输入。")
                continue

            # 检查手牌是否拥有
            need = ranks_to_counts(played_ranks)
            if any(need[r] > self.card[1][r] for r in range(18)):
                print("错误: 你出的牌超出了手牌。")
                continue

            candidates = self.recognize(need)
            if not candidates:
                print("错误: 不符合合法牌型（例如顺子不能含 2/王；四个3只能当炸弹等）。")
                continue

            if must_beat is not None:
                candidates = [m for m in candidates if beats(m, must_beat)]
                if not candidates:
                    print("错误: 无法压过上家这一手牌（牌型/长度须相同，或使用更大炸弹/王炸）。")
                    continue

            if len(candidates) > 1:
                print("这手牌有多种合法解释，请选择：")
                for idx, m in enumerate(candidates, 1):
                    print(f"  {idx}. {m.describe()}")
                choice = None
                while choice is None:
                    sel = sys.stdin.readline().split()
                    if sel and sel[0].isdigit() and 1 <= int(sel[0]) <= len(candidates):
                        choice = candidates[int(sel[0]) - 1]
                    else:
                        print(f"请输入 1~{len(candidates)} 的序号")
                move = choice
            else:
                move = candidates[0]
                print(f"识别为: {move.describe()}")

            for r in range(18):
                self.card[1][r] -= need[r]
            self.print_hands("你出牌后:")
            if self.is_empty(1):
                if getattr(self, "_challenge_mode", False):
                    print("你已出完——挑战成功！先手并非必败（或实现有误）。")
                else:
                    print("你已出完，你赢了！")
                sys.exit(0)
            return move.to_constraint()

    def swap_hands(self) -> None:
        self.card[0], self.card[1] = self.card[1], self.card[0]
        self.new_card[0], self.new_card[1] = self.new_card[1], self.new_card[0]

    def reset_memo_and_flags(self) -> None:
        self.memo.clear()
        self.nodes = 0
        self.flag_series = [
            [[[False] * 16 for _ in range(18)] for _ in range(4)]
            for _ in range(2)
        ]
        self.flag_init()

    def ask_yes_no(self, prompt: str) -> bool:
        while True:
            print(prompt, end="", flush=True)
            line = sys.stdin.readline()
            if not line:
                return False
            ans = line.strip().lower()
            if ans in ("y", "yes", "是", "好", "1"):
                return True
            if ans in ("n", "no", "否", "不", "0"):
                return False
            print("请输入 y 或 n")

    def play_challenge(self) -> None:
        """换牌后由人类先手，电脑逐步回应，证明先手攻不破。"""
        self._challenge_mode = True
        if hasattr(self, "deadline"):
            self.deadline = None
        self.verbose_root = False
        print()
        print("=" * 48)
        print("挑战环节：双方交换手牌，由你先出。")
        print("电脑将尝试化解你的每一步；若你能出完则挑战成功。")
        print("=" * 48)
        self.swap_hands()
        self.reset_memo_and_flags()
        self.print_hands("换牌后的牌面:")
        print("由你先出（持原电脑的牌）。\n")

        card_type, beg, num = self.read_player_move(None)
        self.play_loop(card_type, beg, num)

    def play_loop(self, card_type: int, beg: int, num: int) -> None:
        """从给定约束起循环：电脑应招 → 玩家出牌。"""
        challenge = getattr(self, "_challenge_mode", False)
        while True:
            win = self.determine(0, card_type, beg, num)
            if win:
                last_move = self.apply_computer_move()
                if self.is_empty(0):
                    if challenge:
                        print("电脑出完。挑战失败：先手确实无法攻破。")
                    else:
                        print("电脑出完，你输了！")
                    sys.exit(0)
                card_type, beg, num = self.read_player_move(last_move)
            else:
                if challenge:
                    print("电脑无法应对——挑战成功！该局面下先手并非必败。")
                    sys.exit(0)
                if card_type == 0:
                    print("电脑认输：当前是「先手必败」局面。")
                    if self.ask_yes_no("是否交换手牌进入挑战（你先出，电脑证明攻不破）？(y/n): "):
                        self.play_challenge()
                    else:
                        print("你赢了！")
                        sys.exit(0)
                else:
                    print("电脑认输。你赢了！")
                    sys.exit(0)

    def play_after_first_win(self) -> None:
        """new_card 已记录必胜首着时，直接打出并进入对局（不再重算开局）。"""
        self._challenge_mode = False
        if hasattr(self, "deadline"):
            self.deadline = None
        self.verbose_root = False
        self.memo.clear()
        self.nodes = 0
        self.flag_init()
        print()
        print("=" * 48)
        print("进入对局：电脑先手必胜，按必胜着法出牌。")
        print("=" * 48)
        last_move = self.apply_computer_move()
        if self.is_empty(0):
            print("电脑出完，你输了！")
            sys.exit(0)
        card_type, beg, num = self.read_player_move(last_move)
        self.play_loop(card_type, beg, num)

    def play(self, computer_first: bool) -> None:
        self._challenge_mode = False
        card_type, beg, num = 0, 0, 0

        if not computer_first:
            print("由你先出。")
            card_type, beg, num = self.read_player_move(None)
        else:
            print("由电脑先出。")

        self.flag_init()
        self.play_loop(card_type, beg, num)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="斗地主 1v1 残局求解")
    parser.add_argument(
        "config",
        nargs="?",
        default="cases/gameset_simple.json",
        help="局面配置 JSON（默认 cases/gameset_simple.json）",
    )
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_file():
        # 相对脚本目录再试（便于在任意 cwd 下运行）
        alt = Path(__file__).resolve().parent / args.config
        if alt.is_file():
            path = alt
        else:
            # 只写了文件名时，自动到 cases/ 下找
            named = Path(__file__).resolve().parent / "cases" / Path(args.config).name
            if named.is_file():
                path = named
            else:
                print(f"找不到配置文件: {args.config}")
                sys.exit(1)

    game = Landlords()
    print("正在读取配置:", path.resolve())
    cfg = game.load_config(path)

    enabled = [f"{i}:{TYPE_NAMES[i]}" for i in range(1, 12) if game.type_allowed[i]]
    if game.allow_four_two_singles:
        enabled.append("12:四带两单")
    if game.allow_four_two_pairs:
        enabled.append("12:四带两对")
    print("启用牌型:", "，".join(enabled) if enabled else "（无）")
    game.print_hands("初始牌面:")

    if "computer_first" in cfg:
        computer_first = bool(cfg["computer_first"])
        print(f"先手: {'电脑' if computer_first else '玩家'}（来自配置）")
    else:
        while True:
            ans = input("电脑是否先手？(y/n): ").strip().lower()
            if ans in ("y", "n", "yes", "no", "是", "否"):
                computer_first = ans in ("y", "yes", "是")
                break
            print("请输入 y 或 n")

    print("对局开始！\n")
    game.play(computer_first)


if __name__ == "__main__":
    main()
