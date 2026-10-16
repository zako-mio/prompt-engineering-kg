#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-root.py —— 根入口生成器

输出：`04-prototype/index.html`（经 gen-common.page_shell 产出）。
双轨入口：速览 → 交互全景图；深学 → 学习路径。

★ 本轮形态变更（H3 G13 / C11）：⛔ 不再用「67 节点 / 96 边 / 11 组 / 30 层」这类 hero 大数字
   作首屏主张——那是「模板化首屏」的标志形态。改为**信息性结构定位图**（分组序号 + 名称 +
   规模 + 层范围的中性表），规模数字降为普通元信息行。
★ 组身份由**文字与中性序号**承载（H2 硬规则 5）：⛔ 不按组分配色相。
"""

import importlib.util
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_common")

BASE = ""


def root_page(dag, frontier, page_exists):
    nodes = dag["nodes"]
    groups = sorted(dag["groups"], key=lambda g: g["order"])
    edges = dag["edges"]
    meta = dag["meta"]
    complete = [n for n in nodes if n["content_status"] == "complete"]
    registered = [n for n in nodes if n["content_status"] == "registered"]
    nxt = C.reveal_seq()
    body = []
    body.append('<h1>%s</h1>' % C.esc(meta["mission"]))
    body.append('<p class="lede">%s。全站 %d 个知识节点、%d 条依赖边、%d 个知识分组、'
                "%d 个依赖深度层，全部由同一份数据派生：一张可点击下钻的全景图做速览，"
                "一套按依赖层序排布的分层教程做深学。</p>"
                % (C.esc(meta["audience"]), len(nodes), len(edges), len(groups), meta["layer_count"]))
    body.append('<p class="meta-line"><span>数据时点 %s</span><span>版次 %s</span>'
                '<span>边语义 %s</span><span>无环</span></p>'
                % (C.esc(meta["as_of"]), C.esc(meta["edition"]), C.esc(" / ".join(meta["edge_semantics"]))))

    # --- 结构定位图：★ 用「序号 + 名称 + 规模 + 层范围」的文本表代替 hero 大数字 ---
    body.append('<h2>这张图覆盖什么</h2>')
    body.append('<p class="lede">下表是本站的结构定位：左列是知识分区的序号，'
                '分组身份由序号与名称承载（不用颜色区分分组）。'
                '"依赖深度"是学习顺序的拓扑层，与分组序号彼此独立。</p>')
    body.append('<div class="table-scroll"><table>'
                '<caption>%d 个知识分区；层范围指该分区内节点所在的依赖深度区间。</caption>'
                '<thead><tr><th>序号</th><th>分区</th><th>节点</th><th>层范围</th>'
                '<th>已写满</th></tr></thead><tbody>' % len(groups))
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        body.append('<tr><td>%s</td><td><a href="%s">%s</a></td><td>%d</td>'
                    '<td>第 %d – %d 层</td><td>%d</td></tr>'
                    % (C.group_mark(g["id"]), C.esc(C.group_page_rel(g["id"])), C.esc(g["name"]),
                       len(mem), min(n["layer"] for n in mem), max(n["layer"] for n in mem),
                       sum(1 for n in mem if n["content_status"] == "complete")))
    body.append("</tbody></table></div>")

    # --- 两条入口（卡片四件套 + 拉伸层，标题链接即整卡热区） ---
    body.append('<h2>两条入口</h2>')
    body.append('<div class="grid">')
    body.append(C.card(
        '<h3><a class="card__title-link" href="%s">速览：交互全景图</a></h3>'
        "<p>先看组级总览，再点进任一分组下钻到组内节点；支持按节点或分组深链定位。"
        "适合先建立「这块知识长什么样」的整体印象。</p>"
        % C.esc(C.DIR_INTERACTIVE + "/index.html"), reveal_index=nxt()))
    body.append(C.card(
        '<h3><a class="card__title-link" href="%s">深学：学习路径</a></h3>'
        "<p>按依赖深度逐层展开：每层给出该层节点的全部前置与「为什么在这层」。"
        "适合按顺序系统学一遍。</p>"
        % C.esc(C.DIR_VIEWS + "/01-learning-path.html"), reveal_index=nxt()))
    body.append(C.card(
        '<h3><a class="card__title-link" href="%s">按方向：知识分组</a></h3>'
        "<p>%d 个知识分区，每区含导读、组内节点表与组间前后继。"
        "适合「我只关心某个方向」的读法。</p>"
        % (C.esc(C.DIR_GROUPS + "/index.html"), len(groups)), reveal_index=nxt()))
    body.append(C.card(
        '<h3><a class="card__title-link" href="%s">追新：新一代模块</a></h3>'
        "<p>只含数据、不含教程正文的分区：条目带时间锚、版次、状态与取代关系，"
        "大更新时只刷新这一处。</p>"
        % C.esc(C.DIR_VIEWS + "/02-frontier.html"), reveal_index=nxt()))
    body.append("</div>")

    body.append("<h2>内容状态（两态登记）</h2>")
    body.append('<div class="notice"><strong>已写满 %d 个</strong>：八个区块（为什么需要它、机制说明、'
                "何时该用与不该用、实验台、证据、术语、失效模式、一句话小结）全部非空，"
                "可点进节点页完整阅读。<br><strong>架构在册 %d 个</strong>：知识架构位置已确定、"
                "导读已写，节点页待后续波次填充 —— 这一状态在组页与学习路径上以徽标显式标注，"
                "不隐藏、不静默留白。</div>" % (len(complete), len(registered)))
    body.append('<div class="table-scroll"><table><caption>已写满的节点（可直接阅读）。</caption>'
                "<thead><tr><th>节点</th><th>名称</th><th>分组</th><th>依赖深度</th></tr></thead><tbody>")
    for n in sorted(complete, key=lambda x: x["layer"]):
        body.append('<tr><td><a href="%s">%s</a></td><td>%s</td>'
                    '<td><a href="%s">%s</a></td><td>第 %d 层</td></tr>'
                    % (C.esc(C.node_page_rel(n["id"])), C.esc(n["id"]), C.esc(n["name"]),
                       C.esc(C.group_page_rel(n["group"])),
                       C.group_mark(n["group"]), n["layer"]))
    body.append("</tbody></table></div>")

    body.append("<h2>知识分组一览</h2>")
    body.append('<div class="legend">%s</div>'
                % "".join(C.group_chip(g["id"], g["name"], C.group_page_rel(g["id"])) for g in groups))

    body.append("<h2>怎么读这个站</h2>")
    body.append('<ol class="tight">'
                "<li>先读「地基」组：全站其余内容都建立在它给出的心智模型上。</li>"
                "<li>再按学习路径逐层推进；每层同层节点无先后约束，可按兴趣跳读。</li>"
                "<li>遇到某个方向的疑问时，从知识分组进组页看导读与组内节点表。</li>"
                "<li>判断某条技巧是否仍然成立时，先看新一代模块的状态徽标与取代关系。</li></ol>")
    body.append('<p class="lede">本站的依赖方向约定：边 A→B 表示先学 A 再学 B；'
                "层序由该方向推导，同一层的节点彼此无先后约束。</p>")
    return C.page_shell(BASE, "root", "ROOT", meta["mission"], "\n".join(body))


def generate(root=None):
    data = C.load_sources()
    dag = data["dag"]
    page_exists = {n["id"] for n in dag["nodes"] if n["content_status"] == "complete"}
    return {"index.html": root_page(dag, data["frontier"], page_exists)}


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
