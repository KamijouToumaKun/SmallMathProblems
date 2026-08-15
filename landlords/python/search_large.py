#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大残局实验性求解器（与 landlords.py 主程序分离）

思路：分阶段开放牌型（由简到繁）。
  - 若在较简规则下已找到先手必胜 → 结论精确（多出来的牌型可以不用）
  - 若较简规则下先手必败 → 可能漏掉「靠飞机等」的胜着，升级到下一阶段
  - 最后一阶段使用 JSON 中的完整规则，结论才对「必败」精确

用法：
  python search_large.py cases/gameset_case2_hard.json
  python search_large.py gameset_case2_hard.json --time 120
  python search_large.py cases/gameset_case2_hard.json --phase full
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from landlords import TYPE_NAMES, Landlords, format_counts


class SearchTimeout(Exception):
    pass


@dataclass(frozen=True)
class Phase:
    name: str
    # 启用的牌型编号 1..11；12 用 singles/pairs 单独控制
    types: frozenset
    four_two_singles: bool = False
    four_two_pairs: bool = False
    description: str = ""


# 由简到繁；可按需要改顺序或增删
PHASES: List[Phase] = [
    Phase(
        "basic",
        frozenset({1, 2, 3, 11}),
        description="单/对/三 + 炸弹",
    ),
    Phase(
        "straight",
        frozenset({1, 2, 3, 6, 7, 8, 11}),
        description="加上单顺/双顺/三顺",
    ),
    Phase(
        "kickers",
        frozenset({1, 2, 3, 4, 5, 6, 7, 8, 11}),
        description="加上三带一/三带二",
    ),
    Phase(
        "plane",
        frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}),
        description="加上飞机带翅膀",
    ),
    Phase(
        "full",
        frozenset(range(1, 12)),
        four_two_singles=True,
        four_two_pairs=True,
        description="JSON 允许的全部牌型（含四带二）",
    ),
]


class LargeLandlords(Landlords):
    """在 landlords 搜索上增加超时与进度汇报。"""

    def __init__(self) -> None:
        super().__init__()
        self.deadline: Optional[float] = None
        self.progress_every = 250_000
        self._last_report_nodes = 0
        self._t0 = 0.0
        self.verbose_root = False

    def determine(
        self,
        depth: int,
        card_type: int,
        beg: int,
        num: int,
        can_pass: bool = True,
    ) -> bool:
        if self.deadline is not None and time.perf_counter() >= self.deadline:
            raise SearchTimeout()
        ans = Landlords.determine(self, depth, card_type, beg, num, can_pass)
        if self.nodes - self._last_report_nodes >= self.progress_every:
            self._last_report_nodes = self.nodes
            elapsed = time.perf_counter() - self._t0
            nps = self.nodes / elapsed if elapsed > 0 else 0
            print(
                f"  … nodes={self.nodes} memo={len(self.memo)} "
                f"time={elapsed:.1f}s nps={nps:.0f}",
                flush=True,
            )
        return ans


def resolve_config(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_file():
        return path
    here = Path(__file__).resolve().parent
    alt = here / path_str
    if alt.is_file():
        return alt
    named = here / "cases" / Path(path_str).name
    if named.is_file():
        return named
    raise FileNotFoundError(path_str)


def snapshot_rules(game: Landlords) -> Dict:
    return {
        "type_allowed": list(game.type_allowed),
        "singles": game.allow_four_two_singles,
        "pairs": game.allow_four_two_pairs,
    }


def snapshot_cards(game: Landlords) -> Dict:
    return {
        "card": [row[:] for row in game.card],
        "new_card": [row[:] for row in game.new_card],
    }


def restore_rules(game: Landlords, snap: Dict) -> None:
    game.type_allowed = list(snap["type_allowed"])
    game.allow_four_two_singles = snap["singles"]
    game.allow_four_two_pairs = snap["pairs"]


def restore_cards(game: Landlords, snap: Dict) -> None:
    game.card = [row[:] for row in snap["card"]]
    game.new_card = [row[:] for row in snap["new_card"]]


def apply_phase(game: Landlords, base: Dict, phase: Phase) -> None:
    """在 JSON 允许的前提下，只打开本阶段牌型。"""
    base_types: Sequence[bool] = base["type_allowed"]
    for i in range(1, 12):
        game.type_allowed[i] = bool(base_types[i]) and (i in phase.types)
    want_s = phase.four_two_singles and base["singles"]
    want_p = phase.four_two_pairs and base["pairs"]
    # full 阶段：跟 JSON；此前阶段默认不开四带二，除非 phase 显式打开且 JSON 允许
    if phase.name != "full":
        game.allow_four_two_singles = want_s
        game.allow_four_two_pairs = want_p
    else:
        game.allow_four_two_singles = base["singles"]
        game.allow_four_two_pairs = base["pairs"]
        for i in range(1, 12):
            game.type_allowed[i] = bool(base_types[i])
    game.type_allowed[12] = game.allow_four_two_singles or game.allow_four_two_pairs


def describe_enabled(game: Landlords) -> str:
    parts = [TYPE_NAMES[i] for i in range(1, 12) if game.type_allowed[i]]
    if game.allow_four_two_singles:
        parts.append("四带两单")
    if game.allow_four_two_pairs:
        parts.append("四带两对")
    return "、".join(parts) if parts else "（无）"


def run_phase(
    game: LargeLandlords,
    phase: Phase,
    time_limit: Optional[float],
    cards_snap: Dict,
) -> Tuple[str, Optional[bool], int, float]:
    """
    返回 (status, win, nodes, seconds)
    status: ok | timeout
    无论正常结束还是超时，结束后都恢复开局牌面（超时会中断回溯，牌面可能脏）。
    """
    restore_cards(game, cards_snap)
    game.memo.clear()
    game.nodes = 0
    game._last_report_nodes = 0
    game._t0 = time.perf_counter()
    game.deadline = (game._t0 + time_limit) if time_limit and time_limit > 0 else None
    try:
        win = game.determine(0, 0, 0, 0)
        dt = time.perf_counter() - game._t0
        # 保留 new_card 中的必胜首着，仅在胜利时有用；牌面 card 本身应已还原
        # determine 正常返回时 card 已被回溯干净；再保险一次：
        opening = [row[:] for row in cards_snap["card"]]
        first_remain = [row[:] for row in game.new_card]
        restore_cards(game, cards_snap)
        if win:
            # 恢复「开局牌面 + 记下的出完后牌面」，供对局打出首着
            game.card = opening
            game.new_card = first_remain
        return "ok", win, game.nodes, dt
    except SearchTimeout:
        dt = time.perf_counter() - game._t0
        restore_cards(game, cards_snap)
        game.memo.clear()
        return "timeout", None, game.nodes, dt


def enter_play_or_challenge(
    game: LargeLandlords,
    base: Dict,
    cards_snap: Dict,
    *,
    first_wins: bool,
    loss_exact: bool,
) -> None:
    """搜索结束后进入对局或挑战。对局使用 JSON 完整规则。"""
    restore_rules(game, base)
    game.deadline = None
    game.verbose_root = False

    if first_wins:
        # card/new_card 已由 run_phase 在胜利时设好
        game.play_after_first_win()
        return

    # 必败：确保是完整开局牌面再换牌挑战
    restore_cards(game, cards_snap)
    print("结论: 先手必败" + ("（完整规则下已证）。" if loss_exact else "（当前阶段结论，可能尚不完整）。"))
    if not loss_exact:
        print("提示: 非 full 阶段的必败未必精确；挑战按完整 JSON 规则进行。")
    if game.ask_yes_no("是否交换手牌进入挑战（你先出，电脑证明攻不破）？(y/n): "):
        game.memo.clear()
        game.nodes = 0
        game.play_challenge()
    else:
        print("未进入挑战。你赢了！")


def solve_large(
    config: Path,
    *,
    time_limit: Optional[float] = None,
    only_phase: Optional[str] = None,
    start_phase: Optional[str] = None,
    no_play: bool = False,
) -> int:
    game = LargeLandlords()
    print("正在读取:", config.resolve())
    game.load_config(config)
    game.flag_init()
    base = snapshot_rules(game)
    cards0 = snapshot_cards(game)

    print(f"牌数: 电脑 {game.hand_total(0)} / 玩家 {game.hand_total(1)}")
    print(f"电脑: {game.hand_str(0)}")
    print(f"玩家: {game.hand_str(1)}")
    print(f"JSON 规则: {describe_enabled(game)}")
    print()

    phases = PHASES
    if only_phase:
        phases = [p for p in PHASES if p.name == only_phase]
        if not phases:
            print(f"未知阶段 {only_phase!r}，可选: {[p.name for p in PHASES]}")
            return 2
    elif start_phase:
        idx = next((i for i, p in enumerate(PHASES) if p.name == start_phase), None)
        if idx is None:
            print(f"未知阶段 {start_phase!r}")
            return 2
        phases = PHASES[idx:]

    per_phase_limit = time_limit
    if time_limit and time_limit > 0 and len(phases) > 1 and only_phase is None:
        per_phase_limit = max(5.0, time_limit / len(phases))

    print("=== 大残局分阶段搜索 ===")
    print("说明: 简规则下的「必胜」可直接采信；「必败」需升到更全规则再确认。")
    if time_limit:
        print(f"总时限约 {time_limit:.0f}s（每阶段约 {per_phase_limit:.0f}s）")
    print()

    last_loss_phase = None
    for phase in phases:
        apply_phase(game, base, phase)
        print(f"▶ 阶段 [{phase.name}] {phase.description}")
        print(f"  启用: {describe_enabled(game)}")

        status, win, nodes, dt = run_phase(game, phase, per_phase_limit, cards0)
        nps = nodes / dt if dt > 0 else 0
        if status == "timeout":
            print(f"  超时 nodes={nodes} time={dt:.2f}s nps={nps:.0f}")
            print("  → 本阶段未完成（已恢复开局牌面），进入下一阶段或结束。\n")
            continue

        print(f"  结果: 先手{'必胜' if win else '必败'}  nodes={nodes} time={dt:.2f}s nps={nps:.0f}")

        if win:
            diff = [0] * 18
            for i in range(3, 18):
                diff[i] = game.card[0][i] - game.new_card[0][i]
            played = format_counts(diff)
            print(f"  首着: {played if sum(diff) else '（过牌/未知）'}")
            print()
            print(f"结论: 先手必胜（在阶段 [{phase.name}] 已证；对完整规则亦成立）。")
            if no_play:
                restore_rules(game, base)
                restore_cards(game, cards0)
                return 0
            enter_play_or_challenge(
                game, base, cards0, first_wins=True, loss_exact=True
            )
            return 0

        last_loss_phase = phase.name
        if phase.name != phases[-1].name:
            print("  → 简规则下未见胜着，升级牌型再搜。\n")
        else:
            print()

    restore_rules(game, base)
    restore_cards(game, cards0)
    if last_loss_phase == "full" or (only_phase and last_loss_phase):
        loss_exact = last_loss_phase == "full"
        if no_play:
            print(
                "结论: 先手必败"
                + ("（完整规则下已证）。" if loss_exact else f"（阶段 [{last_loss_phase}]，可能不精确）。")
            )
            return 0
        enter_play_or_challenge(
            game, base, cards0, first_wins=False, loss_exact=loss_exact
        )
        return 0

    if last_loss_phase:
        print(
            f"结论: 尚未在完整规则下证伪；最后完成的阶段 [{last_loss_phase}] 显示必败（可能不精确）。"
        )
        print("可加大 --time，或 --phase full 单跑完整规则。")
        if not no_play and game.ask_yes_no("仍按该结论进入换牌挑战？(y/n): "):
            enter_play_or_challenge(
                game, base, cards0, first_wins=False, loss_exact=False
            )
            return 0
        return 1

    print("结论: 所有阶段均超时，无结果。每一个阶段都在时限内未算完，所以既不能判定先手必胜，也不能判定先手必败。")
    print("提示: 可以加大 --time 参数，或 --phase full 单跑完整规则。")
    return 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="大残局实验性求解（分阶段开放牌型）"
    )
    parser.add_argument(
        "config",
        nargs="?",
        default="cases/gameset_case2_hard.json",
        help="局面 JSON（默认 cases/gameset_case2_hard.json）",
    )
    parser.add_argument(
        "--time",
        type=float,
        default=180.0,
        help="总时限秒数（默认 180；0 表示不限制）",
    )
    parser.add_argument(
        "--phase",
        choices=[p.name for p in PHASES],
        default=None,
        help="只跑某一个阶段",
    )
    parser.add_argument(
        "--start",
        choices=[p.name for p in PHASES],
        default=None,
        help="从某一阶段开始往后跑",
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="只搜索、打印结论，不进入对局/挑战",
    )
    args = parser.parse_args()
    try:
        path = resolve_config(args.config)
    except FileNotFoundError:
        print(f"找不到配置: {args.config}")
        return 2

    tlim = None if args.time <= 0 else args.time
    return solve_large(
        path,
        time_limit=tlim,
        only_phase=args.phase,
        start_phase=args.start,
        no_play=args.no_play,
    )


if __name__ == "__main__":
    sys.exit(main())
