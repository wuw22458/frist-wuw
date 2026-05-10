"""Agent 5: 生成交互式 HTML 报告（含图表可视化）。"""
import html as html_mod
import json
import math
import os
import time
from collections import Counter
from datetime import datetime

from utils import anonymize, format_bytes, format_count, setup_logging

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,"Microsoft YaHei","PingFang SC",sans-serif;background:#F4F5F7;color:#1A1A1A;padding:100px 20px 40px;min-height:100vh}

/* 顶部导航 */
.topnav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(255,255,255,0.94);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid #E8E8EA;padding:0 20px;display:flex;align-items:center;gap:6px;height:56px;overflow-x:auto}
.topnav a{flex-shrink:0;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:600;color:#666;text-decoration:none;transition:all .15s;min-height:44px;display:flex;align-items:center;gap:5px}
.topnav a:hover,.topnav a.active{background:#EEF2FF;color:#4A6CF7}
.topnav .nav-sep{width:1px;height:24px;background:#E8E8EA;margin:0 2px}
.topnav .nav-title{font-weight:800;font-size:14px;color:#1A1A1A;margin-right:12px;white-space:nowrap}

/* Header */
.header{text-align:center;padding:52px 32px;background:#FFFFFF;border-radius:20px;margin-bottom:24px;box-shadow:0 2px 12px rgba(0,0,0,0.04);position:relative;overflow:hidden}
.header::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#4A6CF7,#7C5CFC,#4A6CF7)}
.header h1{font-size:28px;font-weight:800;margin-bottom:6px;background:linear-gradient(135deg,#4A6CF7,#7C5CFC);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.header p{color:#888;font-size:14px}
.header .badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;margin:4px 3px;background:#EEF2FF;color:#4A6CF7}

/* 统计卡片 */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:12px;margin-bottom:24px}
.stat-card{background:#FFFFFF;border-radius:16px;padding:22px 14px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.04);position:relative;overflow:hidden}
.stat-card::after{content:'';position:absolute;bottom:0;left:20%;right:20%;height:3px;border-radius:3px;background:linear-gradient(90deg,#4A6CF7,#7C5CFC);opacity:0;transition:opacity .2s}
.stat-card:hover::after{opacity:1}
.stat-card .value{font-size:30px;font-weight:800;background:linear-gradient(135deg,#4A6CF7,#7C5CFC);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.stat-card .label{font-size:11px;color:#999;margin-top:4px}

/* 通用 section */
.section{background:#FFFFFF;border-radius:20px;padding:28px;margin-bottom:24px;box-shadow:0 2px 12px rgba(0,0,0,0.04)}
.section h2{font-size:17px;font-weight:700;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid #F0F0F2;display:flex;align-items:center;gap:8px}

/* 图表区 */
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:768px){.charts-row{grid-template-columns:1fr}}
.chart-box{background:#FAFAFB;border-radius:14px;padding:20px;text-align:center}
.chart-box h3{font-size:13px;font-weight:700;color:#666;margin-bottom:12px}
.chart-legend{display:flex;flex-wrap:wrap;gap:6px 14px;justify-content:center;margin-top:14px}
.legend-item{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:#555;white-space:nowrap}

/* 管线流程图 */
.pipeline-flow{display:flex;align-items:center;gap:0;justify-content:center;padding:24px 0;flex-wrap:wrap}
.pf-step{background:#FFFFFF;border:2px solid #EEE;border-radius:16px;padding:18px 22px;text-align:center;min-width:100px;transition:all .2s}
.pf-step:hover{border-color:#4A6CF7;box-shadow:0 4px 16px rgba(74,108,247,0.12)}
.pf-step .pf-num{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#4A6CF7,#7C5CFC);color:#FFF;font-weight:800;font-size:14px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:8px}
.pf-step .pf-name{font-weight:700;font-size:13px;color:#1A1A1A}
.pf-step .pf-stat{font-size:11px;color:#999;margin-top:2px}
.pf-arrow{font-size:20px;color:#CCC;margin:0 4px;font-weight:bold}

/* 搜索 + 筛选 */
.toolbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
.search-box{flex:1;min-width:200px;padding:10px 14px;border:1px solid #E0E0E3;border-radius:10px;font-size:13px;color:#333;background:#F9FAFB;outline:none;transition:border-color .15s}
.search-box:focus{border-color:#4A6CF7;background:#FFF}
.filter-btn{padding:7px 14px;border:1px solid #E0E0E3;border-radius:20px;background:#FFF;cursor:pointer;font-size:12px;color:#666;font-weight:500;min-height:40px;transition:all .15s;user-select:none}
.filter-btn:hover{border-color:#4A6CF7;color:#4A6CF7}
.filter-btn.active{background:#4A6CF7;color:#FFF;border-color:#4A6CF7}
.result-hint{font-size:12px;color:#999;margin-left:auto;white-space:nowrap}

/* 表格 */
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;background:#FAFAFB;color:#666;font-weight:700;border-bottom:2px solid #EEF0F4;font-size:11px;white-space:nowrap;cursor:pointer;user-select:none}
th:hover{color:#4A6CF7}
td{padding:9px 12px;border-bottom:1px solid #F5F5F7;color:#333;vertical-align:top}
tr.doc-row{transition:opacity .15s;cursor:pointer}
tr.doc-row:hover td{background:#F8F9FF}
tr.doc-row.hidden{display:none}
tr.doc-row.expanded td{background:#F8F9FF;border-bottom-color:#D8DCF0}
tr.doc-detail{display:none}
tr.doc-detail.show{display:table-row}
tr.doc-detail td{background:#F8F9FF;padding:4px 12px 16px 24px;color:#666;font-size:12px;line-height:1.7;white-space:pre-wrap;max-width:0}

.tag{display:inline-block;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:600;background:#EEF2FF;color:#4A6CF7;margin:1px 2px;cursor:pointer;transition:all .15s}
.tag:hover{background:#4A6CF7;color:#FFF}
.tag.active{background:#4A6CF7;color:#FFF}

.relation{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;margin:8px 0;background:#FAFAFB;border-radius:12px;font-size:13px;border-left:4px solid #DDD}
.type-before_after{background:#ECFDF5;color:#059669}
.type-cross_format{background:#FFFBEB;color:#D97706}
.type-same_student{background:#EEF2FF;color:#4A6CF7}
.type-same_topic{background:#F5F3FF;color:#7C3AED}

.timeline{font-family:"SF Mono","Fira Code","Consolas",monospace;font-size:12px;color:#555;padding:20px;background:#FAFAFB;border-radius:12px;white-space:pre-wrap;line-height:1.6;max-height:400px;overflow-y:auto}
.footer{text-align:center;padding:32px;color:#BBB;font-size:12px}

/* 回到顶部 */
#backTop{position:fixed;bottom:32px;right:32px;width:48px;height:48px;border-radius:50%;background:#4A6CF7;color:#FFF;border:none;cursor:pointer;font-size:18px;box-shadow:0 4px 16px rgba(74,108,247,0.35);opacity:0;transform:translateY(20px);transition:opacity .25s,transform .25s;z-index:99;display:flex;align-items:center;justify-content:center}
#backTop.visible{opacity:1;transform:translateY(0)}

@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}#backTop{transition:none}}
"""

JS = """
function filterTable(){
  var q=(document.getElementById('tableSearch').value||'').toLowerCase();
  var rows=document.querySelectorAll('tr.doc-row');
  var cats=document.querySelectorAll('.filter-btn.active');
  var activeCat=cats.length?Array.from(cats).map(function(b){return b.dataset.cat}):[];
  var visible=0;
  rows.forEach(function(r){
    var text=(r.textContent||'').toLowerCase();
    var tags=JSON.parse(r.dataset.tags||'[]');
    var matchSearch=!q||text.indexOf(q)>=0;
    var matchCat=!activeCat.length||activeCat.some(function(c){return tags.indexOf(c)>=0});
    if(matchSearch&&matchCat){r.classList.remove('hidden');visible++
    }else{r.classList.add('hidden');r.classList.remove('expanded');
      var d=r.nextElementSibling;if(d&&d.classList.contains('doc-detail'))d.classList.remove('show')}
  });
  document.getElementById('resultHint').textContent=visible+' / '+rows.length+' 条';
}

function setFilter(el,cat){
  el.classList.toggle('active');filterTable();
  var btns=document.querySelectorAll('.filter-btn');
  btns.forEach(function(b){if(b.dataset.cat===cat)b.classList.toggle('active',el.classList.contains('active'))});
}

function tagFilter(tag){
  var btn=document.querySelector('.filter-btn[data-cat="'+tag+'"]');
  if(btn)btn.classList.toggle('active');
  filterTable();
}

function sortTable(n){
  var table=document.getElementById('docTable');
  var tbody=table.querySelector('tbody');
  var rows=Array.from(tbody.querySelectorAll('tr.doc-row'));
  var asc=table.dataset.sortCol==String(n)&&table.dataset.sortDir!=='asc';
  rows.sort(function(a,b){
    var va=(a.cells[n].textContent||'').trim();
    var vb=(b.cells[n].textContent||'').trim();
    var na=parseFloat(va),nb=parseFloat(vb);
    if(!isNaN(na)&&!isNaN(nb))return asc?na-nb:nb-na;
    return asc?va.localeCompare(vb):vb.localeCompare(va);
  });
  rows.forEach(function(r){
    tbody.appendChild(r);
    var d=r.nextElementSibling;
    if(d&&d.classList.contains('doc-detail'))tbody.appendChild(d);
  });
  table.dataset.sortCol=n;table.dataset.sortDir=asc?'asc':'desc';
}

function toggleRow(row){
  var detail=row.nextElementSibling;
  if(detail&&detail.classList.contains('doc-detail')){
    var show=!detail.classList.contains('show');
    detail.classList.toggle('show',show);
    row.classList.toggle('expanded',show);
  }
}

function scrollToSection(id){
  document.getElementById(id).scrollIntoView({behavior:'smooth',block:'start'});
}

var backTop=null;
document.addEventListener('DOMContentLoaded',function(){
  backTop=document.getElementById('backTop');
  window.addEventListener('scroll',function(){
    backTop.classList.toggle('visible',window.scrollY>400);
  });
  backTop.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});
});
document.addEventListener('keydown',function(e){
  if(e.ctrlKey&&e.key==='k'){e.preventDefault();document.getElementById('tableSearch').focus()}
  if(e.key==='Escape'){document.getElementById('tableSearch').blur()}
});
"""

# 16 色板用于图表
CHART_COLORS = [
    "#4A6CF7", "#7C5CFC", "#F59E0B", "#10B981", "#EF4444",
    "#8B5CF6", "#06B6D4", "#F97316", "#6366F1", "#14B8A6",
    "#EC4899", "#84CC16", "#3B82F6", "#A855F7", "#E11D48",
]


class ReporterAgent:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.logger = setup_logging(output_dir)

    def _esc(self, text):
        return html_mod.escape(anonymize(str(text)))

    def run(self, manifest):
        self.logger.info("=" * 50)
        self.logger.info("[REPORTER] 生成交互式 HTML 报告")
        t0 = time.time()

        log_path = os.path.join(self.output_dir, "pipeline.log")
        log_text = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - 4000))
                log_text = f.read()

        html = self._build_html(manifest, log_text)
        report_path = os.path.join(self.output_dir, "report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        manifest["stats"]["reporter_time"] = round(time.time() - t0, 2)
        self.logger.info("[REPORTER] 报告已生成: %s", report_path)
        return manifest

    def _build_html(self, manifest, log_text):
        stats = manifest.get("stats", {})
        files = manifest.get("files", [])
        dup_groups = manifest.get("duplicate_groups", [])
        pid = self._esc(manifest.get("pipeline_run_id", "N/A"))
        source = self._esc(manifest.get("source_dir", "N/A"))

        all_cats = sorted(set(
            tag for f in files for tag in (f.get("tags") or [])
        ))

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MADIP — 文档智能管线报告</title>
<style>{CSS}</style>
</head>
<body>

<nav class="topnav">
<span class="nav-title">MADIP Report</span>
<a href="#stats" onclick="scrollToSection('stats');return false">📊 概览</a>
<span class="nav-sep"></span>
<a href="#charts" onclick="scrollToSection('charts');return false">📈 图表</a>
<span class="nav-sep"></span>
<a href="#pipeline" onclick="scrollToSection('pipeline');return false">🔀 管线</a>
<span class="nav-sep"></span>
<a href="#inventory" onclick="scrollToSection('inventory');return false">📋 清单</a>
<span class="nav-sep"></span>
<a href="#duplicates" onclick="scrollToSection('duplicates');return false">🔁 重复</a>
<span class="nav-sep"></span>
<a href="#relations" onclick="scrollToSection('relations');return false">🔗 关系</a>
<span class="nav-sep"></span>
<a href="#timeline" onclick="scrollToSection('timeline');return false">⏱️ 日志</a>
</nav>

<div class="container">
<div class="header">
<h1>Multi-Agent Document Intelligence Pipeline</h1>
<p>Run ID: {pid} &nbsp;|&nbsp; Source: {source}</p>
<div style="margin-top:12px">
<span class="badge">🔍 Scanner</span><span class="badge">📝 Extractor</span><span class="badge">🧠 Analyzer</span><span class="badge">🔄 Converter</span><span class="badge">📊 Reporter</span>
</div>
</div>

<div id="stats">{self._stats_grid(stats)}</div>
<div id="charts">{self._charts_section(files, stats)}</div>
<div id="pipeline">{self._pipeline_flow(stats)}</div>
<div id="inventory">{self._inventory_section(files, all_cats)}</div>
<div id="duplicates">{self._duplicates_section(dup_groups)}</div>
<div id="relations">{self._relations_section(files)}</div>
<div id="timeline">{self._timeline_section(stats, log_text)}</div>

<div class="footer">Generated by Multi-Agent Document Intelligence Pipeline v1.0 — {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</div>

<button id="backTop" aria-label="回到顶部">↑</button>
<script>{JS}</script>
</body></html>"""

    # ── 统计卡片 ──
    def _stats_grid(self, stats):
        items = [
            ("文件总数", stats.get("total_files", 0)),
            ("唯一文件", stats.get("unique_files", 0)),
            ("重复组", stats.get("duplicate_groups", 0)),
            ("文本字符", format_count(stats.get("total_chars", 0))),
            ("分析文档", stats.get("analyzed_count", 0)),
            ("发现关系", stats.get("relations_count", 0)),
            ("格式转换", stats.get("conversions", 0)),
            ("管线耗时", str(stats.get("scanner_time", 0) + stats.get("extractor_time", 0) + stats.get("analyzer_time", 0) + stats.get("converter_time", 0) + stats.get("reporter_time", 0))[:4] + "s"),
        ]
        cards = "".join(
            f'<div class="stat-card"><div class="value">{v}</div><div class="label">{k}</div></div>'
            for k, v in items
        )
        return f'<div class="stats-grid">{cards}</div>'

    # ── 图表区 ──
    def _charts_section(self, files, stats):
        fmt_counter = Counter(f["ext"] for f in files)
        cat_counter = Counter()
        for f in files:
            for t in (f.get("tags") or []):
                cat_counter[t] += 1

        donut = self._svg_donut(fmt_counter)
        bar_chart = self._svg_bars(cat_counter.most_common(10))

        return f"""<div class="section">
<h2>📈 数据可视化</h2>
<div class="charts-row">
<div class="chart-box">
<h3>📁 格式分布</h3>
{donut}
</div>
<div class="chart-box">
<h3>🏷️ 分类 Top 10</h3>
{bar_chart}
</div>
</div>
</div>"""

    def _svg_donut(self, counter):
        total = sum(counter.values())
        if total == 0:
            return '<p style="color:#999;padding:40px">无数据</p>'
        items = sorted(counter.items(), key=lambda x: -x[1])
        cx, cy, r_outer, r_inner = 110, 110, 85, 55
        gap = 1.5
        angle = -90
        paths = ""
        legend = ""
        for i, (label, count) in enumerate(items):
            pct = count / total
            sweep = max(pct * 360 - gap, 0.5)
            start_a, end_a = angle, angle + sweep
            start_rad = math.radians(start_a)
            end_rad = math.radians(end_a)
            x1o = cx + r_outer * math.cos(start_rad)
            y1o = cy + r_outer * math.sin(start_rad)
            x2o = cx + r_outer * math.cos(end_rad)
            y2o = cy + r_outer * math.sin(end_rad)
            x1i = cx + r_inner * math.cos(start_rad)
            y1i = cy + r_inner * math.sin(start_rad)
            x2i = cx + r_inner * math.cos(end_rad)
            y2i = cy + r_inner * math.sin(end_rad)
            large = 1 if sweep > 180 else 0
            color = CHART_COLORS[i % len(CHART_COLORS)]
            paths += (
                f'<path d="M{x1o:.1f},{y1o:.1f} A{r_outer},{r_outer} 0 {large},1 {x2o:.1f},{y2o:.1f} '
                f'L{x2i:.1f},{y2i:.1f} A{r_inner},{r_inner} 0 {large},0 {x1i:.1f},{y1i:.1f} Z" '
                f'fill="{color}" stroke="#fff" stroke-width="1.2"><title>{label}: {count} ({pct*100:.0f}%)</title></path>'
            )
            legend += (
                f'<span class="legend-item">'
                f'<svg width="10" height="10"><circle cx="5" cy="5" r="5" fill="{color}"/></svg>'
                f'{self._esc(label)} {count} ({pct*100:.0f}%)</span>'
            )
            angle = end_a + gap

        return f'''<svg viewBox="0 0 220 220" width="220" height="220">
<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="#FFF"/>
<text x="{cx}" y="{cy-6}" text-anchor="middle" font-size="24" font-weight="800" fill="#1A1A1A">{total}</text>
<text x="{cx}" y="{cy+14}" text-anchor="middle" font-size="11" fill="#999">文件总数</text>
{paths}
</svg>
<div class="chart-legend">{legend}</div>'''

    def _svg_bars(self, top_cats):
        if not top_cats:
            return '<p style="color:#999;padding:40px">无数据</p>'
        labels, counts = zip(*top_cats)
        max_c = max(counts) if counts else 1
        bar_h = 26
        gap = 8
        total_h = len(labels) * (bar_h + gap) + 16
        bars = ""
        for i, (label, count) in enumerate(zip(labels, counts)):
            y = 10 + i * (bar_h + gap)
            w = max(4, int(count / max_c * 180))
            color = CHART_COLORS[i % len(CHART_COLORS)]
            bars += f'''<text x="0" y="{y+16}" font-size="11" fill="#666" text-anchor="end">{self._esc(label)}</text>
<rect x="6" y="{y+4}" width="{w}" height="{bar_h}" rx="4" fill="{color}" opacity="0.85"/>
<text x="{w+10}" y="{y+16}" font-size="11" fill="#999">{count}</text>'''
        return f'''<svg viewBox="0 0 280 {total_h}" width="280" height="{total_h}">
<g transform="translate(80,0)">{bars}</g>
</svg>'''

    # ── 管线流程图 ──
    def _pipeline_flow(self, stats):
        agents = [
            ("Scanner", "🔍", "扫描", stats.get("total_files", 0), "文件"),
            ("Extractor", "📝", "提取", format_count(stats.get("total_chars", 0)), "字符"),
            ("Analyzer", "🧠", "分析", stats.get("relations_count", 0), "关系"),
            ("Converter", "🔄", "转换", stats.get("conversions", 0), "次"),
            ("Reporter", "📊", "报告", "1", "HTML"),
        ]
        steps = ""
        for i, (name, icon, action, val, unit) in enumerate(agents):
            t = stats.get(f"{name.lower()}_time", 0)
            steps += f"""<div class="pf-step">
<div class="pf-num">{i+1}</div>
<div class="pf-name">{icon} {name}</div>
<div style="font-size:11px;color:#999;margin-top:2px">{action}</div>
<div style="font-size:20px;font-weight:800;color:#4A6CF7;margin-top:4px">{val}</div>
<div style="font-size:10px;color:#999">{unit}</div>
<div style="font-size:10px;color:#BBB;margin-top:1px">{t:.1f}s</div>
</div>"""
            if i < len(agents) - 1:
                steps += '<span class="pf-arrow">→</span>'
        return f"""<div class="section">
<h2>🔀 管线流程</h2>
<div class="pipeline-flow">{steps}</div>
</div>"""

    # ── 文档清单 ──
    def _inventory_section(self, files, all_cats):
        rows = ""
        for f in files:
            dup = " 🔁" if f.get("is_duplicate") else ""
            summary = self._esc((f.get("summary") or "")[:80])
            tags = f.get("tags") or []
            tags_html = "".join(
                f'<span class="tag" onclick="event.stopPropagation();tagFilter(\'{self._esc(t)}\')">{self._esc(t)}</span>' for t in tags[:5]
            )
            tags_json = self._esc(json.dumps(tags, ensure_ascii=False))
            detail = self._esc((f.get("text_content") or "")[:300])
            rows += f"""<tr class="doc-row" data-tags='{tags_json}' onclick="toggleRow(this)">
<td>{format_bytes(f.get('size_bytes', 0))}</td>
<td style="font-weight:600;color:#4A6CF7">{f.get('ext', '')}</td>
<td>{self._esc(f['filename'])}{dup}</td>
<td>{tags_html}</td>
<td style="color:#666;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{summary}</td>
</tr>
<tr class="doc-detail"><td></td><td></td><td colspan="3"><div style="max-height:120px;overflow-y:auto">{detail}</div></td></tr>"""

        cat_btns = "".join(
            f'<button class="filter-btn" data-cat="{self._esc(c)}" onclick="setFilter(this,\'{self._esc(c)}\')">{self._esc(c)}</button>'
            for c in all_cats
        )

        return f"""<div class="section">
<h2>📋 文档清单</h2>
<div class="toolbar">
<input type="text" id="tableSearch" class="search-box" placeholder="搜索文件名、内容…（Ctrl+K 聚焦）" oninput="filterTable()">
{cat_btns}
<span class="result-hint" id="resultHint">{len(files)} / {len(files)} 条</span>
</div>
<table id="docTable">
<thead><tr>
<th onclick="sortTable(0)">大小 ⇅</th>
<th onclick="sortTable(1)">格式 ⇅</th>
<th onclick="sortTable(2)">文件名 ⇅</th>
<th>标签</th>
<th>摘要</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
<p style="color:#999;font-size:11px;margin-top:8px">💡 点击行展开预览 &nbsp;|&nbsp; 点击标签筛选 &nbsp;|&nbsp; 点击表头排序 &nbsp;|&nbsp; Ctrl+K 搜索</p>
</div>"""

    # ── 重复文件 ──
    def _duplicates_section(self, dup_groups):
        if not dup_groups:
            return '<div class="section"><h2>🔁 重复文件</h2><p style="color:#999;text-align:center;padding:24px">✅ 未发现重复文件</p></div>'
        rows = ""
        for group in dup_groups:
            orig_name = self._esc(os.path.basename(group[0]))
            for dup_path in group[1:]:
                dup_name = self._esc(os.path.basename(dup_path))
                rows += f"<tr><td>{orig_name}</td><td>{dup_name}</td></tr>"
        return f"""<div class="section">
<h2>🔁 重复文件（{len(dup_groups)} 组）</h2>
<table><thead><tr><th>原始文件</th><th>重复文件</th></tr></thead><tbody>{rows}</tbody></table>
</div>"""

    # ── 文档关系 ──
    def _relations_section(self, files):
        items = []
        seen = set()
        for f in files:
            for r in f.get("relationships", []):
                src = self._esc(f["filename"])
                tgt = self._esc(os.path.basename(r.get("target", "")))
                rtype = r.get("type", "")
                desc = self._esc(r.get("description", ""))
                key = (f["path"], r.get("target"), rtype)
                if key in seen:
                    continue
                seen.add(key)
                rel_label = {"before_after": "版本迭代", "cross_format": "跨格式",
                             "same_student": "同学号", "same_topic": "同主题"}.get(rtype, rtype)
                items.append(f"""<div class="relation">
<span class="relation-type type-{self._esc(rtype)}" style="display:inline-block;padding:3px 10px;border-radius:8px;font-size:10px;font-weight:700;min-width:72px;text-align:center">{rel_label}</span>
<div><strong>{src}</strong> ↔ <strong>{tgt}</strong><br><span style="color:#888;font-size:12px">{desc}</span></div>
</div>""")

        if not items:
            return '<div class="section"><h2>🔗 文档关系</h2><p style="color:#999;text-align:center;padding:24px">未发现显著关系</p></div>'
        shown = items[:200]
        more = f'<p style="color:#999;text-align:center;padding:12px">… 还有 {len(items) - 200} 条关系未显示</p>' if len(items) > 200 else ""
        return f"""<div class="section">
<h2>🔗 文档关系（{len(items)} 条）</h2>
<div id="relContainer">{''.join(shown)}</div>{more}
</div>"""

    # ── 时间线 + 日志 ──
    def _timeline_section(self, stats, log_text):
        agents = [
            ("Scanner", stats.get("scanner_time", 0)),
            ("Extractor", stats.get("extractor_time", 0)),
            ("Analyzer", stats.get("analyzer_time", 0)),
            ("Converter", stats.get("converter_time", 0)),
            ("Reporter", stats.get("reporter_time", 0)),
        ]
        total = sum(t for _, t in agents)
        max_t = max(t for _, t in agents) or 0.1
        bars = ""
        for name, t in agents:
            pct = int(t / max_t * 100)
            bars += f"""<div style="display:flex;align-items:center;gap:12px;margin:8px 0">
<span style="font-size:13px;font-weight:600;min-width:90px;text-align:right;color:#666">{name}</span>
<div style="flex:1;height:8px;background:#F0F0F2;border-radius:4px;overflow:hidden"><div style="height:100%;border-radius:4px;background:linear-gradient(90deg,#4A6CF7,#7C5CFC);width:{pct}%"></div></div>
<span style="font-size:11px;color:#999;min-width:42px">{t:.1f}s</span>
</div>"""
        log_safe = self._esc(log_text or "无日志")
        return f"""<div class="section">
<h2>⏱️ 管线执行时间线（总计 {total:.1f}s）</h2>
{bars}
<div class="timeline" style="margin-top:16px">{log_safe}</div>
</div>"""
