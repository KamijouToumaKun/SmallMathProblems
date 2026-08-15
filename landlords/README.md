# 斗地主 1v1 残局求解

完全信息二人零和残局：电脑与人类对弈，搜索必胜着法（记忆化博弈搜索）。

```
landlords/
├── cpp/                 # 原版 C++ 程序
│   ├── landlords.cpp
│   └── gameset.txt
└── python/              # 重构后的 Python 版（推荐）
    ├── landlords.py     # 主程序（对弈 + 标准搜索）
    ├── search_large.py  # 大残局实验性分阶段搜索
    └── cases/           # 局面 JSON
        ├── gameset_simple.json
        ├── gameset_case1.json
        └── …
```

---

## Python 版使用方法

### 环境

- Python 3.8+（仅标准库，无需额外依赖）

### 运行

```bash
cd python
python landlords.py                         # 默认 cases/gameset_simple.json
python landlords.py cases/gameset_case16.json
python landlords.py gameset_case16.json     # 也可只写文件名（自动在 cases/ 下查找）
```

### 大残局实验搜索

`case2_hard` 等牌很多时，可用独立脚本做**分阶段开放牌型**尝试（简规则下的必胜可直接采信）：

```bash
cd python
python search_large.py cases/gameset_case2_hard.json
python search_large.py gameset_case2_hard.json --time 300
python search_large.py gameset_case2_hard.json --phase basic   # 只跑单/对/三/炸弹
python search_large.py gameset_case2_hard.json --start plane   # 从飞机阶段开始
python search_large.py gameset_case1.json --no-play            # 只搜索不对弈
```

搜出**先手必胜**后会进入对局（电脑按必胜着法出牌）；**先手必败**时会询问是否换牌挑战。

### 配置文件（JSON）

```json
{
  "computer_first": true,
  "rules": {
    "single": true,
    "pair": true,
    "triple": true,
    "triple_one": true,
    "triple_two": true,
    "straight": true,
    "double_straight": true,
    "triple_straight": true,
    "plane_with_singles": true,
    "plane_with_pairs": true,
    "bomb": true,
    "four_with_two": false,
    "four_with_two_pairs": false
  },
  "computer": "bsAAAA43",
  "player": "22225"
}
```

| 字段 | 说明 |
|------|------|
| `computer_first` | 是否电脑先手；可省略，运行时会询问 |
| `rules` | 启用哪些牌型；也可用长度为 12 的布尔数组（第 12 项仅表示四带两单；四带两对请用对象写法） |
| `computer` / `player` | 双方手牌 |

**手牌写法（推荐连写字符串）：**

- 连写：`"2QQ101077553"`、`"AA9"`、`"bsAAAA43"`
- 也可用空格：`"A 10 10"`
- 兼容旧写法：`["A", "10", "10"]`
- 点数：`3`–`10`、`J`/`Q`/`K`/`A`/`2`，小王 `s`，大王 `b`（大小写不敏感于 JQKA）
- 连写时 `10` 按两字符优先识别（`1010` = 两张 10）

**`rules` 键与牌型对应：**

| 键 | 牌型 |
|----|------|
| `single` | 单张 |
| `pair` | 对子 |
| `triple` | 三张 |
| `triple_one` | 三带一 |
| `triple_two` | 三带二 |
| `straight` | 单顺 |
| `double_straight` | 双顺 |
| `triple_straight` | 三顺（飞机不带翼） |
| `plane_with_singles` | 飞机带单 |
| `plane_with_pairs` | 飞机带对 |
| `bomb` | 炸弹 / 王炸 |
| `four_with_two` | 四带两单（默认 `false`） |
| `four_with_two_pairs` | 四带两对（默认 `false`；需在 JSON 中显式设为 `true` 才启用） |

### 对弈操作

1. 程序求解后走出**必胜着**（若存在），并打印牌型。
2. 轮到你时：
   - **出牌**：回车确认；可空格分隔或连写，例如 `9`、`3 4 5 6 7`、`34567`、`AA10`
   - **要不起**：直接回车，或输入 `过` / `pass` / `要不起`
3. 程序会**自动识别牌型**；若有多种合法解释，再让你选序号。
4. 会校验：是否拥有该牌、是否合法牌型、能否压过上家。

### 挑战环节

当局面被判定为**当前行棋方先手必败**（电脑认输）时，可选择：

1. 双方**交换剩余手牌**
2. 由你先出
3. 电脑用后手必胜策略应对；若你能出完则挑战成功，否则先手确败

用于人工检验「先手必败」结论。

### 示例局面

| 文件 | 说明 |
|------|------|
| `cases/gameset_simple.json` | 小残局，便于试玩 |
| `cases/gameset_case1.json` 等 | 逐步补充的残局 |
| `cases/gameset_case2_hard.json` | 大牌面，建议用 `search_large.py` |

---

## 相对 C++ 版的主要改动

### 输入与交互

| | C++ | Python |
|---|-----|--------|
| 局面配置 | `gameset.txt`（规则 0/1 + 牌以 `0` 结尾） | JSON，手牌可连写 |
| 出牌结束符 | 必须以 `0` 结尾 | 回车即可 |
| 牌型说明 | 每次出牌后手动输入「类型 起点 长度」 | 自动识别（歧义时再选） |
| 合法性 | 基本不检查（`without checking`） | 校验手牌、牌型、跟牌 |
| 界面语言 | 英文提示为主 | 中文 |

### 规则与正确性

- 按常见**竞技二打一 / 官方玩法**收紧：
  - 顺子 / 连对 / 飞机机身不含 `2` 与王
  - 四个同点只认炸弹，不当「三带一」
  - 三带、四带二、飞机翅膀等带牌约束（如翅膀不含王等）
- **修复王炸与「炸弹 2」约束冲突**（C++ 原版同样存在）：
  - 旧逻辑在炸出 `2` 后 `beg=16`，导致王炸无法压炸 2
  - 现改为：王炸可压任意普通炸弹；王炸之后用 `beg=17` 与炸 2 区分
- 支持四带二的「带两对」形态（C++ 侧重点在带两单）

### 算法与性能

- 仍为**记忆化极大极小 / OR-AND 搜索**，求精确胜负与必胜着
- 相对原版增强：
  - **跟牌局面也记忆化**（不只自由出牌点）
  - 位压缩牌面作字典键
  - 一手出完即胜的剪枝、按实际最长顺限制搜索长度
  - 着法顺序与带牌枚举剪枝等
- 大残局（如 case2/3）仍可能较慢，尚未上 Proof-Number 等更强框架

### 功能扩展

- 先手必败时的**换牌挑战**
- 规则开关与局面用 JSON 管理，便于批量造 case

### 未改动的部分

- 核心仍是 1v1 残局精确求解，不是完整三人斗地主 AI
- C++ 目录保留原程序，便于对照；日常使用以 `python/` 为准

---

## C++ 版（简要）

```bash
cd cpp
# 按本地环境编译 landlords.cpp 后运行
# 编辑 gameset.txt：第一行 12 个规则开关，第二三行双方牌（以 0 结尾）
```

交互需手动声明牌型编号与起点，细节见 `landlords.cpp` 文件头注释。
