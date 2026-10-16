# B-1 改判表：67 条 `boundary` 字段化（★ 人读；⛔ 不可机检的内容判断）

> 生成件：`16-checkpoint/_b1_emit_review.py`（只读 `dag.json` 摆表，⛔ 不改数据）
> 上游：`CRITERIA-CHANGE-P05.md` §3 C3（`boundary` 由可选转必填）· `CONTINUE-PROMPT-D4.md` §B-1
> 登记：`CRITERIA-CHANGE-P05-R5.md`

## 改判纪律（逐条核的就是这三条）

1. **切分口径与渲染同源**：`gen-common.split_boundary` 的**显式标记**查找（`适用边界是`；`PE-R-02` 用变体 `适用边界必须写清：`）。⛔ 不新写关键词正则 —— 实测 `…而是边界：` 是**主题词**会被误捕（`PE-F-03`），而真正的边界句反而漏捕。
2. **双标记节点的合并规则**：9 个节点在 `why` 与 `intro` 两处各写了一遍边界，两版**近乎重复**。统一**保留 `why` 版、移除 `intro` 版** —— 理由：逐条比对后 `why` 版一致地更完整（`PE-R-02` 两版逐字相同，属纯去重）。⛔ 该规则是**可复核的取舍**，不是唯一正确解；如有异议按下表逐条改。
3. **两条 `complete` 节点的 intro 补写**：移除 intro 版边界后，`PE-R-02` 的 intro 主体降到 122、`PE-P-02` 降到 143，**跌破 `complete` 的 intro 下限 150** ⇒ 按「⛔ 不降下限」的纪律，改为**补写机制句**（分别 +82 / +50 caliber，内容 += 判据的落地方式 / 两条原则的对冲关系），改写后为 204 / 193。

## 表（67 行；caliber 口径 = 汉字数 + 拉丁词数）

| 节点 | 状态 | boundary | why 主体 | intro 主体 | 备注（人核） |
|---|---|---:|---:|---:|---|
| `PE-F-01` | complete | 52 | 114 | 188 | — |
| `PE-F-02` | complete | 49 | 119 | 188 | — |
| `PE-F-03` | complete | 64 | 95 | 205 | — |
| `PE-F-04` | complete | 39 | 126 | 193 | — |
| `PE-F-05` | complete | 74 | 94 | 175 | — |
| `PE-F-06` | complete | 50 | 98 | 190 | — |
| `PE-S-01` | complete | 62 | 148 | 284 | — |
| `PE-S-02` | complete | 95 | 188 | 266 | — |
| `PE-S-03` | complete | 109 | 113 | 299 | — |
| `PE-S-04` | complete | 82 | 130 | 275 | — |
| `PE-S-05` | complete | 199 | 148 | 415 | — |
| `PE-R-01` | registered | 58 | 92 | 217 | — |
| `PE-R-02` | complete | 57 | 118 | 204 | 双标记：保留 why 版、移除 intro 版 |
| `PE-R-03` | registered | 55 | 116 | 129 | 双标记：保留 why 版、移除 intro 版 |
| `PE-R-04` | registered | 54 | 147 | 197 | — |
| `PE-R-05` | registered | 57 | 79 | 228 | — |
| `PE-R-06` | registered | 61 | 95 | 177 | — |
| `PE-R-07` | registered | 68 | 85 | 142 | 双标记：保留 why 版、移除 intro 版 |
| `PE-R-08` | registered | 52 | 88 | 194 | — |
| `PE-C-01` | registered | 45 | 105 | 145 | 双标记：保留 why 版、移除 intro 版 |
| `PE-C-02` | registered | 50 | 80 | 213 | — |
| `PE-C-03` | registered | 70 | 78 | 223 | — |
| `PE-C-04` | registered | 50 | 69 | 202 | — |
| `PE-C-05` | registered | 71 | 65 | 216 | — |
| `PE-C-06` | registered | 64 | 68 | 206 | — |
| `PE-C-07` | registered | 57 | 98 | 178 | — |
| `PE-O-01` | registered | 47 | 95 | 213 | — |
| `PE-O-02` | registered | 49 | 83 | 187 | — |
| `PE-O-03` | registered | 39 | 82 | 213 | — |
| `PE-O-04` | registered | 57 | 89 | 156 | — |
| `PE-O-05` | registered | 62 | 76 | 213 | — |
| `PE-O-06` | registered | 47 | 70 | 191 | — |
| `PE-O-07` | registered | 52 | 86 | 161 | — |
| `PE-O-08` | registered | 51 | 71 | 212 | — |
| `PE-E-01` | registered | 53 | 74 | 212 | — |
| `PE-E-02` | registered | 40 | 84 | 191 | — |
| `PE-E-03` | registered | 46 | 67 | 219 | — |
| `PE-E-04` | registered | 44 | 92 | 189 | — |
| `PE-E-05` | registered | 50 | 80 | 221 | — |
| `PE-E-06` | registered | 53 | 80 | 197 | — |
| `PE-E-07` | registered | 46 | 85 | 199 | — |
| `PE-E-08` | registered | 49 | 69 | 222 | — |
| `PE-E-09` | registered | 48 | 61 | 217 | — |
| `PE-A-01` | registered | 60 | 82 | 149 | 双标记：保留 why 版、移除 intro 版 |
| `PE-A-02` | registered | 47 | 100 | 173 | — |
| `PE-A-03` | registered | 52 | 85 | 208 | — |
| `PE-A-04` | registered | 49 | 78 | 199 | — |
| `PE-A-05` | registered | 58 | 90 | 193 | — |
| `PE-A-06` | registered | 57 | 80 | 223 | — |
| `PE-M-01` | registered | 50 | 70 | 207 | — |
| `PE-M-02` | registered | 64 | 90 | 196 | — |
| `PE-M-03` | registered | 71 | 84 | 216 | — |
| `PE-M-04` | registered | 52 | 65 | 194 | — |
| `PE-V-01` | registered | 51 | 75 | 206 | — |
| `PE-V-02` | registered | 49 | 97 | 221 | — |
| `PE-V-03` | registered | 52 | 78 | 183 | — |
| `PE-P-01` | registered | 44 | 90 | 188 | — |
| `PE-P-02` | complete | 66 | 114 | 193 | 双标记：保留 why 版、移除 intro 版 |
| `PE-P-03` | registered | 67 | 74 | 166 | — |
| `PE-P-04` | registered | 50 | 97 | 212 | — |
| `PE-P-05` | registered | 56 | 78 | 208 | — |
| `PE-P-06` | registered | 66 | 69 | 146 | 双标记：保留 why 版、移除 intro 版 |
| `PE-P-07` | registered | 51 | 98 | 185 | — |
| `PE-N-01` | registered | 58 | 91 | 151 | 双标记：保留 why 版、移除 intro 版 |
| `PE-N-02` | registered | 47 | 87 | 226 | — |
| `PE-N-03` | registered | 46 | 94 | 155 | 双标记：保留 why 版、移除 intro 版 |
| `PE-N-04` | registered | 50 | 71 | 207 | — |

## 统计

- 行数：67
- `boundary` 为空的：0
- 正文残留引导串的：0
- boundary caliber 区间：39 – 199
- `why` 主体 caliber 区间：61 – 188（下限：complete 80 / registered 60）
- `intro` 主体 caliber 区间：129 – 415（下限：complete 150 / registered 120）
- 跌破各自下限的：0（由 `gate_prototype.py` P05 与 `10-dag-data/_selfcheck.py` C28c 逐条机检）

