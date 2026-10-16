# 视觉验证通道受限记录（本会话沙箱）

> 记录人：主 Agent　时点：2026-10-14　性质：**环境约束，非产物缺陷**

> ## ⚠️ 更正声明（2026-10-15 留档轮，⛔ 原文一律保留在下方，本节只做标注）
>
> **本件原记载的根因是错的，原结论「本会话内无法进行任何浏览器截图验证」已被推翻。**
> 三条更正（每条附第一手实测证据指针，均由留档轮子 Agent 亲自复跑，⛔ 非转述）：
>
> | # | 原文记载 | 实测事实 | 证据 |
> |:--:|---|---|---|
> | 1 | `/run/user/1000/snap.chromium` 在本会话内**只读** | 该目录**存在且可写**（`mode=0o40700`，建临时文件成功并已删除） | `16-checkpoint/_cap_probe.py` B 项；`_render-proof/_evidence_snap_rootcause.py` P1 |
> | 2 | 失败发生在「创建 XDG_RUNTIME_DIR 文件夹」阶段 | 失败发生在**更早的 `snap-confine` 启动层**，根本没走到创建目录那一步 ⇒ 改 `XDG_RUNTIME_DIR` **必然无效** | `_cap_probe.py` A/C/D 项；`_evidence_snap_rootcause.py` P2/P3/P5 |
> | 3 | 通道 3（`agent-browser`）「报同一条错误」，属同根因的另一种表现 | 它**不报错，而是假成功**——回显 `✓ Screenshot saved to …` 却产出**纯白 1 色空图** | `_evidence_agentbrowser.py`；见下方「更正二」 |
>
> ⇒ **「环境能力不可用」这一结论本身也被复核了。** 本轮实测发现：通道一直存在（playwright 的
> 非 snap 内核早已在盘上），真正卡住的是一个**被误诊的根因** ＋ 一个**会静默产空图的假通道**。
> 详见 `RENDER-CHANNEL.md`（新通道的操作说明与完整证据索引）。

---

## 结论

> ★ **【已推翻 · 2026-10-15】** 以下原结论不再成立。正确表述：
> **本会话内浏览器截图验证通道已建立并实测通过**（`_render.py` / `_render.sh`），
> 且 `_render-proof/_verify_all.py` 复跑 **10/10 PASS**。原文保留如下，仅作历史留痕。

~~**本会话内无法进行任何浏览器截图验证。**~~ 根因已定位到具体挂载点，非猜测。

## 根因

> ★ **【误诊 · 2026-10-15 更正】** 下面的报错**文本本身是真的**（本轮复跑逐字复现），
> 但由它推出的**因果是错的**：报错里那句 `read-only file system` 是 `snap-confine`
> 在**能力不足时的兜底文案**，⛔ 不是本次失败的现场。真正的失败层在它之前。
> 真因见下方「更正一」。

```
internal error, please report: running "chromium" failed:
cannot create XDG_RUNTIME_DIR folder "/run/user/1000/snap.chromium":
mkdir /run/user/1000/snap.chromium: read-only file system
```

`/run/user/1000` 在本会话沙箱内为**只读挂载**，而本机 chromium 是 **snap 包**——snap 的 confinement 强制要求该目录可写，且该路径由其启动器硬编码。

## 已尝试的通道（3 次，逐条留痕）

| # | 通道 | 命令要点 | 结果 |
|:--:|---|---|---|
| 1 | snap chromium 直调 | `chromium --headless --screenshot=…` | FAIL：XDG_RUNTIME_DIR 只读 |
| 2 | 同上 + 环境重定向 | `XDG_RUNTIME_DIR=/tmp/xdgrt`（另试 `SNAP_USER_DATA` / `SNAP_USER_COMMON`） | FAIL：snap 启动器忽略重定向，仍走 `/run/user/1000` |
| 3 | `agent-browser` 0.34.0（已装） | `agent-browser open file://…` | FAIL 两次：① 先报 socket 目录 `~/.agent-browser` 只读；② 用 `HOME=/tmp/abhome` 重定向后暴露真因——**agent-browser 底层同样驱动 snap chromium**，报同一条 XDG 错误 |

> ★ **【第 1、2 行更正】** 失败原因不是「目录只读」而是「**capability 缺失**」（更正一）。
> 结论「改 `XDG_RUNTIME_DIR` 无效」**是对的**，但理由错了：不是「启动器忽略重定向」，
> 而是**失败发生在重定向能起作用的层次之前**。
>
> ★ **【第 3 行更正 · 重要】** `agent-browser` 的实测行为**不是报错**，而是**假成功**（更正二）。
> 原文把它归为「同一根因的另一种表现」，这一归类**低估了它的危险性**：
> 报错会让人停下来，假绿会让人**拿着空图当证据**。

⇒ 两条通道共用同一个 snap 后端，属**同一根因的两种表现**，不构成独立备选。按故障自愈纪律**停止重试**。

> ★ **【补充】** 「停止重试」这条纪律本身是对的；错的是**没有同时去问「有没有第三条通道」**。
> 本轮实测：**非 snap 的 Chromium 早就在盘上**（`~/.cache/ms-playwright/chromium-1243/`），
> 只是当时没被探到 ⇒ 见「更正三」。

## 替代验证方案（本会话实际采用）

> ★ **【已过期 · 2026-10-15】** 本表是「无浏览器」前提下的降级方案。该前提已不成立：
> 现在有 **V2 真实渲染**（`_render.py`）这一级，V1/V1′/V3 降为**并行**手段而非替代品。

| 级别 | 手段 | 覆盖什么 | 不覆盖什么 |
|---|---|---|---|
| **V1 机检** | `16-checkpoint/gate_prototype.py`（结构 / 断链 / 自包含 / 主题根唯一 / 对比度逐底色 / 内部编号 / 幂等 / 前沿刷新） | 全部**可编码**的判据 | 视觉观感、布局在窄视口的实际表现 |
| **V1′ 静态渲染复算** | 由内联 CSS 文本独立解析出令牌取值与底色，用 `gen-tokens.py` 的同一套 WCAG 口径复算对比度 | 对比度（**不依赖浏览器**） | 浏览器真实排版下的溢出/重叠 |
| **V3 人看** | 把产物交给用户在本机浏览器打开（`present` 工具 + 本地路径） | 视觉观感、窄视口、交互可点性 | —（这正是 V3 的正当用途） |

## 对交付的影响（如实登记，⛔ 不得以「门控全绿」掩盖）

1. `stage2.json` 中 `risks.usability` 的 `next_step`（用户走查原型）**本来就要求人看**，本约束不改变该计划，只是把「机器先筛一遍」的覆盖面收窄到机检可及的部分。
2. 浏览器侧的真实排版风险（长表格横向溢出、中文长行断行、窄视口侧栏挤压）**本轮未被机器验证**，须由用户走查时重点看。这三点恰好是既有站被审计出的历史缺陷类型。
3. 第 2 轮若需要机器视觉回归，须先解决沙箱对 `/run/user/1000` 的只读限制（或改用非 snap 的 chromium / 独立浏览器后端）。

> ★ **【第 2、3 条更正 · 2026-10-15】** 第 2 条的「本轮未被机器验证」**已不成立**：
> 留档轮已用 `_render.py` 真实渲染 5 个页面（含组页、学习路径页、交互页）并出 PIL 读数，
> 全部非空图（唯一色 4030–4569）。第 3 条给出的**两条出路，第二条本轮已走通**：
> 改用非 snap 的 chromium（playwright 自带内核）——⛔ 无需解决 `/run/user/1000` 的挂载问题，
> 因为**那个问题本来就不存在**。

---

# ★ 更正一：真因复核（capability 缺失，⛔ 不是「路径只读」）

## 实测（第一手，`_cap_probe.py`）

```
== A. 进程能力集（/proc/self/status）==
   CapInh: 0000000000000000
   CapPrm: 0000000000000000
   CapEff: 0000000000000000      ← 有效集为空
   CapBnd: 000001ffffffffff
   NoNewPrivs: 1                 ← no-new-privs 已开启
   Seccomp: 0

== B. /run/user/1000/snap.chromium 存在性与可写性 ==
   exists=True
   mode=0o40700 uid=1000 gid=1001
   WRITABLE = YES  （建临时文件成功并已删除）

== C. snap-confine 的 file capability ==
   exists=True
   security.capability = 00000002cf002c01000000000000000000000000
   （非空即说明该二进制带 file capability，需被提升进 CapEff 才能运行）
```

`getcap` 口径（`_evidence_snap_rootcause.py` P2）给出同一件事的可读形式：

```
/usr/lib/snapd/snap-confine cap_chown,cap_dac_override,cap_dac_read_search,
  cap_fowner,cap_setgid,cap_setuid,cap_sys_chroot,cap_sys_ptrace,
  cap_sys_admin,cap_sys_resource=p
```

## 因果链（三步，逐条可复算）

1. **`snap-confine` 是 file-capability 程序**（`security.capability` 非空，`-rwxr-xr-x` ⇒ 无 setuid）。
   它要正常工作，必须把文件上声明的 `cap_dac_override` 等提升进自己的**有效集**。
2. 但本会话 **`CapEff = 0000000000000000`**（`CapBnd` 里那一位是在的，可 `CapPrm/CapEff` 为空），
   且 **`NoNewPrivs = 1`**（`capsh`：`Securebits: 00/0x0/1'b0 (no-new-privs=1)`）
   ⇒ 内核**拒绝**把文件能力提升进有效集。
3. 于是 `snap-confine` 在**自身启动阶段**就退出，报：

```
snap-confine is packaged without necessary permissions and cannot continue
required permitted capability cap_dac_override not found in current capabilities:
  =: Operation canceled
```

★ 这条报错**逐字**说明了真因（`cap_dac_override not found in current capabilities`），
而原件的 `/run/user/1000` 报错文本是**另一条更靠后的兜底路径**留下的 ⇒ 两者**不是同一次失败**。

## 为什么「改 `XDG_RUNTIME_DIR` 必然无效」

失败点在**第 3 步**——`snap-confine` 连自己的初始化都没完成。而 `XDG_RUNTIME_DIR`
是它在初始化**成功之后**才会去用的变量。⇒ 在它之前发生的失败，**不可能**被在它之后才被读取的变量治好。
（这解释了原件观察到的「重定向无效」，但推翻了原件给出的理由。）

## 证据脚本

| 脚本 | 作用 |
|---|---|
| `16-checkpoint/_cap_probe.py` | ★ 留档轮新写：Python 侧独立取证（能力集 / 目录可写性 / 扩展属性 / 负对照） |
| `_render-proof/_evidence_snap_rootcause.py` | 原始根因定位（P1–P6，含非 snap 内核对照） |
| `_render-proof/_evidence_negative_control.py` | snap 通道负对照（原始报错逐字留痕） |

---

# ★ 更正二：`agent-browser 0.34.0` 是本机的**假绿通道**（⛔ 禁止用于视觉验证）

## 实测（第一手，`_evidence_agentbrowser.py`）

**它不报错。它回显成功：**

```
$ agent-browser screenshot about:blank
✓ Screenshot saved to /home/zako-mio/.agent-browser/tmp/screenshots/screenshot-1792056494439.png
```

**但产物是纯白空图：**

```
  screenshot-1792056435846.png
    size=(1280, 577) uniq_colors=1 top_left=(255, 255, 255)
  screenshot-1792056494439.png
    size=(1280, 577) uniq_colors=1 top_left=(255, 255, 255)
```

**对真实页面更糟——它把 `--output` 当字面文件名：**

```
$ agent-browser screenshot http://127.0.0.1:45197/index.html --output <…>/_ab_test.png
✓ Screenshot saved to --output          ← 把选项名当成了文件名
  -> 无输出文件                          ← 目标 PNG 根本不存在
```

## 判定与禁令

| 项 | 判定 |
|---|---|
| 通道性质 | **假绿（false-green）**：退出码/回显均表示成功，产物却无信息量 |
| 危险点 | ① 静默产空图（1280×577 / `uniq_colors=1`）；② `--output` 被当字面文件名，目标文件不存在 |
| 处置 | **⛔ 禁止用于视觉验证**（不得作为「已看渲染」的证据来源） |
| 连带结论 | **此前若有人据此声称「已验证视觉」，那些结论一律无效**——须以 `_render.py` 重跑后重新判定 |

★ 这条与原件「通道 3 报同一条错误」的记载**直接冲突**，以实测为准。
★ 一般化教训：**验证通道本身必须先被验证**。「工具回显成功」不等于「产物有内容」——
凡截图类证据，必须补一步**像素读数**（尺寸 + 唯一色数），否则无法区分「渲染成功」与「渲染了一张白纸」。
本轮的 `_pil_read.py` 就是为此而写。

---

# ★ 更正三：新通道与用法（G5 已消）

| 项 | 值 |
|---|---|
| 通道 | `playwright-python` → **非 snap** Chromium |
| 浏览器 | `~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`（Google Chrome for Testing **153.0.8010.12**） |
| 驱动 | Python `playwright` 1.63.0 |
| 通道本体 | `04-prototype/16-checkpoint/_render.py` |
| 便捷入口 | `04-prototype/16-checkpoint/_render.sh` |
| 操作说明 | `04-prototype/16-checkpoint/RENDER-CHANNEL.md` |
| 证据目录 | `04-prototype/16-checkpoint/_render-proof/`（含 `_verify_all.py` 一键复跑） |
| 是否新装东西 | **否**——内核与驱动**早已在盘上**，本轮只是把它们找出来用 |

## 用法

```bash
python3 04-prototype/16-checkpoint/_render.py \
    --html 04-prototype/index.html --width 1440 --height 900 \
    --out 04-prototype/16-checkpoint/_render-proof/index.png
```

参数：`--html --out --width --height --dsf --theme{light,dark} --root --full --json --quiet`。
脚本内部自起临时 `http.server`（docroot 自动探测到 `04-prototype/`），
⛔ 不要用 `file://` 直开（背景素材会 404）。

## 留档轮的真实渲染读数（★ 留档轮子 Agent 亲自跑，G4 落地后）

| PNG（相对 `04-prototype/16-checkpoint/`） | 尺寸 | 唯一色 | 字节 | sha256(前16) |
|---|---|---|---|---|
| `_render-proof/g4-final/01-root-index.png` | 1440×900 | 4547 | 453785 | `80d9336de07eb135` |
| `_render-proof/g4-final/02-node-pe-f-01.png` | 1440×900 | 4569 | 362642 | `dc580d62b15ee51a` |
| `_render-proof/g4-final/03-group-g00.png` | 1440×900 | 4192 | 452024 | `a26a29230f7af93e` |
| `_render-proof/g4-final/04-learning-path.png` | 1440×900 | 4030 | 407675 | `bdbe026dad921424` |
| `_render-proof/g4-final/05-interactive.png` | 1440×900 | 4496 | 444482 | `3224511245291ae2` |

`_render-proof/_verify_all.py` 复跑：**10 项全 PASS，用时 40.8s**。

---

# ★ 更正四：原文「对交付的影响」第 3 条给出的两条出路，走通的是第二条

原文写：「第 2 轮若需要机器视觉回归，须先解决沙箱对 `/run/user/1000` 的只读限制
（**或改用非 snap 的 chromium / 独立浏览器后端**）」。

实测结论：**第二条出路成立，且第一条出路不必走**——因为 `/run/user/1000` 从来不是障碍
（更正一）。⇒ 本件登记的「环境约束」至此**全部解除**，G5 在 `DESIGN-CONTRACT.md` 中改判 ✅。

---

# ★ 本件的一般化教训（写给后续轮次）

1. **「环境能力不可用」的结论也要被复核。** 本轮实测发现：通道**一直存在**（playwright 的
   非 snap 内核早已在盘上），而真正卡住的是一个**被误诊的根因** ＋ 一个**会静默产空图的假通道**。
   ⇒ 把「不可用」当成**待验证的假设**，而不是**已确立的事实**；下结论前先问
   「我失败的是哪一层？有没有别的后端？失败文案是不是兜底文案？」
2. **报错文案 ≠ 失败现场。** `read-only file system` 是兜底路径的文案，真因在更早一层。
   ⇒ 定位根因要看**能力集/权限**这类**前置条件**，不要只读最后一行的报错。
3. **验证通道自身必须先被验证。** 一个会「假绿」的通道比一个会报错的通道危险得多：
   报错让人停下来，假绿让人拿着空图当证据。⇒ 截图类证据一律补**像素读数**。
4. **「停止重试」是对的，但要连「换后端」一起做。** 原件停在「两条通道同源 ⇒ 放弃」，
   而正确的下一步是「**找一个不同源的通道**」——本轮的成本是 `find` 一次浏览器内核路径。
