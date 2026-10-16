// _selfcheck_switches.mjs —— 四枚显示开关的**行为**自检（无浏览器：自建最小 DOM 桩）
//
// 为什么需要它：`VERIFY-CONSTRAINT.md` 记录的通道缺失是「浏览器不可用」，而门控 P26/P34
// 只能断言「脚本在 <head>」「键名出现」「按钮档位齐备」——**都不断言点了会怎样**。
// 本自检把生成的 pre-paint 脚本放进最小 DOM 桩里真跑一遍，断言四枚偏好的：
//   ① 默认态不落属性、不落 localStorage 键；② 点击后落属性 + 落键 + 两个副本的 aria-pressed 同步；
//   ③ 回到默认态时属性与键都被清掉；④ 预置 localStorage 时首帧即生效（pre-paint，无闪烁）。
//
// 用法：PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$PATH" node _selfcheck_switches.mjs
// 退出码 0 = 全 PASS。

import fs from "node:fs";
import vm from "node:vm";

const HTML = new URL("../index.html", import.meta.url);
const src = fs.readFileSync(HTML, "utf8");
const m = src.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.log("[FAIL] 产物里找不到内联脚本"); process.exit(1); }
const SCRIPT = m[1];

const SWITCHES = [
  { attr: "data-theme-set",    key: "ui-theme",    states: ["system", "light", "dark"], def: "system",   rootAttr: "data-theme",    nonDef: "dark" },
  { attr: "data-motion-set",   key: "ui-motion",   states: ["system", "on", "off"],     def: "system",   rootAttr: "data-motion",   nonDef: "off" },
  { attr: "data-backdrop-set", key: "ui-backdrop", states: ["on", "off"],               def: "on",       rootAttr: "data-backdrop", nonDef: "off" },
  { attr: "data-fontsize-set", key: "ui-fontsize", states: ["standard", "large"],       def: "standard", rootAttr: "data-fontsize", nonDef: "large" },
];

class El {
  constructor(attrs = {}, tag = "div") {
    this.attrs = { ...attrs }; this.tag = tag; this.parentNode = null;
    this.className = ""; this.style = { setProperty() {} };
  }
  getAttribute(n) { return Object.prototype.hasOwnProperty.call(this.attrs, n) ? this.attrs[n] : null; }
  setAttribute(n, v) { this.attrs[n] = String(v); }
  removeAttribute(n) { delete this.attrs[n]; }
}

function makeEnv(seed = {}) {
  const root = new El({}, "html");
  const body = new El({}, "body");
  const buttons = [];
  for (const sw of SWITCHES) {
    for (const st of sw.states) {
      // 两个副本（顶部导航 / 侧栏），与真实产物一致
      for (const copy of ["head", "rail"]) {
        const b = new El({ [sw.attr]: st, class: "switch__btn" }, "button");
        b.parentNode = new El({ class: "switch" }, "div");
        b.parentNode.parentNode = body;
        b.copy = copy;
        buttons.push(b);
      }
    }
  }
  const store = new Map(Object.entries(seed));
  const listeners = [];
  const document = {
    documentElement: root,
    body,
    readyState: "complete",
    querySelectorAll(sel) {
      const mm = sel.match(/^\[([a-z-]+)\]$/);
      if (!mm) return [];
      return buttons.filter((b) => b.getAttribute(mm[1]) !== null);
    },
    addEventListener(ev, fn) { listeners.push([ev, fn]); },
  };
  const localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => { store.set(k, String(v)); },
    removeItem: (k) => { store.delete(k); },
  };
  const window = {};                       // 无 IntersectionObserver ⇒ 走 fin() 兜底分支
  const ctx = { document, localStorage, window, setTimeout: () => 0, console };
  vm.createContext(ctx);
  vm.runInContext(SCRIPT, ctx);
  return { root, buttons, store, listeners, document };
}

function click(env, attr, state) {
  const btn = env.buttons.find((b) => b.getAttribute(attr) === state);
  if (!btn) throw new Error("找不到按钮 " + attr + "=" + state);
  for (const [ev, fn] of env.listeners) {
    if (ev === "click") fn({ target: btn, preventDefault() {} });
  }
}

const results = [];
const chk = (name, cond, detail = "") => results.push([name, !!cond, detail]);

// ---- ① 默认态：不落属性、不落键
{
  const env = makeEnv();
  for (const sw of SWITCHES) {
    chk(`默认态不落属性 ${sw.rootAttr}`, env.root.getAttribute(sw.rootAttr) === null);
    chk(`默认态不落键 ${sw.key}`, !env.store.has(sw.key));
    chk(`默认态 aria-pressed 唯一 true（${sw.attr}）`,
        env.buttons.filter((b) => b.getAttribute(sw.attr) === sw.def)
                   .every((b) => b.getAttribute("aria-pressed") === "true") &&
        env.buttons.filter((b) => b.getAttribute("aria-pressed") === "true" &&
                                  b.getAttribute(sw.attr) !== null &&
                                  b.getAttribute(sw.attr) !== sw.def).length === 0);
  }
}

// ---- ② 点击非默认档：落属性 + 落键 + 两副本 aria-pressed 同步
for (const sw of SWITCHES) {
  const env = makeEnv();
  click(env, sw.attr, sw.nonDef);
  chk(`点击 ${sw.attr}=${sw.nonDef} ⇒ 落属性 ${sw.rootAttr}`,
      env.root.getAttribute(sw.rootAttr) === sw.nonDef);
  chk(`点击 ${sw.attr}=${sw.nonDef} ⇒ 落键 ${sw.key}`,
      env.store.get(sw.key) === sw.nonDef);
  const copies = env.buttons.filter((b) => b.getAttribute(sw.attr) === sw.nonDef);
  chk(`点击 ${sw.attr}=${sw.nonDef} ⇒ 两副本 aria-pressed=true`,
      copies.length === 2 && copies.every((b) => b.getAttribute("aria-pressed") === "true"));
  // ---- ③ 回到默认档：属性与键都被清掉
  click(env, sw.attr, sw.def);
  chk(`回到 ${sw.attr}=${sw.def} ⇒ 属性被清`, env.root.getAttribute(sw.rootAttr) === null);
  chk(`回到 ${sw.attr}=${sw.def} ⇒ 键被清`, !env.store.has(sw.key));
}

// ---- ④ 预置 localStorage ⇒ 首帧即生效（pre-paint，无闪烁）
{
  const seed = Object.fromEntries(SWITCHES.map((s) => [s.key, s.nonDef]));
  const env = makeEnv(seed);
  for (const sw of SWITCHES) {
    chk(`预置 ${sw.key}=${sw.nonDef} ⇒ 首帧即落属性 ${sw.rootAttr}`,
        env.root.getAttribute(sw.rootAttr) === sw.nonDef);
  }
  chk("预置非法值被收敛（ui-backdrop=zzz ⇒ 视为默认）",
      makeEnv({ "ui-backdrop": "zzz" }).root.getAttribute("data-backdrop") === null);
}

let bad = 0;
for (const [n, ok, d] of results) {
  if (!ok) bad++;
  console.log(`[${ok ? "PASS" : "FAIL"}] ${n}${d ? " " + d : ""}`);
}
console.log(`\n== 开关行为自检：${bad === 0 ? "PASS" : "FAIL"}（${results.length} 例，FAIL ${bad}）==`);
process.exit(bad === 0 ? 0 : 1);
