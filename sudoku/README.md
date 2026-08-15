# Sudoku Solvers

本仓库包含早期 C++ 数独求解器，以及用 Python 重构后的普通数独 / 摩天楼数独求解器。

## 目录结构

```
sudoku/
├── cpp/                      # 原始 C++ 版本
│   ├── sudoku.cpp
│   └── sudoku.txt            # 空格分隔的题面（0 = 空）
└── python/                   # Python 重构版
    ├── sudoku.py             # 普通数独
    ├── skyscraper_sudoku.py  # 摩天楼数独
    └── tests/                # 题面样例（JSON）
        ├── puzzle.json
        ├── puzzle2.json
        ├── skyscraper_puzzle1.json
        └── skyscraper_puzzle2.json
```

---

## C++ 版本

在 `cpp/` 目录下编译并运行（程序固定读写同目录的 `sudoku.txt` / `result.txt`）：

```bash
cd cpp
g++ -O2 -o sudoku sudoku.cpp
./sudoku          # Windows 下为 sudoku.exe
```

题面格式：每行 9 个整数，`0` 表示空格；可连续放多道题。

策略：唯一数、隐含唯一数、显性数对，不足时再试数回溯；找到一解即结束。

---

## Python 版本

依赖：Python 3.10+（仅标准库）。

### 普通数独

```bash
cd python
python sudoku.py                          # 默认 tests/puzzle.json，只求一解
python sudoku.py -i tests/puzzle2.json
python sudoku.py -i tests/puzzle.json --all   # 枚举全部解
```

| 参数 | 含义 |
|------|------|
| `-i` / `--input` | 题面 JSON 路径 |
| `-a` / `--all` | 搜索全部解（默认只返回第一个） |

### 摩天楼数独

```bash
cd python
python skyscraper_sudoku.py
python skyscraper_sudoku.py -i tests/skyscraper_puzzle2.json
python skyscraper_sudoku.py -i tests/skyscraper_puzzle1.json --all
```

参数与普通数独相同；默认题面为 `tests/skyscraper_puzzle1.json`。

---

## JSON 题面格式

### 普通数独

支持多种写法，任选其一。

**多题（数字矩阵）：**

```json
{
  "puzzles": [
    [
      [0, 0, 5, 3, 0, 0, 0, 0, 0],
      [8, 0, 0, 0, 0, 0, 0, 2, 0]
    ]
  ]
}
```

**单题（点阵字符串，`.` 或 `0` = 空，空格可忽略）：**

```json
{
  "board": [
    "8.. ... ...",
    "..3 6.. ...",
    ".7. .9. 2..",
    ".5. ..7 ...",
    "... .45 7..",
    "... 1.. .3.",
    "..1 ... .68",
    "..8 5.. .1.",
    ".9. ... 4.."
  ]
}
```

也可用 `"board": [[...9x9...]]`，或顶层直接放一个 / 多个 9×9 矩阵。

### 摩天楼数独

在 `board` 之外增加四边线索。每个数组长度为 9；**`0` 表示该位置无线索**。

```json
{
  "board": [
    ".3. 5.. .1.",
    "9.6 ... ..5",
    "8.1 ... 9..",
    "... ... ...",
    ".18 ... ...",
    "5.3 ... ..9",
    "... ... 6..",
    "1.. .3. ...",
    ".8. .51 .3."
  ],
  "skyscrapers": {
    "top":    [2, 4, 5, 4, 2, 1, 2, 3, 3],
    "bottom": [3, 2, 1, 3, 3, 4, 3, 2, 2],
    "left":   [3, 1, 2, 2, 3, 4, 3, 7, 3],
    "right":  [2, 3, 3, 2, 4, 1, 5, 2, 2]
  }
}
```

| 字段 | 含义 |
|------|------|
| `top` | 从上往下看每一列，可见摩天楼栋数 |
| `bottom` | 从下往上看每一列 |
| `left` | 从左往右看每一行 |
| `right` | 从右往左看每一行 |

数字表示楼高；从某一侧看去，只有比前面所有楼都高的楼才计入可见栋数。

---

## Python 相对 C++ 的改进

### 工程与接口

- **JSON 题面**：支持数字矩阵与点阵字符串，摩天楼线索一并写入文件，不必改代码。
- **结果打印到终端**，不再写死输出文件。
- **单解 / 全解**两种模式（`--all`）。
- **摩天楼数独**独立求解器（C++ 版无此变体）。
- 修复了原 C++ 隐含唯一数中 `num1 > 0` 漏掉第 0 列/行的问题。

### 约束传播（推演）

| C++ | Python |
|-----|--------|
| 唯一数（Naked Single） | 有 |
| 隐含唯一数（Hidden Single） | 有 |
| 显性数对（仅 size=2） | 显性数对 + **三元组** |
| — | **隐性数对 / 三元组** |
| — | **宫线消除**（指向数对 / Claiming） |
| — | **X-Wing** |

### 搜索策略

| C++ | Python |
|-----|--------|
| 按格顺序取第一个空格 | **MRV**：优先候选最少的格 |
| — | **Degree**：并列时优先约束更多空格的格 |
| 候选按 1…9 顺序试 | **LCV**：优先对同伴破坏更少的数字 |
| 找到一解即 `exit` | 可选继续搜索全部解 |

### 摩天楼专用（仅 Python）

- 线索为 `1` / `9` 时的极端直接填数
- 最高楼（9）相对线索的位置剪枝
- 单行/列可行性检测以删除不可能候选
- 部分填充时的可见性上界剪枝

---

## 算法概要

两者都是「约束传播 + 回溯」：先尽量用规则填数或删候选，卡住后再试数；Python 版规则更多、选点选值更优，通常分支更少。
