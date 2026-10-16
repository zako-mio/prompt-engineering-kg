# 接续件 · D3：生成器重写（设计系统换底座）

> 上游：`gen-tokens.py` v2（**已就绪**）· `10-dag-data/site-palette.json`（**已就绪**）· `ADR-002`（架构裁决）· `H1-hub-design-system.md`（hub 基准）· `H2-hub-design-lessons.md`（10 条硬规则）· `H3-prototype-design-gap.md`（18 条差距）
> 性质：**用户已裁决「档 A+B+D 全换底座与交互，并同步补判据」**，且**引入真实摄影素材背景**。

---

## 0. 已就绪的前置（⛔ 不要重写）

| 件 | 状态 | 用法 |
|---|---|---|
| `16-checkpoint/gen-tokens.py` | ✅ v2，自检 **12/12 PASS**，对比度 **34 PASS / 0 FAIL / 2 REPORT** | `--print` / `--write` / `--check` / `--selftest` / `--coverage` / `--gate-contrast` / `--contrast <#HEX>` |
| `10-dag-data/site-palette.json` | ✅ **56 令牌**，契约 11 角色覆盖 **11/11**，追加 45 个 | 令牌值唯一真相源 |
| `16-checkpoint/tokens.generated.css` | ✅ 6,005 B（sha256 `00824a6b0340…`） | 三块：`:root` / 系统深色 / 强制深色 |
| `04-prototype/assets/backdrop/*.webp` | ✅ 7 个文件 / 2.3MB | `night-portrait-1080` `night-1280/1920/2560` `day-1280/1920/2560` |
| `04-prototype/assets/favicon.svg` | ✅ | 站点图标 |

★ **令牌块的唯一来源是 `gen-tokens.py`**：⛔ 不得在生成器里手写任何令牌声明，必须调 `gen-tokens.py --print` 取块内联。

---

## 1. 主题机制（★ 结构性变更，v1 的 `light-dark()` 全部撤掉）

1. **三块结构**由 `gen-tokens.py` 产出（`:root` / `@media (prefers-color-scheme: dark) { :root:not([data-theme='light']) }` / `:root[data-theme='dark']`）。⛔ **无 `:root[data-theme='light']` 块** —— 强制浅色是「不覆盖 + 守卫」。
2. **pre-paint 内联脚本**（`<head>` 内、先于首帧）：读 `localStorage['ui-theme']`，为 `light`/`dark` 时落 `document.documentElement.dataset.theme`，`system` 时 `removeAttribute`。⛔ **不得放 body 末尾**。
3. **切换只改属性，⛔ 不接管 `color-scheme`**（避免双真相源）。
4. **三态开关**：跟随系统 → 浅色 → 深色 → 跟随系统；`aria-pressed`；可见文本**加类型前缀**（「主题：跟随系统」），因为站内还有一枚动效开关会与它相邻 ⇒ 两枚默认态可见文本不得逐字相同。
5. **两条 `theme-color` meta**（按媒体查询分档），值**必须与 `--surface-page` 的浅/深值同步**。
6. **背景帧显隐必须用 `display: none`**（⛔ 不得用 `opacity:0`/`visibility:hidden`——那两样仍会下载素材）。

---

## 2. 视觉底座（档 A）

1. **表面阶梯 5 级**（`--surface-page/raised/subtle/stripe/sunken`）：页面底**着色**、卡片底**留白**（对比方向反转）。
2. **描边三级按语义分工**（★ ⛔ 不得按「哪个好看」挑）：
   - `--border-subtle`（1.19:1）→ 弱分隔：行分隔、页脚顶线、组内条目之间
   - `--border-card`（1.34:1）→ **卡片可见柔边**（装饰性，report-only）
   - `--border-line`（**3.24:1 硬判**）→ **控件边界**：按钮、输入框、可交互 chip、术语点线
   ⚠ 把 `--border-subtle` 用在 `<input>` 边框上会**直接违反 WCAG 1.4.11** 且门控抓不到。
3. **★ 卡片四件套**（⛔ 不押在单一 box-shadow 上）：
   ```
   background: linear-gradient(180deg, var(--surface-raised) 0%,
     color-mix(in srgb, var(--brand-primary) 4%, var(--surface-raised)) 100%);
   border: 1px solid var(--border-card);
   border-radius: var(--radius-lg);
   box-shadow: var(--shadow-1), inset 0 1px 0 var(--edge-highlight);
   ```
   悬停/聚焦：`transform: translateY(-3px)` + `border-color: var(--brand-tint)` + `box-shadow: var(--shadow-2), inset 0 1px 0 var(--edge-highlight)`。
4. **字号只用 6 档令牌**（`--fs-hero/section/card-title/body/label/nav`）：⛔ **令牌外不得出现任何 `font-size` 字面值**（v1 有 15 个零碎值 ⇒ 门控要判 0）。
5. **间距只用 `--space-1..7`**；圆角只用 `--radius` / `--radius-lg`；行宽用 `--measure`。
6. **字体族 ≤2**（`--font-sans` / `--font-mono`，均已含中文回退链）。
7. **`--text-tertiary` ⛔ 仅限非正文**（元信息/标签）；可核对的关键字段用 `--text-secondary`。

---

## 3. 色板收敛（★ 最硬的一条：硬规则 5）

**11 组彩虹色 + warn/danger（13 个强调色）全部撤掉**，改为「1 品牌色 + 4 语义色」。
**组身份改由文字与位置承载**，⛔ 不再由色相承载：
- 组页/组索引/学习路径/交互图里，分组用**中性色的序号标记**（如 `G02`）+ 文字标题；
- 交互图的组节点**统一用品牌色或中性表面色**，⛔ 不得按组分配不同色相；
- 若确需在图中区分「当前选中组」，用**同一色相的深浅或描边**表达，⛔ 不用多色相。
★ 依据：hub 的 C26 实测——7 色按行序取值被判「**不承载任何信息**，且与图件自身声明相抵」⇒ 裁决改单色。

---

## 4. 交互（档 B）

1. **`:hover` 全站包 `@media (hover: hover)`**；`:focus-within` / `:focus-visible` ⛔ **不进**该门控。
2. **反馈面 ≡ 热区**（硬规则 2）：
   - 卡片：标题链接 `::after { inset: 0; z-index: 1 }` 拉伸铺满整卡；卡内其它真链接 `position: relative; z-index: 2` **抬升**（**必须成对**）。
   - ⚠ containing block 必须是卡片本体：祖先带 `transform`/`filter`/`will-change` 会让拉伸层只覆盖到那个祖先（Bootstrap stretched-link 的已知陷阱）。
   - 纯装饰面：`cursor` ⛔ 不得为 `pointer`。
3. **导航二选一，⛔ 不叠加**：`<1180px` 顶部导航（sticky）；`≥1180px` **顶部导航 `display:none` + 左栏 rail**（sticky，`100dvh`）。同一组路由⛔ 不得同时出现两处可交互实例。
4. **断点**：至少补 `640 / 768 / 1024 / 1180`；容器内边距 `16 → 24(≥640) → 32(≥1024)`。
5. **触控目标 ≥44px**（导航/按钮/链接/折叠控件）。
6. **skip link**：body 第一个子元素；★ 其底色＝品牌色而 `a:hover` 强调色也是品牌色 ⇒ **须显式收回本色**（对比度优先于一致性）。
7. **focus-visible**：全局 `outline: 2px solid var(--focus-ring); outline-offset: 2px`；★ **焦点可见性不依赖任何装饰环**。

---

## 5. 动效层（档 B）

1. `[data-reveal]` 机制，**★ 必须用独立 `translate` 属性，⛔ 不用 `transform`**：
   - 用 `transform` 会因特异性压过 `.card:hover { transform: translateY(-3px) }` ⇒ 卡片悬停永不抬起；
   - 在 `.is-in` 里声明 `transition` 同样压过卡片自身的 ⇒ 描边/阴影无过渡。
   - ⛔ **不得退回「抬高 `.card:hover` 特异性」的写法**。
2. **错峰** `animation-delay: calc(var(--i, 0) * 70ms)`。
3. **★ 无 JS 兜底双保险**：① 隐藏态挂在 `html.js-motion` 之下（无 JS ⇒ 元素**默认可见**）；② pre-paint 脚本挂 **1800ms 一次性定时器**，若未落 `data-motion-ready` 就把全部 `[data-reveal]` 置终态。
   原文纪律：**「退化路径是「没有动画」，⛔ 绝不是「没有内容」。」**
4. **三态动效开关**（跟随系统 / 开 / 关）：`on` **必须落属性**（否则在 OS 开了 reduce 的机器上被静默压掉）；所有 reduce 熔断块以 `:not([data-motion='on'])` 限定。
5. **两条独立熔断**：`@media (prefers-reduced-motion: reduce)` 与 `:root[data-motion='off']`，均含 `*` 级 animation/transition 压制。
6. **动效预算**（门控要判）：单页 `[data-reveal]` ≤ **32**；进场完成 ≤ **1800ms**；`--dur-*` 之和 ≤ **3.6s**（本站 1.79s）；常驻 `infinite` 元素 ≤ **12**。

---

## 6. 背景层（★ 真实摄影素材）

**DOM 顺序即堆叠顺序**（容器 `position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden`，`aria-hidden="true"`）：
1. `.backdrop__photo--day` / `--night`（`cover` + `scale(1.07)`；夜间 `contrast(1.5) brightness(0.62)`、日间 `hue-rotate(-18deg) saturate(0.9)`；`opacity: 0.62`）
2. `.backdrop__veil--day` / `--night`（纱幕：把正文压在可预期合成亮度区间内，色由 `--surface-page` 派生）
3. `.backdrop__scrim`（局部 scrim：只压**阅读带**，三档 `--scrim-1/2/3`）

**分辨率阶梯**（⛔ 不用 `image-set`，用显式媒体查询以便门控可读）：
| 条件 | 夜间 | 日间 |
|---|---|---|
| 默认（窄屏） | `night-portrait-1080.webp` | `day-1920.webp` |
| `≥760px` | `night-1280.webp` | `day-1920.webp` |
| `≥1100px` | `night-1920.webp` | `day-2560.webp` |
| `≥1900px` 或 (`≥1100px` 且 `2dppx`) | `night-2560.webp` | `day-2560.webp` |

**许可登记（必须进页脚）**：
- 夜间：ESO `eso0934a`《A 340-million pixel starscape from Paranal》(S. Guisard)，**CC BY 4.0，须署名**
- 日间：Lofoten, Norway (Unsplash) 极光天幕，**CC0 1.0**
页脚须有独占一行的 `.footer__credits`，含素材名、作者、许可与链接。

**⛔ 背景子树内不得有任何可聚焦元素**（`a`/`button`/`input`/`select`/`textarea`/`[tabindex]`）。

---

## 7. ★ 资产白名单（本轮的边界变更，须与 ADR-002 一致）

`assets/backdrop/*.webp` 是**站点级只读图片资产**。自包含契约需开**第二类白名单**：
- 允许：以 `assets/` 前缀的**相对路径**引用，且扩展名 ∈ `{.webp, .png, .jpg, .jpeg, .svg, .avif}`；
- ⛔ 禁止：白名单内出现 `script` / `link[rel=stylesheet]` / `@import` / 任何非图片资源；
- ⛔ 白名单**不得扩散**：门控须断言受检集合中命中该前缀的资源引用**全部为图片**。
- `13-interactive/vendor/` 的**脚本**白名单保持不变，两者**分开声明、互不包含**。

---

## 8. 判据同批（档 D，元规则 2：修法与判据必须同批）

在 `gate_prototype.py` 现有 P01–P22 之外**新增**（编号续接）：

| 判据 | 断言 |
|---|---|
| P23 | **令牌来源唯一**：产物中每个令牌声明块与 `gen-tokens.py --print` 逐字节一致；⛔ 无第二处令牌声明 |
| P24 | **令牌外硬编码 = 0**：产物 CSS 中不得出现字面 `font-size` / `border-radius` / `color:` 十六进制值 / `padding|margin` 字面值（只允许 `var(--…)` 与结构性 0/auto/100%） |
| P25 | **`:hover` 门控覆盖**：含 `:hover` 的选择器 100% 位于 `@media (hover: hover)` 内；`:focus-within`/`:focus-visible` ⛔ 不在其内 |
| P26 | **主题三态同步**：三块齐备（`:root` / 系统深色 / 强制深色）＋ pre-paint 脚本在 `<head>` 且**早于**任何样式表之外的可视内容 |
| P27 | **背景层结构护栏**：`.backdrop` 为 `fixed` + 负 `z-index` + `pointer-events:none` + `aria-hidden`；**子树零可聚焦元素**；非当前主题帧 `display:none` |
| P28 | **动效预算四项上界**：`[data-reveal]` ≤32 / 进场 ≤1800ms / `--dur-*` 和 ≤3.6s / `infinite` ≤12 |
| P29 | **交互作用面双向闭合**：CSS 中含 `:hover`/`:focus-within` 的选择器集合 ⟺ 声明表登记集合（漏登记与**幽灵登记**均 FAIL）；每条登记的基选择器在产物中**至少命中 1 个元素** |
| P30 | **资产白名单未扩散**：受检集合中命中 `assets/` 前缀的引用全部为图片扩展名；无 `script`/`stylesheet` 混入 |
| P31 | **色相不承载身份**：产物中组相关选择器**不得**出现多色相分配（断言组配色令牌数 = 0） |
| P32 | **许可证登记**：页脚含 CC BY 素材的署名行（素材名 + 作者 + 许可 + 链接），且 `assets/backdrop/` 每个文件都在登记表里 |

**判据纪律（沿用）**：⛔ 不得为通过而放宽阈值；⛔ 不得设豁免；失败即 FAIL 且退出码非 0；`--selftest` 须**逐条触发负例**；每条判据须带**空集守卫**（计数型判据为 0 即 FAIL）。

---

## 9. 交付与自检

1. 跑 `python3 16-checkpoint/gen-tokens.py --write`（确认 sha256 不变）。
2. 跑 `build-all.py --dry-run` → `--write` → 再 `--write`（验幂等）。
3. 跑 `gate_prototype.py`（须 **0 FAIL**）与 `gate_prototype.py --selftest`（负例须全部触发）。
4. 更新 `PUBLISH-STATE.json`（含 `gates.criteria_change_*` 指针与资产清单）。
5. ⛔ 只写 `04-prototype/` 下文件；⛔ 不碰 `10-dag-data/*.json`（`site-palette.json` 除外，若需补令牌须说明理由）、⛔ 不碰 `gen-tokens.py`、⛔ 不碰 `assets/`。
6. 返回时把 `gate_prototype.py` 与 `--selftest` 的**真实输出原文**放进 `data`。

## 10. ⛔ 已知的不可验证面（须如实登记，⛔ 不得声称已验证）

浏览器在本会话**不可用**（snap chromium 卡在只读 `/run/user/1000`）⇒ **视觉与真实 JS 行为均未经渲染验证**。须在 `warnings` 里写明：主题三态的真实切换、动效兜底的真实触发、背景合成后的对比度、窄视口形态、cytoscape 实际布局——**全部未验证**，须用户走查。
