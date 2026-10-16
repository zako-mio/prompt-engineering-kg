# G5 · 真实渲染验证通道（RENDER-CHANNEL）

**状态：通道已建立并实测通过。** 本文件是通道的操作说明与证据索引。

---

## 一、结论先行

| 项 | 值 |
|---|---|
| 通道 | `playwright-python` → 非 snap Chromium |
| 浏览器路径 | `~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome` |
| 浏览器版本 | Google Chrome for Testing **153.0.8010.12**（`file` 判定：ELF 64-bit LSB pie executable, x86-64） |
| 驱动 | Python `playwright` **1.63.0**（`~/.local/lib/python3.12/site-packages/playwright`） |
| 通道脚本 | `04-prototype/16-checkpoint/_render.py` |
| 便捷入口 | `04-prototype/16-checkpoint/_render.sh` |
| 网络 | 可用（`curl -sI https://registry.npmjs.org/` ⇒ `HTTP/2 200`），但**本通道不需要联网** |
| 确定性 | **逐字节可复现**（同参两次渲染 sha256 完全一致） |
| 中文 | **真字形**，非豆腐块（逐字墨迹指纹 22/22 互异） |

---

## 二、为什么必须换通道（负对照，原始报错）

任务书给出的两条已失败通道，**我复现了，但根因与任务书描述不同**，以实测为准：

### 2.1 实测报错（原始输出）

```
$ /snap/bin/chromium --version
snap-confine is packaged without necessary permissions and cannot continue
required permitted capability cap_dac_override not found in current capabilities:
  =: Operation canceled
```

`/usr/bin/chromium-browser` 与 `snap run chromium` **报同一条错**：

```
$ /usr/bin/chromium-browser --headless --disable-gpu --no-sandbox \
      --screenshot=/tmp/g5_n3.png about:blank
snap-confine is packaged without necessary permissions and cannot continue
required permitted capability cap_dac_override not found in current capabilities:
  =: Operation canceled
```

### 2.2 ★ 根因修正（与任务书假设不符）

| 任务书假设 | 实测事实 |
|---|---|
| `/run/user/1000/snap.chromium` 在本会话内**只读** | 该目录**存在且可写**：`drwx------ 2 zako-mio zako-mio` ⇒ `touch` 成功，回显 `WRITABLE` |
| 失败发生在「创建 XDG_RUNTIME_DIR 文件夹」阶段 | 失败发生在**更早的 snap-confine 启动阶段**，根本没走到创建目录那一步 |

真实根因是 **capability 缺失**：

```
$ grep CapEff /proc/self/status
CapInh: 0000000000000000
CapPrm: 0000000000000000
CapEff: 0000000000000000      <-- 有效集为空
CapBnd: 000001ffffffffff

$ capsh --print | head -3
Current: =                    <-- 空集
Bounding set =cap_chown,cap_dac_override,...
```

而 `snap-confine` 是 **file-capability** 程序，需要从文件上取 `cap_dac_override`：

```
$ getcap /usr/lib/snapd/snap-confine
/usr/lib/snapd/snap-confine cap_chown,cap_dac_override,cap_dac_read_search,
  cap_fowner,cap_setgid,cap_setuid,cap_sys_chroot,cap_sys_ptrace,
  cap_sys_admin,cap_sys_resource=p
```

会话内 `CapBnd` 含该位但 `CapPrm/CapEff` 为空，且 `no-new-privs=1`
（`capsh` 输出：`Securebits: 00/0x0/1'b0 (no-new-privs=1)`），
文件能力无法被提升进有效集 ⇒ snap 路径在本会话内**结构性不可用**，
且**改 `XDG_RUNTIME_DIR` 无效**（失败在更早一层，与任务书观察一致）。

### 2.3 通道 3（agent-browser 0.34.0）—— ★ 假成功，必须弃用

任务书记为「报同一条错误」。实测**报错形式变了，但更危险**：

```
$ agent-browser screenshot about:blank
✓ Screenshot saved to /home/zako-mio/.agent-browser/tmp/screenshots/screenshot-1792055215057.png
```

它**声称成功**。但核验像素：

```
size=(1280, 577)  uniq_colors=1  top_left=(255, 255, 255)
```

⇒ **纯白 1 色空图**。对真实页面再测，它把 `--output` 当字面文件名，产出 `./--output`，目标 PNG 根本不存在。
**判定：agent-browser 在本机是「假绿」通道，会静默产出空图，禁止用于视觉验证。**

---

## 三、用法

```bash
cd <workspace>

# 直接调用通道本体
python3 04-prototype/16-checkpoint/_render.py \
    --html 04-prototype/index.html \
    --width 1440 --height 900 \
    --out 04-prototype/16-checkpoint/_render-proof/index.png

# 便捷入口
04-prototype/16-checkpoint/_render.sh 04-prototype/index.html 1440 900 /tmp/out.png
```

参数：`--html --out --width --height --dsf --theme{light,dark} --root --full --json --quiet`

**站点根自动探测**：脚本从 HTML 所在目录向上找含 `assets/` 的目录作为文档根。
因为样式块里写的是 `../assets/backdrop/*.webp`（相对**站点根**，不是相对 HTML），
所以 `04-prototype/` 才是文档根。脚本内部起临时 `http.server`（`127.0.0.1:<随机端口>`），
⛔ **不要用 `file://` 直开**（背景素材会 404）。

---

## 四、确定性保证（逐条）

1. 固定视口 + 固定 `device_scale_factor` + `--force-device-scale-factor`
2. 显式 `color_scheme=light`（该站 `data-theme="auto"` + `@media (prefers-color-scheme:dark)`
   ⇒ 不固定则浅/深色产出不同 PNG）；可用 `--theme dark` 显式切深色
3. `reduced_motion="reduce"` + 注入 CSS 把 `animation/transition` 冻到终态
   （该站有 `@keyframes reveal-in` 入场动画，不冻结会截到动画中途帧）
4. `localStorage.clear()`（该站用 `localStorage` 存主题/动效/背景/字号偏好）
5. 等 `document.fonts.ready` + 所有 `<img>` complete + `networkidle`
6. 页面脚本自身**无** `Date()` / `Math.random()` / `performance.now()`（已 grep 核查）
7. 全部资源来自本地静态服务器，无外部网络依赖

**实测**：`index.html` 两次渲染 sha256 均为 `80d9336de07eb135…`；
`pe-f-01.html` 两次均为 `dc580d62b15ee51a…` ⇒ **逐字节一致**。

---

## 五、验收证据

### 5.1 渲染产物

| PNG | 尺寸 | sha256(前16) | 字节 |
|---|---|---|---|
| `_render-proof/index.png` | 1440×900 | `80d9336de07eb135` | 453785 |
| `_render-proof/pe-f-01.png` | 1440×900 | `dc580d62b15ee51a` | 362642 |
| `_render-proof/index.dark.png` | 1440×900 | `372649ce134fe434` | 930857 |
| `_render-proof/index.backdrop-off.png` | 1440×900 | `ee98ea1e03e6fdd8` | — |

PIL 判定：`index.png` 唯一色 **4547** 色，9×9 抽样亮度 **22.4 – 255.0**，非全白非全黑；
`pe-f-01.png` 唯一色 **4569** 色，同样非全白非全黑。

### 5.2 CSS 已应用的 3 处硬证据

1. **样式表真的解析了**：`document.styleSheets` 计数 `sheets=2, rules=202`；
   服务器侧 `200 /index.html`、`200 /assets/backdrop/day-2560.webp`、`200 /assets/favicon.svg`。
   计算样式探针：`bodyBg=rgb(244,247,252)`、`bodyColor=rgb(14,23,41)`、
   `h1Size=41.28px`、`bodySize=16px` —— 全是 CSS 令牌算出来的值，不是 UA 默认（UA 默认是白底黑字 32px h1）。
2. **背景摄影素材真的画进了像素**：A/B 实验（`data-backdrop` on vs off）
   像素差 `bbox=(0,0,1440,900)`，抽样 36000 点中 **9960 点（27.7%）被改变**，
   最大通道和差 **169**；且深色主题下 `.backdrop__photo--night` 的
   `background-image` 解析为 `night-1920.webp` 并 `display:block`，PNG 中可见真实星野与星云细节。
3. **深色主题走了另一条 CSS 分支**：`color_scheme=dark` 时探针给出
   `bodyBg=rgb(6,10,20)`、`bodyColor=rgb(232,237,247)`、`colorScheme=dark`、
   `dayDisplay=none` / `nightDisplay=block` —— 对应 CSS 里
   `html:not([data-theme="light"]) .backdrop__photo--day{display:none}` 那一段。

肉眼可见证据（浅色 1440×900）：侧栏导航带圆角选中态、表格有表头底色与分隔线、
`h1` 为 41.28px 粗体、`.callout` 有圆角浅底 —— 均非裸 HTML 外观。

### 5.3 中文字形（非豆腐块）判定

**对照法**：把真汉字与「必然无字形的码点」放在同一字体栈、同一 100px 字号下逐字截图，
比较**像素墨迹指纹**（归一化 32×32 墨迹网格的 sha256）。

| 组 | 样本 | 墨迹指纹去重数 | 墨迹像素数 |
|---|---|---|---|
| 真汉字 | 新一代替示词工程知识全景图概率采样确定性边界（22 字） | **22 / 22** | 1208 – 5425 |
| 无字形私用区 | U+E000 / U+E001 / U+E002 | **1 / 3**（三者指纹完全相同 `6f63742555777614`） | 均 1424，bbox 均 (50,87) |
| 替换字符 | U+FFFD | 1（`d06f3be9653b9096`） | 4103 |

- 汉字指纹集合 ∩ 豆腐块指纹集合 = **∅**
- 22 个汉字两两指纹互异 ⇒ 每个字都有独立轮廓

辅助证据：本机字体可用性 `fc-list :lang=zh` 列出
`Noto Sans CJK SC / Noto Serif CJK SC / Noto Sans SC` 等 16 个中文字族；
`fc-list :lang=zh file` 给出实体文件
`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`、
`~/.local/share/fonts/NotoSansSC-Bold.ttf`。
（注：`fc-match sans-serif:lang=zh` 返回 `DejaVu Sans`，但 DejaVu 无汉字字形，
浏览器按字体栈逐级回退到 Noto CJK —— 墨迹证据证明回退**确实发生且成功**。）

**结论：`cjk_ok = yes`。**

---

## 六、本通道的已知限制（诚实声明）

1. **渲染脚本只负责出图，不负责判对错。** 它证明「CSS 生效、素材加载、字形正常」，
   不证明版式符合设计意图。
2. `--full` 整页截图对 `13-interactive/`（cytoscape）这类需要 JS 布局的页面，
   可能截到未完全布局的状态；建议只用视口截图 + 交互后等待。
3. 深色主题必须显式 `--theme dark`；默认 `light` 是为可复现性做的**故意固定**，
   不代表站点默认观感。
4. snap 通道在本会话内**结构性不可用**（capability 限制），若未来会话
   `CapEff` 非空则可能恢复 —— 本通道不依赖它，无需关心。

---

## 七、证据文件索引

**一键复跑全部证据**：

```bash
python3 04-prototype/16-checkpoint/_render-proof/_verify_all.py
```

实测输出（10 项全 PASS，用时 40.1s）：

```
G5 通道证据自检汇总
证据                                           脚本                          判定      用时
环境侦察（浏览器/字体/网络/node）                _recon1.py                    PASS    12.1s
通道可用性冒烟（非 snap chromium 启动）          _smoke_launch.py              PASS     0.9s
★ 渲染两页 + PIL 尺寸/像素断言                   _run_render_proof.py          PASS     5.0s
逐字节确定性                                     _evidence_determinism.py      PASS     9.7s
背景素材 A/B 像素差                              _evidence_backdrop.py         PASS     3.4s
深色主题分支                                     _evidence_cjk_dark.py         PASS     2.3s
★ CJK 逐字墨迹指纹（豆腐块对照）                 _evidence_glyph_ink.py        PASS     3.6s
snap 负对照（原始报错）                          _evidence_negative_control.py PASS     1.3s
snap 根因定位                                    _evidence_snap_rootcause.py   PASS     0.9s
agent-browser 假成功核实                         _evidence_agentbrowser.py     PASS     0.8s
总体判定：PASS —— 渲染通道健全，全部证据可复跑
```

| 文件 | 作用 |
|---|---|
| `../_render.py` | **通道本体**（可复用） |
| `../_render.sh` | 便捷入口（已实测与直调逐字节一致） |
| `_verify_all.py` | ★ 一键复跑全部证据（健全性自检） |
| `_run_render_proof.py` | 渲染两页 + PIL 尺寸/像素断言 |
| `_evidence_determinism.py` | 逐字节可复现性验证 |
| `_evidence_backdrop.py` | 背景素材 A/B 像素差 |
| `_evidence_cjk_dark.py` | 深色主题分支探针 |
| `_evidence_glyph_ink.py` | ★ 逐字墨迹指纹（豆腐块对照） |
| `_evidence_negative_control.py` | snap 通道负对照（原始报错） |
| `_evidence_snap_rootcause.py` | snap 根因定位 + agent-browser 复测 |
| `_evidence_agentbrowser.py` | ★ agent-browser 假成功核实 |
| `_recon1.py` | 环境侦察（浏览器/字体/网络/node） |
| `_smoke_launch.py` | 通道冒烟（非 snap chromium 启动 + 中文渲染） |
| `_finalize.py` / `_cleanup_index.py` | 收尾与索引生成 |
| `EVIDENCE-INDEX.json` | 证据文件清单（含 sha256） |
| `*.png` / `*.manifest.json` | 渲染产物与逐次证据 manifest |
