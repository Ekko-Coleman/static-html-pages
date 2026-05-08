#!/usr/bin/env python3
"""Assemble the Vendor Explorer single-file HTML."""
import json, gzip, base64, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(OUT, "vendors_data.json")

with open(DATA_JSON) as f:
    data_str = f.read()

gz = gzip.compress(data_str.encode("utf-8"), compresslevel=9)
b64 = base64.b64encode(gz).decode("ascii")

# US state tile-grid layout (row, col) — common cartogram positions
TILE_GRID = {
    "AK": (0, 0),  "ME": (0, 11),
    "VT": (1, 10), "NH": (1, 11),
    "WA": (2, 1),  "ID": (2, 2),  "MT": (2, 3),  "ND": (2, 4),  "MN": (2, 5),
    "MI": (2, 8),  "NY": (2, 9),  "MA": (2, 10), "WI": (2, 7),  "CT": (3, 11),
    "OR": (3, 1),  "UT": (3, 2),  "WY": (3, 3),  "SD": (3, 4),  "IA": (3, 5),
    "IL": (3, 6),  "IN": (3, 7),  "OH": (3, 8),  "PA": (3, 9),  "NJ": (3, 10),
    "CA": (4, 1),  "NV": (4, 2),  "CO": (4, 3),  "NE": (4, 4),  "MO": (4, 5),
    "KY": (4, 6),  "WV": (4, 7),  "VA": (4, 8),  "MD": (4, 9),  "DE": (4, 10),
    "RI": (4, 11),
    "AZ": (5, 2),  "NM": (5, 3),  "KS": (5, 4),  "AR": (5, 5),  "TN": (5, 6),
    "NC": (5, 7),  "SC": (5, 8),  "DC": (5, 9),
    "HI": (6, 0),  "OK": (6, 4),  "LA": (6, 5),  "MS": (6, 6),  "AL": (6, 7),
    "GA": (6, 8),
    "TX": (7, 4),  "FL": (7, 8),
}

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia",
    "FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois",
    "IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada",
    "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York",
    "NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon",
    "PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Appraiser Vendor Explorer</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0d1117;
    --panel: #161b22;
    --panel-2: #1f2630;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --accent-2: #7ee787;
    --warn: #f1c40f;
    --danger: #f85149;
    --shadow: 0 1px 0 rgba(255,255,255,0.04), 0 4px 12px rgba(0,0,0,0.35);
  }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; background:var(--bg); color:var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px; line-height: 1.45; }
  a { color: var(--accent); text-decoration: none; }
  .layout { padding: 12px 16px 80px; max-width: 1800px; margin: 0 auto; }

  /* Header */
  .topbar { display:flex; align-items:center; gap:12px; padding:10px 4px 14px;
    border-bottom:1px solid var(--border); margin-bottom:14px; flex-wrap:wrap; }
  .topbar h1 { font-size:18px; margin:0; font-weight:600; letter-spacing:-0.01em; }
  .badge { background:var(--panel-2); color:var(--text); padding:3px 9px;
    border-radius:999px; font-size:12px; border:1px solid var(--border); }
  .badge.accent { color:var(--accent); border-color:rgba(88,166,255,0.4); }
  .spacer { flex:1; }
  .btn { background:var(--panel-2); color:var(--text); border:1px solid var(--border);
    padding:6px 12px; border-radius:6px; cursor:pointer; font-size:12px;
    display:inline-flex; align-items:center; gap:6px; transition:all .15s; }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.primary { background: var(--accent); color:#0d1117; border-color:var(--accent); font-weight:600; }
  .btn.primary:hover { background: #79b8ff; color:#0d1117; }
  .btn.ghost { background: transparent; }

  /* View toggle */
  .view-toggle { display:inline-flex; border:1px solid var(--border); border-radius:6px;
    overflow:hidden; background:var(--panel-2); }
  .view-toggle button { background:transparent; color:var(--muted); border:0;
    padding:6px 12px; font-size:12px; cursor:pointer; }
  .view-toggle button.active { background: var(--accent); color:#0d1117; font-weight:600; }
  .view-toggle button:hover:not(.active) { color:var(--text); }

  /* KPIs */
  .kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap:10px; margin-bottom:14px; }
  .kpi { background:var(--panel); border:1px solid var(--border); border-radius:8px;
    padding:12px; box-shadow: var(--shadow); }
  .kpi .label { font-size:11px; color:var(--muted); text-transform:uppercase;
    letter-spacing:.05em; margin-bottom:4px; }
  .kpi .value { font-size:22px; font-weight:600; color:var(--text); }
  .kpi .sub { font-size:11px; color:var(--muted); margin-top:2px; }
  .kpi .pct { color:var(--accent-2); }

  /* Filters */
  .filters { display:flex; gap:10px; flex-wrap:wrap; padding:12px;
    background:var(--panel); border:1px solid var(--border); border-radius:8px;
    margin-bottom:14px; box-shadow: var(--shadow); position:sticky; top:0; z-index:50; }
  .filter-group { display:flex; flex-direction:column; gap:4px; min-width:160px; }
  .filter-group label { font-size:11px; color:var(--muted); text-transform:uppercase;
    letter-spacing:.05em; }
  .input, .select { background:var(--panel-2); color:var(--text); border:1px solid var(--border);
    padding:6px 10px; border-radius:6px; font-size:13px; min-width:160px; }
  .input:focus, .select:focus { outline:none; border-color:var(--accent); }
  .search-box { flex: 2; min-width: 240px; position: relative; }
  .search-box input { width:100%; padding-left:30px; }
  .search-box::before { content:"\1F50D"; position:absolute; left:9px; top:7px;
    opacity:.5; font-size:13px; pointer-events:none; }
  .triseg { display:inline-flex; border:1px solid var(--border); border-radius:6px;
    overflow:hidden; background:var(--panel-2); }
  .triseg button { background:transparent; color:var(--muted); border:0;
    padding:6px 10px; font-size:12px; cursor:pointer; min-width:48px; }
  .triseg button.active { background: var(--accent); color:#0d1117; font-weight:600; }
  .triseg button.active.no { background: var(--danger); color:#fff; }

  /* Multi-select dropdown */
  .ms { position:relative; min-width:180px; }
  .ms-btn { background:var(--panel-2); color:var(--text); border:1px solid var(--border);
    padding:6px 10px; border-radius:6px; cursor:pointer; min-width:180px; text-align:left;
    display:flex; align-items:center; justify-content:space-between; gap:6px; }
  .ms-btn .count { background:var(--accent); color:#0d1117; font-size:11px; padding:1px 6px;
    border-radius:999px; font-weight:600; }
  .ms-panel { display:none; position:absolute; top:calc(100% + 4px); left:0;
    background:var(--panel); border:1px solid var(--border); border-radius:6px;
    z-index:100; min-width:240px; max-width:340px; max-height:320px; overflow-y:auto;
    box-shadow: var(--shadow); padding:6px; }
  .ms.open .ms-panel { display:block; }
  .ms-search { width:100%; margin-bottom:6px; padding:5px 8px; background:var(--panel-2);
    border:1px solid var(--border); color:var(--text); border-radius:4px; font-size:12px; }
  .ms-options { max-height:240px; overflow-y:auto; }
  .ms-option { display:flex; align-items:center; gap:8px; padding:4px 6px; cursor:pointer;
    border-radius:4px; font-size:12px; }
  .ms-option:hover { background:var(--panel-2); }
  .ms-option input { margin:0; }
  .ms-option .count-pill { margin-left:auto; color:var(--muted); font-size:11px; }
  .ms-actions { display:flex; gap:4px; padding-top:6px; border-top:1px solid var(--border); margin-top:4px; }
  .ms-actions button { flex:1; }

  /* Charts row */
  .charts-row { display:grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 2fr;
    gap:10px; margin-bottom:14px; }
  @media (max-width: 1100px) { .charts-row { grid-template-columns: 1fr 1fr; } }
  .chart-card { background:var(--panel); border:1px solid var(--border); border-radius:8px;
    padding:10px 12px; box-shadow: var(--shadow); position:relative; min-height: 200px; }
  .chart-card h3 { font-size:12px; color:var(--muted); margin:0 0 6px;
    text-transform:uppercase; letter-spacing:.05em; font-weight:500; }
  .chart-card .chart-wrap { position:relative; height: 180px; }
  .chart-card .hint { position:absolute; top:8px; right:10px; font-size:10px; color:var(--muted); }

  /* Main view */
  .main-view { background:var(--panel); border:1px solid var(--border); border-radius:8px;
    box-shadow: var(--shadow); overflow:hidden; }
  .main-view header { display:flex; align-items:center; gap:10px; padding:10px 14px;
    border-bottom:1px solid var(--border); flex-wrap:wrap; }
  .main-view header .title { font-size:14px; font-weight:600; }
  .main-view .body { min-height: 400px; }

  /* Table view */
  .table-wrap { overflow:auto; max-height: 70vh; }
  table.tbl { width:100%; border-collapse: collapse; font-size:12px; }
  table.tbl th { position: sticky; top:0; background: var(--panel-2);
    color:var(--muted); text-transform:uppercase; font-size:10px; letter-spacing:.05em;
    padding:8px 10px; text-align:left; border-bottom:1px solid var(--border); cursor:pointer;
    white-space:nowrap; user-select:none; }
  table.tbl th:hover { color:var(--accent); }
  table.tbl th.sorted { color:var(--accent); }
  table.tbl th.sorted::after { content: attr(data-arrow); margin-left:4px; }
  table.tbl td { padding:6px 10px; border-bottom:1px solid var(--border); vertical-align:top; }
  table.tbl tr:hover td { background: var(--panel-2); }
  .yn { display:inline-block; width:18px; text-align:center; border-radius:4px;
    font-size:10px; font-weight:700; padding:1px 4px; }
  .yn.yes { background: rgba(126,231,135,0.12); color: var(--accent-2); }
  .yn.no { background: rgba(139,148,158,0.1); color: var(--muted); }
  .row-actions { display:flex; gap:4px; }
  .row-actions button { background:var(--panel-2); border:1px solid var(--border); color:var(--muted);
    padding:2px 6px; border-radius:4px; font-size:11px; cursor:pointer; }
  .row-actions button:hover { color:var(--accent); border-color:var(--accent); }
  .pager { display:flex; align-items:center; gap:8px; padding:10px 14px;
    border-top:1px solid var(--border); flex-wrap:wrap; }
  .pager .page-info { color:var(--muted); font-size:12px; }
  .pager .pgbtn { background:var(--panel-2); border:1px solid var(--border); color:var(--text);
    padding:4px 10px; border-radius:4px; font-size:12px; cursor:pointer; }
  .pager .pgbtn:disabled { opacity:.4; cursor:not-allowed; }
  .pager select { background:var(--panel-2); color:var(--text); border:1px solid var(--border);
    padding:3px 8px; border-radius:4px; font-size:12px; }

  /* Card view */
  .cards { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap:10px; padding:14px; max-height: 70vh; overflow-y:auto; }
  .card { background: var(--panel-2); border:1px solid var(--border); border-radius:6px;
    padding:10px 12px; cursor:pointer; transition: all .15s; }
  .card:hover { border-color: var(--accent); }
  .card .name { font-weight:600; font-size:13px; margin-bottom:2px; }
  .card .co { font-size:11px; color:var(--muted); margin-bottom:6px; }
  .card .meta { display:flex; gap:6px; flex-wrap:wrap; font-size:11px; color:var(--muted); }
  .card .pills { display:flex; gap:4px; margin-top:6px; flex-wrap:wrap; }
  .card .pill { font-size:10px; padding:1px 6px; border-radius:999px; background:rgba(126,231,135,0.12);
    color:var(--accent-2); font-weight:600; }
  .card .pill.muted { background:rgba(139,148,158,0.1); color:var(--muted); }

  /* Map view */
  .map-wrap { padding:14px; }
  .map-wrap .legend { display:flex; gap:6px; align-items:center; font-size:11px; color:var(--muted); margin-bottom:10px; }
  .map-wrap .legend .scale { display:inline-flex; gap:2px; }
  .map-wrap .legend .scale span { width:18px; height:10px; display:inline-block; border:1px solid var(--border); }
  .tile-map { display:grid;
    grid-template-columns: repeat(12, minmax(40px, 60px));
    grid-auto-rows: 50px;
    gap:4px; justify-content:center; margin: 0 auto; max-width:780px; }
  .tile {
    border:1px solid var(--border); border-radius:6px; display:flex; flex-direction:column;
    justify-content:center; align-items:center; cursor:pointer; user-select:none;
    transition: all .12s; font-size:11px; font-weight:600; padding:2px;
  }
  .tile:hover { transform: scale(1.05); border-color: var(--accent); z-index: 2; }
  .tile.selected { outline: 2px solid var(--accent); outline-offset: 1px; }
  .tile .abbr { font-size:13px; font-weight:700; }
  .tile .num { font-size:10px; opacity:.85; }
  .tile.empty { opacity:.2; pointer-events:none; }

  /* Modal */
  .modal-overlay { display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    background:rgba(0,0,0,0.6); z-index:200; align-items:center; justify-content:center; padding:20px; }
  .modal-overlay.open { display:flex; }
  .modal { background:var(--panel); border:1px solid var(--border); border-radius:8px;
    width:100%; max-width:560px; max-height:90vh; overflow-y:auto; box-shadow: var(--shadow); }
  .modal header { padding:14px 18px; border-bottom:1px solid var(--border);
    display:flex; align-items:center; justify-content:space-between; }
  .modal header h2 { margin:0; font-size:16px; }
  .modal .body { padding:14px 18px; }
  .modal .row { display:flex; gap:10px; margin-bottom:8px; font-size:13px; }
  .modal .row .k { color:var(--muted); min-width:120px; }
  .modal .row .v { flex:1; word-break:break-word; }
  .tag-list { display:flex; gap:4px; flex-wrap:wrap; margin-top:6px; }
  .tag { background: rgba(88,166,255,0.12); color:var(--accent); padding:2px 8px;
    border-radius:999px; font-size:11px; display:inline-flex; align-items:center; gap:4px; }
  .tag .x { cursor:pointer; opacity:.6; }
  .tag .x:hover { opacity:1; color:var(--danger); }
  .tag-input { display:flex; gap:6px; margin-top:6px; }
  .tag-input input { flex:1; }

  /* Loading */
  #loader { position:fixed; top:0; left:0; right:0; bottom:0; background:var(--bg);
    display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:1000; }
  #loader .spinner { width:40px; height:40px; border:3px solid var(--panel-2);
    border-top-color: var(--accent); border-radius:50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  #loader .label { margin-top:12px; color:var(--muted); font-size:13px; }

  /* Hidden */
  .hidden { display:none !important; }

  /* Active filter chips */
  .active-filters { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
  .chip { background:rgba(88,166,255,0.12); color:var(--accent); padding:2px 8px;
    border-radius:999px; font-size:11px; display:inline-flex; align-items:center; gap:6px;
    border:1px solid rgba(88,166,255,0.3); }
  .chip .x { cursor:pointer; opacity:.7; font-weight:bold; }
  .chip .x:hover { opacity:1; color:var(--danger); }

  /* Group view */
  .groups { padding: 8px 14px; }
  .group { background:var(--panel-2); border:1px solid var(--border); border-radius:6px;
    margin-bottom:6px; overflow:hidden; }
  .group-header { padding:8px 12px; cursor:pointer; display:flex; align-items:center;
    gap:8px; user-select:none; }
  .group-header:hover { background: rgba(88,166,255,0.05); }
  .group-header .name { font-weight:600; font-size:13px; }
  .group-header .count { color:var(--muted); font-size:11px; }
  .group-body { display:none; padding: 0 12px 12px; }
  .group.open .group-body { display:block; }

  /* Top counties section */
  .counties-list { font-size:12px; }
  .counties-list .row { display:flex; justify-content:space-between; padding:3px 0;
    border-bottom: 1px solid rgba(255,255,255,0.03); cursor:pointer; }
  .counties-list .row:hover { color: var(--accent); }
  .counties-list .row .num { color:var(--muted); }

  /* Color scale for choropleth */
  .scale-0 { background:#0d1117; color:var(--muted); }
  .scale-1 { background:#0a3069; color:#79b8ff; }
  .scale-2 { background:#1158c7; color:#fff; }
  .scale-3 { background:#388bfd; color:#fff; }
  .scale-4 { background:#58a6ff; color:#0d1117; }
  .scale-5 { background:#79b8ff; color:#0d1117; }
</style>
</head>
<body>
<div id="loader">
  <div class="spinner"></div>
  <div class="label">Loading 38,295 vendors…</div>
</div>

<div class="layout hidden" id="app">
  <div class="topbar">
    <h1>Appraiser Vendor Explorer</h1>
    <span class="badge accent" id="result-count">0 / 0</span>
    <div class="active-filters" id="active-filters"></div>
    <div class="spacer"></div>
    <div class="view-toggle" id="view-toggle">
      <button data-view="table" class="active">List</button>
      <button data-view="cards">Cards</button>
      <button data-view="map">Map</button>
      <button data-view="groups">Groups</button>
    </div>
    <button class="btn ghost" id="clear-filters" title="Clear all filters">Clear</button>
    <button class="btn primary" id="export-btn">Export CSV</button>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="filters" id="filters">
    <div class="search-box">
      <input class="input" id="search" placeholder="Search name, company, email, address…" />
    </div>
    <div class="filter-group">
      <label>State</label>
      <div class="ms" id="ms-state">
        <button class="ms-btn">All states <span class="count hidden">0</span></button>
        <div class="ms-panel">
          <input class="ms-search" placeholder="Filter…" />
          <div class="ms-options"></div>
          <div class="ms-actions">
            <button class="btn" data-act="clear">Clear</button>
            <button class="btn" data-act="close">Done</button>
          </div>
        </div>
      </div>
    </div>
    <div class="filter-group">
      <label>Coverage county</label>
      <div class="ms" id="ms-county">
        <button class="ms-btn">Any county <span class="count hidden">0</span></button>
        <div class="ms-panel">
          <input class="ms-search" placeholder="Filter…" />
          <div class="ms-options"></div>
          <div class="ms-actions">
            <button class="btn" data-act="clear">Clear</button>
            <button class="btn" data-act="close">Done</button>
          </div>
        </div>
      </div>
    </div>
    <div class="filter-group">
      <label>FHA</label>
      <div class="triseg" data-key="fha">
        <button data-v="any" class="active">Any</button>
        <button data-v="yes">Yes</button>
        <button data-v="no">No</button>
      </div>
    </div>
    <div class="filter-group">
      <label>VA</label>
      <div class="triseg" data-key="va">
        <button data-v="any" class="active">Any</button>
        <button data-v="yes">Yes</button>
        <button data-v="no">No</button>
      </div>
    </div>
    <div class="filter-group">
      <label>ACH</label>
      <div class="triseg" data-key="ach">
        <button data-v="any" class="active">Any</button>
        <button data-v="yes">Yes</button>
        <button data-v="no">No</button>
      </div>
    </div>
    <div class="filter-group">
      <label>Tags</label>
      <div class="ms" id="ms-tag">
        <button class="ms-btn">Any tag <span class="count hidden">0</span></button>
        <div class="ms-panel">
          <input class="ms-search" placeholder="Filter…" />
          <div class="ms-options"></div>
          <div class="ms-actions">
            <button class="btn" data-act="clear">Clear</button>
            <button class="btn" data-act="close">Done</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="charts-row">
    <div class="chart-card">
      <h3>Top states</h3>
      <span class="hint">click bar to filter</span>
      <div class="chart-wrap"><canvas id="chart-states"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>FHA</h3>
      <div class="chart-wrap"><canvas id="chart-fha"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>VA</h3>
      <div class="chart-wrap"><canvas id="chart-va"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>ACH</h3>
      <div class="chart-wrap"><canvas id="chart-ach"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Top counties (coverage)</h3>
      <span class="hint">click row to filter</span>
      <div class="chart-wrap" style="overflow:auto;">
        <div class="counties-list" id="counties-list"></div>
      </div>
    </div>
  </div>

  <div class="main-view">
    <header>
      <span class="title" id="view-title">List view</span>
      <span class="badge" id="view-sub"></span>
      <div class="spacer"></div>
      <div class="filter-group" style="flex-direction:row; align-items:center; gap:6px;" id="group-by-wrap">
        <label style="margin:0;">Group by</label>
        <select class="select" id="group-by">
          <option value="state">State</option>
          <option value="fha">FHA</option>
          <option value="va">VA</option>
          <option value="ach">ACH</option>
          <option value="city">City</option>
          <option value="company">Company</option>
        </select>
      </div>
    </header>
    <div class="body">
      <div id="view-table" class="hidden">
        <div class="table-wrap">
          <table class="tbl" id="tbl">
            <thead><tr id="tbl-head"></tr></thead>
            <tbody id="tbl-body"></tbody>
          </table>
        </div>
        <div class="pager">
          <span class="page-info" id="page-info">—</span>
          <div class="spacer"></div>
          Page size:
          <select id="page-size">
            <option>25</option><option selected>50</option><option>100</option><option>250</option><option>500</option>
          </select>
          <button class="pgbtn" id="prev">‹ Prev</button>
          <button class="pgbtn" id="next">Next ›</button>
        </div>
      </div>
      <div id="view-cards" class="hidden">
        <div class="cards" id="cards-grid"></div>
      </div>
      <div id="view-map" class="hidden">
        <div class="map-wrap">
          <div class="legend">
            <span>Vendors per state:</span>
            <span class="scale">
              <span class="scale-0"></span>
              <span class="scale-1"></span>
              <span class="scale-2"></span>
              <span class="scale-3"></span>
              <span class="scale-4"></span>
              <span class="scale-5"></span>
            </span>
            <span>fewer → more (click any state to filter)</span>
          </div>
          <div class="tile-map" id="tile-map"></div>
        </div>
      </div>
      <div id="view-groups" class="hidden">
        <div class="groups" id="groups-list"></div>
      </div>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <header>
      <h2 id="modal-title">Vendor</h2>
      <button class="btn ghost" id="modal-close">✕</button>
    </header>
    <div class="body" id="modal-body"></div>
  </div>
</div>

<script>
/* === Data bootstrap (gzip+base64) === */
const _DATA_B64 = "__DATA_B64__";
const _TILE_GRID = __TILE_GRID__;
const _STATE_NAMES = __STATE_NAMES__;

async function decompressData() {
  const bin = Uint8Array.from(atob(_DATA_B64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const stream = new Blob([bin]).stream().pipeThrough(ds);
  const text = await new Response(stream).text();
  return JSON.parse(text);
}

(async () => {
let DATA;
try { DATA = await decompressData(); }
catch (e) { document.getElementById('loader').innerHTML = '<div style="color:#f85149">Failed to load data: '+e.message+'</div>'; throw e; }

/* === Build indexes === */
const N = DATA.length;
DATA.forEach((r, idx) => { r._id = idx; });
const stateCounts = {};
const countyCounts = {};
for (const r of DATA) {
  if (r.s) stateCounts[r.s] = (stateCounts[r.s] || 0) + 1;
  for (const c of (r.cv || [])) countyCounts[c] = (countyCounts[c] || 0) + 1;
}
const allStates = Object.keys(stateCounts).sort();
const allCounties = Object.keys(countyCounts).sort();
const totalRows = N;

/* === LocalStorage tags === */
const TAG_KEY = 'vendor_explorer_tags_v1';
const VIEW_KEY = 'vendor_explorer_view_v1';
let tagDict = {};
try { tagDict = JSON.parse(localStorage.getItem(TAG_KEY) || '{}'); } catch(_){ tagDict = {}; }
function saveTags() { try { localStorage.setItem(TAG_KEY, JSON.stringify(tagDict)); } catch(_){} }
function getTags(id) { return tagDict[id] || []; }
function setTags(id, arr) { if (arr && arr.length) tagDict[id] = arr; else delete tagDict[id]; saveTags(); }
function allTagsList() {
  const c = {};
  for (const k in tagDict) for (const t of tagDict[k]) c[t] = (c[t] || 0) + 1;
  return Object.keys(c).sort().map(t => ({ tag: t, count: c[t] }));
}

/* === Filter state === */
const state = {
  search: '',
  states: new Set(),
  counties: new Set(),
  tags: new Set(),
  fha: 'any',  // any|yes|no
  va: 'any',
  ach: 'any',
  view: 'table',
  page: 0,
  pageSize: 50,
  sortKey: 'n',
  sortDir: 1,
  groupBy: 'state',
};
try {
  const saved = JSON.parse(localStorage.getItem(VIEW_KEY) || '{}');
  if (saved.view) state.view = saved.view;
  if (saved.pageSize) state.pageSize = saved.pageSize;
} catch(_){}
function persistView() { try { localStorage.setItem(VIEW_KEY, JSON.stringify({ view:state.view, pageSize:state.pageSize })); } catch(_){} }

/* === Filtering === */
let filtered = [];  // array of indices
function applyFilters() {
  const q = state.search.trim().toLowerCase();
  const useStates = state.states.size > 0;
  const useCounties = state.counties.size > 0;
  const useTags = state.tags.size > 0;
  const out = [];
  for (let i=0; i<N; i++) {
    const r = DATA[i];
    if (useStates && !state.states.has(r.s)) continue;
    if (state.fha !== 'any' && r.fha !== (state.fha === 'yes')) continue;
    if (state.va !== 'any' && r.va !== (state.va === 'yes')) continue;
    if (state.ach !== 'any' && r.ach !== (state.ach === 'yes')) continue;
    if (useCounties) {
      let any = false;
      for (const c of r.cv) { if (state.counties.has(c)) { any = true; break; } }
      if (!any) continue;
    }
    if (useTags) {
      const t = tagDict[r._id] || [];
      let any = false;
      for (const x of t) { if (state.tags.has(x)) { any = true; break; } }
      if (!any) continue;
    }
    if (q) {
      const hay = (r.n + ' ' + r.co + ' ' + r.e + ' ' + r.a + ' ' + r.c + ' ' + r.i).toLowerCase();
      if (!hay.includes(q)) continue;
    }
    out.push(i);
  }
  filtered = out;
}

/* === Aggregations from filtered === */
function agg() {
  const a = { byState: {}, byCounty: {}, fha: { yes:0, no:0 }, va: { yes:0, no:0 }, ach: { yes:0, no:0 }, companies: new Set(), cities: new Set() };
  for (const i of filtered) {
    const r = DATA[i];
    if (r.s) a.byState[r.s] = (a.byState[r.s] || 0) + 1;
    for (const c of r.cv) a.byCounty[c] = (a.byCounty[c] || 0) + 1;
    a[r.fha ? 'fha' : 'fha'][r.fha ? 'yes':'no']++;
    a[r.va ? 'va' : 'va'][r.va ? 'yes':'no']++;
    a[r.ach ? 'ach' : 'ach'][r.ach ? 'yes':'no']++;
    if (r.co) a.companies.add(r.co);
    if (r.c) a.cities.add(r.c);
  }
  return a;
}

/* === KPIs === */
function renderKPIs(a) {
  const total = filtered.length;
  const pct = (x) => total ? Math.round(100 * x / total) + '%' : '—';
  const items = [
    { label: 'Vendors', value: total.toLocaleString(), sub: total === N ? 'all' : (Math.round(100*total/N)) + '% of ' + N.toLocaleString() },
    { label: 'States', value: Object.keys(a.byState).length },
    { label: 'Companies', value: a.companies.size.toLocaleString() },
    { label: 'FHA', value: a.fha.yes.toLocaleString(), sub: pct(a.fha.yes), pctClass: 'pct' },
    { label: 'VA', value: a.va.yes.toLocaleString(), sub: pct(a.va.yes), pctClass: 'pct' },
    { label: 'ACH', value: a.ach.yes.toLocaleString(), sub: pct(a.ach.yes), pctClass: 'pct' },
    { label: 'Tagged', value: filtered.filter(i => getTags(i).length).length.toLocaleString() },
  ];
  document.getElementById('kpis').innerHTML = items.map(k => `
    <div class="kpi">
      <div class="label">${k.label}</div>
      <div class="value">${k.value}</div>
      <div class="sub ${k.pctClass||''}">${k.sub||''}</div>
    </div>`).join('');
}

/* === Charts === */
let chartStates, chartFha, chartVa, chartAch;
function chartColors() {
  return { accent:'#58a6ff', accent2:'#7ee787', muted:'#8b949e', danger:'#f85149', text:'#e6edf3', bg:'#161b22', grid:'rgba(255,255,255,0.05)' };
}
function makeBar(ctx, labels, data, onClick) {
  const c = chartColors();
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ data, backgroundColor: c.accent, borderRadius: 3 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display:false }, tooltip: { callbacks: { label: (it)=> it.formattedValue+' vendors' } } },
      scales: {
        x: { ticks:{ color: c.muted, font:{size:10} }, grid:{ color: c.grid } },
        y: { ticks:{ color: c.text, font:{size:11} }, grid:{ display:false } },
      },
      onClick: (evt, els) => { if (els.length) onClick(labels[els[0].index]); }
    }
  });
}
function makeDoughnut(ctx, yes, no) {
  const c = chartColors();
  return new Chart(ctx, {
    type: 'doughnut',
    data: { labels: ['Yes','No'], datasets: [{ data: [yes, no], backgroundColor: [c.accent2, '#30363d'], borderColor: c.bg, borderWidth: 2 }] },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { position:'bottom', labels: { color: c.text, font:{size:11}, boxWidth:10, boxHeight:10 } },
        tooltip: { callbacks: { label: (it)=> it.label+': '+it.formattedValue.toLocaleString() } }
      }
    }
  });
}
function renderCharts(a) {
  // Top 15 states bar
  const sortedStates = Object.entries(a.byState).sort((x,y) => y[1]-x[1]).slice(0, 15);
  const stLabels = sortedStates.map(x => x[0]);
  const stData = sortedStates.map(x => x[1]);
  if (chartStates) { chartStates.data.labels = stLabels; chartStates.data.datasets[0].data = stData; chartStates.update(); }
  else chartStates = makeBar(document.getElementById('chart-states'), stLabels, stData, (st) => toggleState(st));

  if (chartFha) { chartFha.data.datasets[0].data = [a.fha.yes, a.fha.no]; chartFha.update(); }
  else chartFha = makeDoughnut(document.getElementById('chart-fha'), a.fha.yes, a.fha.no);

  if (chartVa) { chartVa.data.datasets[0].data = [a.va.yes, a.va.no]; chartVa.update(); }
  else chartVa = makeDoughnut(document.getElementById('chart-va'), a.va.yes, a.va.no);

  if (chartAch) { chartAch.data.datasets[0].data = [a.ach.yes, a.ach.no]; chartAch.update(); }
  else chartAch = makeDoughnut(document.getElementById('chart-ach'), a.ach.yes, a.ach.no);

  // Top counties list
  const sortedCounties = Object.entries(a.byCounty).sort((x,y) => y[1]-x[1]).slice(0, 30);
  document.getElementById('counties-list').innerHTML = sortedCounties.map(([c,n]) =>
    `<div class="row" data-county="${c.replace(/"/g,'&quot;')}"><span>${c}</span><span class="num">${n}</span></div>`).join('') || '<div style="color:#8b949e;padding:8px">No coverage data</div>';
}

/* === Tile map === */
function colorScaleClass(v, max) {
  if (v === 0) return 'scale-0';
  const r = v / Math.max(1, max);
  if (r < 0.05) return 'scale-1';
  if (r < 0.15) return 'scale-2';
  if (r < 0.35) return 'scale-3';
  if (r < 0.65) return 'scale-4';
  return 'scale-5';
}
function renderMap(a) {
  const root = document.getElementById('tile-map');
  const max = Math.max(...Object.values(a.byState), 1);
  const tiles = [];
  // build a 8x12 grid of empties first, then fill
  const grid = {};
  for (const [st, [r, c]] of Object.entries(_TILE_GRID)) grid[r+','+c] = st;
  for (let r=0; r<8; r++) {
    for (let c=0; c<12; c++) {
      const st = grid[r+','+c];
      if (!st) {
        tiles.push(`<div class="tile empty" style="grid-row:${r+1};grid-column:${c+1};"></div>`);
      } else {
        const v = a.byState[st] || 0;
        const cls = colorScaleClass(v, max);
        const sel = state.states.has(st) ? ' selected' : '';
        tiles.push(`<div class="tile ${cls}${sel}" data-st="${st}" title="${_STATE_NAMES[st]||st}: ${v} vendors" style="grid-row:${r+1};grid-column:${c+1};"><span class="abbr">${st}</span><span class="num">${v.toLocaleString()}</span></div>`);
      }
    }
  }
  root.innerHTML = tiles.join('');
}

/* === Table === */
const COLUMNS = [
  { key:'i', label:'ID', w:'70px' },
  { key:'n', label:'Contact' },
  { key:'co', label:'Company' },
  { key:'c', label:'City' },
  { key:'s', label:'State', w:'60px' },
  { key:'z', label:'Zip', w:'70px' },
  { key:'e', label:'Email' },
  { key:'cp', label:'Cell' },
  { key:'fha', label:'FHA', w:'50px', flag:true },
  { key:'va', label:'VA', w:'50px', flag:true },
  { key:'ach', label:'ACH', w:'50px', flag:true },
  { key:'_tags', label:'Tags', w:'120px' },
];
function sortFiltered() {
  const k = state.sortKey, dir = state.sortDir;
  filtered.sort((a, b) => {
    const ra = DATA[a], rb = DATA[b];
    let va = ra[k], vb = rb[k];
    if (k === '_tags') { va = (tagDict[a]||[]).join(','); vb = (tagDict[b]||[]).join(','); }
    if (typeof va === 'boolean') { va = va?1:0; vb = vb?1:0; }
    va = (va == null ? '' : va);
    vb = (vb == null ? '' : vb);
    if (typeof va === 'string') { return dir * va.localeCompare(vb); }
    return dir * (va - vb);
  });
}
function renderTable() {
  const head = COLUMNS.map(c => {
    const sorted = state.sortKey === c.key;
    return `<th data-key="${c.key}" class="${sorted?'sorted':''}" data-arrow="${sorted ? (state.sortDir>0?'▲':'▼'):''}" style="${c.w?'width:'+c.w:''}">${c.label}</th>`;
  }).concat('<th style="width:80px;">Actions</th>').join('');
  document.getElementById('tbl-head').innerHTML = head;

  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page >= pages) state.page = 0;
  const start = state.page * state.pageSize;
  const end = Math.min(start + state.pageSize, total);

  const body = [];
  for (let i = start; i < end; i++) {
    const r = DATA[filtered[i]];
    const tags = (tagDict[r._id] || []);
    body.push(`<tr data-id="${r._id}">
      <td>${r.i}</td>
      <td>${escHtml(r.n)}</td>
      <td>${escHtml(r.co)}</td>
      <td>${escHtml(r.c)}</td>
      <td>${r.s}</td>
      <td>${r.z}</td>
      <td><a href="mailto:${r.e}">${escHtml(r.e)}</a></td>
      <td>${r.cp}</td>
      <td><span class="yn ${r.fha?'yes':'no'}">${r.fha?'Y':'N'}</span></td>
      <td><span class="yn ${r.va?'yes':'no'}">${r.va?'Y':'N'}</span></td>
      <td><span class="yn ${r.ach?'yes':'no'}">${r.ach?'Y':'N'}</span></td>
      <td>${tags.map(t=>`<span class="tag">${escHtml(t)}</span>`).join(' ')}</td>
      <td><div class="row-actions">
        <button data-act="open">View</button>
      </div></td>
    </tr>`);
  }
  document.getElementById('tbl-body').innerHTML = body.join('');
  document.getElementById('page-info').textContent = total === 0 ? 'No results' : `Showing ${start+1}–${end} of ${total.toLocaleString()}`;
  document.getElementById('prev').disabled = state.page === 0;
  document.getElementById('next').disabled = state.page >= pages - 1;
}

/* === Cards === */
function renderCards() {
  const max = Math.min(filtered.length, 500);
  const body = [];
  for (let i = 0; i < max; i++) {
    const r = DATA[filtered[i]];
    const tags = tagDict[r._id] || [];
    body.push(`<div class="card" data-id="${r._id}">
      <div class="name">${escHtml(r.n)}</div>
      <div class="co">${escHtml(r.co)}</div>
      <div class="meta">
        <span>${escHtml(r.c)}, ${r.s} ${r.z}</span>
      </div>
      <div class="meta" style="margin-top:4px;">${escHtml(r.e)}</div>
      <div class="pills">
        ${r.fha ? '<span class="pill">FHA</span>':''}
        ${r.va ? '<span class="pill">VA</span>':''}
        ${r.ach ? '<span class="pill">ACH</span>':''}
        ${(r.cv && r.cv.length) ? `<span class="pill muted">${r.cv.length} counties</span>` : ''}
        ${tags.map(t => `<span class="pill" style="background:rgba(241,196,15,0.15);color:#f1c40f">${escHtml(t)}</span>`).join('')}
      </div>
    </div>`);
  }
  if (filtered.length > 500) body.push(`<div style="grid-column:1/-1;color:#8b949e;padding:6px;font-size:11px;">Showing first 500 of ${filtered.length.toLocaleString()} — narrow filters or use list view to see more</div>`);
  if (filtered.length === 0) body.push(`<div style="grid-column:1/-1;color:#8b949e;padding:14px;">No results match your filters</div>`);
  document.getElementById('cards-grid').innerHTML = body.join('');
}

/* === Groups === */
function renderGroups() {
  const k = state.groupBy;
  const groups = {};
  for (const idx of filtered) {
    const r = DATA[idx];
    let g;
    if (k === 'fha') g = r.fha ? 'FHA Yes' : 'FHA No';
    else if (k === 'va') g = r.va ? 'VA Yes' : 'VA No';
    else if (k === 'ach') g = r.ach ? 'ACH Yes' : 'ACH No';
    else if (k === 'state') g = r.s || '—';
    else if (k === 'city') g = r.c || '—';
    else if (k === 'company') g = r.co || '—';
    if (!groups[g]) groups[g] = [];
    groups[g].push(idx);
  }
  const sorted = Object.entries(groups).sort((a,b) => b[1].length - a[1].length);
  const body = sorted.slice(0, 200).map(([g, ids]) => `
    <div class="group">
      <div class="group-header" data-group="${escHtml(g)}">
        <span class="name">${escHtml(g)}</span>
        <span class="count">${ids.length.toLocaleString()} vendors</span>
      </div>
      <div class="group-body">
        <div class="cards">
          ${ids.slice(0, 24).map(i => {
            const r = DATA[i];
            return `<div class="card" data-id="${i}">
              <div class="name">${escHtml(r.n)}</div>
              <div class="co">${escHtml(r.co)}</div>
              <div class="meta"><span>${escHtml(r.c)}, ${r.s}</span></div>
            </div>`;
          }).join('')}
          ${ids.length > 24 ? `<div style="color:#8b949e;font-size:11px;padding:6px;">+ ${(ids.length-24).toLocaleString()} more</div>` : ''}
        </div>
      </div>
    </div>`).join('');
  document.getElementById('groups-list').innerHTML = body || '<div style="color:#8b949e;padding:14px;">No results</div>';
}

/* === Multi-select dropdown === */
function buildMultiSelect(elId, key, items, getLabel, getCount) {
  const root = document.getElementById(elId);
  const btn = root.querySelector('.ms-btn');
  const panel = root.querySelector('.ms-panel');
  const search = root.querySelector('.ms-search');
  const opts = root.querySelector('.ms-options');
  function renderOpts(filterStr) {
    const f = (filterStr || '').toLowerCase();
    const html = items
      .filter(it => !f || getLabel(it).toLowerCase().includes(f))
      .slice(0, 500)
      .map(it => {
        const lbl = getLabel(it);
        const checked = state[key].has(lbl) ? 'checked' : '';
        return `<label class="ms-option"><input type="checkbox" value="${escHtml(lbl)}" ${checked}><span>${escHtml(lbl)}</span><span class="count-pill">${getCount(it)}</span></label>`;
      }).join('');
    opts.innerHTML = html || `<div style="color:#8b949e;padding:6px;">No matches</div>`;
  }
  btn.addEventListener('click', () => {
    document.querySelectorAll('.ms.open').forEach(m => { if (m !== root) m.classList.remove('open'); });
    root.classList.toggle('open');
    if (root.classList.contains('open')) { search.value = ''; renderOpts(''); search.focus(); }
  });
  search.addEventListener('input', () => renderOpts(search.value));
  opts.addEventListener('change', e => {
    const cb = e.target;
    if (cb.checked) state[key].add(cb.value); else state[key].delete(cb.value);
    onChange();
  });
  root.querySelectorAll('.ms-actions button').forEach(b => {
    b.addEventListener('click', () => {
      if (b.dataset.act === 'clear') { state[key] = new Set(); renderOpts(search.value); onChange(); }
      else if (b.dataset.act === 'close') { root.classList.remove('open'); }
    });
  });
  function refresh() {
    const c = state[key].size;
    btn.firstChild.textContent = c === 0 ? defaultLabel(elId) : `${c} selected `;
    const cnt = btn.querySelector('.count');
    if (c === 0) cnt.classList.add('hidden'); else { cnt.classList.remove('hidden'); cnt.textContent = c; }
  }
  return { refresh, renderOpts };
}
function defaultLabel(elId) {
  if (elId === 'ms-state') return 'All states ';
  if (elId === 'ms-county') return 'Any county ';
  if (elId === 'ms-tag') return 'Any tag ';
  return '';
}

/* === Active filter chips === */
function renderActiveFilters() {
  const chips = [];
  if (state.search) chips.push({ key: 'search', label: 'Search: "'+state.search+'"' });
  for (const s of state.states) chips.push({ key: 'state:'+s, label: s });
  if (state.fha !== 'any') chips.push({ key: 'fha', label: 'FHA: '+state.fha });
  if (state.va !== 'any') chips.push({ key: 'va', label: 'VA: '+state.va });
  if (state.ach !== 'any') chips.push({ key: 'ach', label: 'ACH: '+state.ach });
  for (const c of state.counties) chips.push({ key: 'county:'+c, label: 'County: '+c });
  for (const t of state.tags) chips.push({ key: 'tag:'+t, label: 'Tag: '+t });
  document.getElementById('active-filters').innerHTML = chips.map(ch =>
    `<span class="chip" data-rk="${escHtml(ch.key)}">${escHtml(ch.label)} <span class="x">×</span></span>`).join('');
}

/* === Master onChange === */
let stateMs, countyMs, tagMs;
function onChange() {
  applyFilters();
  const a = agg();
  document.getElementById('result-count').textContent = filtered.length.toLocaleString() + ' / ' + N.toLocaleString();
  renderActiveFilters();
  renderKPIs(a);
  renderCharts(a);
  if (state.view === 'map') renderMap(a);
  // Always sort, then render the active view
  if (state.view === 'table') { sortFiltered(); renderTable(); }
  else if (state.view === 'cards') { sortFiltered(); renderCards(); }
  else if (state.view === 'groups') { sortFiltered(); renderGroups(); }
  if (stateMs) stateMs.refresh();
  if (countyMs) countyMs.refresh();
  if (tagMs) tagMs.refresh();
}

/* === Toggling a state === */
function toggleState(st) {
  if (state.states.has(st)) state.states.delete(st);
  else state.states.add(st);
  onChange();
}

/* === Helpers === */
function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

/* === View switching === */
function switchView(v) {
  state.view = v;
  persistView();
  document.querySelectorAll('#view-toggle button').forEach(b => b.classList.toggle('active', b.dataset.view === v));
  document.getElementById('view-table').classList.toggle('hidden', v !== 'table');
  document.getElementById('view-cards').classList.toggle('hidden', v !== 'cards');
  document.getElementById('view-map').classList.toggle('hidden', v !== 'map');
  document.getElementById('view-groups').classList.toggle('hidden', v !== 'groups');
  document.getElementById('view-title').textContent = ({table:'List view', cards:'Card view', map:'Map view', groups:'Group view'})[v];
  document.getElementById('group-by-wrap').style.display = v === 'groups' ? '' : 'none';
  onChange();
}

/* === Modal === */
function openVendor(id) {
  const r = DATA[id];
  if (!r) return;
  document.getElementById('modal-title').textContent = r.n + ' — ' + (r.co || '');
  const tags = tagDict[id] || [];
  const rows = [
    ['Vendor ID', r.i],
    ['Contact', r.n],
    ['Company', r.co],
    ['Address', `${r.a}<br>${r.c}, ${r.s} ${r.z}`],
    ['Email', r.e ? `<a href="mailto:${r.e}">${escHtml(r.e)}</a>` : ''],
    ['Work', r.wp || ''],
    ['Cell', r.cp || ''],
    ['Coverage', r.cv && r.cv.length ? r.cv.join(', ') : '<i>None listed</i>'],
    ['FHA', r.fha ? '<span class="yn yes">Yes</span>' : '<span class="yn no">No</span>'],
    ['VA', r.va ? '<span class="yn yes">Yes</span>' : '<span class="yn no">No</span>'],
    ['ACH', r.ach ? '<span class="yn yes">Yes</span>' : '<span class="yn no">No</span>'],
  ];
  document.getElementById('modal-body').innerHTML = `
    ${rows.map(([k,v]) => `<div class="row"><div class="k">${k}</div><div class="v">${v||''}</div></div>`).join('')}
    <div class="row"><div class="k">Tags</div><div class="v">
      <div class="tag-list" id="modal-tags">${tags.map(t=>`<span class="tag">${escHtml(t)}<span class="x" data-tag="${escHtml(t)}">×</span></span>`).join('')}</div>
      <div class="tag-input"><input class="input" id="new-tag" placeholder="Add a tag, press Enter"><button class="btn primary" id="add-tag-btn">Add</button></div>
    </div></div>`;
  document.getElementById('modal').classList.add('open');
  // Tag handlers
  document.getElementById('modal-tags').onclick = (e) => {
    if (e.target.classList.contains('x')) {
      const t = e.target.dataset.tag;
      setTags(id, (tagDict[id]||[]).filter(x => x !== t));
      openVendor(id); onChange();
    }
  };
  const addTag = () => {
    const inp = document.getElementById('new-tag');
    const v = inp.value.trim();
    if (!v) return;
    const cur = tagDict[id] || [];
    if (!cur.includes(v)) cur.push(v);
    setTags(id, cur);
    inp.value = '';
    openVendor(id); onChange(); rebuildTagMs();
  };
  document.getElementById('add-tag-btn').onclick = addTag;
  document.getElementById('new-tag').onkeydown = (e) => { if (e.key === 'Enter') addTag(); };
}

function rebuildTagMs() {
  const list = allTagsList();
  // rebuild tag multi-select
  const root = document.getElementById('ms-tag');
  const opts = root.querySelector('.ms-options');
  const search = root.querySelector('.ms-search');
  opts.innerHTML = list.map(it =>
    `<label class="ms-option"><input type="checkbox" value="${escHtml(it.tag)}" ${state.tags.has(it.tag)?'checked':''}><span>${escHtml(it.tag)}</span><span class="count-pill">${it.count}</span></label>`
  ).join('') || '<div style="color:#8b949e;padding:6px;">No tags yet — add some via vendor details</div>';
}

/* === CSV export === */
function exportCSV() {
  const cols = ['Vendor ID','Contact Name','Company Name','Address','City','State','Zip','Work Phone','Cell Phone','Email','Coverage (Counties)','FHA Approved','VA Approved','ACH Available','Tags'];
  const lines = [cols.join(',')];
  const escCSV = s => {
    if (s == null) return '';
    s = String(s);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) return '"' + s.replace(/"/g,'""') + '"';
    return s;
  };
  for (const i of filtered) {
    const r = DATA[i];
    const tags = (tagDict[r._id]||[]).join('; ');
    lines.push([
      r.i, r.n, r.co, r.a, r.c, r.s, r.z, r.wp, r.cp, r.e,
      (r.cv||[]).join(', '),
      r.fha ? 'Yes':'No', r.va?'Yes':'No', r.ach?'Yes':'No', tags
    ].map(escCSV).join(','));
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `vendors_export_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* === Wire up === */
document.getElementById('search').addEventListener('input', e => { state.search = e.target.value; state.page = 0; onChange(); });
document.querySelectorAll('.triseg').forEach(seg => {
  const k = seg.dataset.key;
  seg.addEventListener('click', e => {
    if (!e.target.dataset.v) return;
    seg.querySelectorAll('button').forEach(b => b.classList.remove('active','no'));
    e.target.classList.add('active');
    if (e.target.dataset.v === 'no') e.target.classList.add('no');
    state[k] = e.target.dataset.v;
    onChange();
  });
});
document.getElementById('clear-filters').addEventListener('click', () => {
  state.search = ''; document.getElementById('search').value = '';
  state.states = new Set(); state.counties = new Set(); state.tags = new Set();
  state.fha = 'any'; state.va = 'any'; state.ach = 'any';
  document.querySelectorAll('.triseg').forEach(seg => {
    seg.querySelectorAll('button').forEach(b => b.classList.remove('active','no'));
    seg.querySelector('button[data-v="any"]').classList.add('active');
  });
  onChange();
});
document.getElementById('view-toggle').addEventListener('click', e => {
  if (e.target.dataset.view) switchView(e.target.dataset.view);
});
document.getElementById('export-btn').addEventListener('click', exportCSV);
document.getElementById('group-by').addEventListener('change', e => { state.groupBy = e.target.value; onChange(); });

// Table sorting / pagination
document.getElementById('tbl-head').addEventListener('click', e => {
  const k = e.target.dataset.key;
  if (!k) return;
  if (state.sortKey === k) state.sortDir *= -1; else { state.sortKey = k; state.sortDir = 1; }
  onChange();
});
document.getElementById('tbl-body').addEventListener('click', e => {
  const tr = e.target.closest('tr'); if (!tr) return;
  const id = +tr.dataset.id;
  if (e.target.dataset.act === 'open') openVendor(id);
});
document.getElementById('cards-grid').addEventListener('click', e => {
  const card = e.target.closest('.card'); if (!card) return;
  openVendor(+card.dataset.id);
});
document.getElementById('groups-list').addEventListener('click', e => {
  const head = e.target.closest('.group-header');
  if (head) { head.parentElement.classList.toggle('open'); return; }
  const card = e.target.closest('.card');
  if (card) openVendor(+card.dataset.id);
});
document.getElementById('prev').addEventListener('click', () => { if (state.page > 0) { state.page--; renderTable(); } });
document.getElementById('next').addEventListener('click', () => { state.page++; renderTable(); });
document.getElementById('page-size').addEventListener('change', e => { state.pageSize = +e.target.value; state.page = 0; persistView(); renderTable(); });
document.getElementById('page-size').value = String(state.pageSize);

// Tile map clicks
document.getElementById('tile-map').addEventListener('click', e => {
  const t = e.target.closest('.tile'); if (!t || t.classList.contains('empty')) return;
  toggleState(t.dataset.st);
});
// Counties list clicks
document.getElementById('counties-list').addEventListener('click', e => {
  const row = e.target.closest('.row'); if (!row) return;
  const c = row.dataset.county;
  if (state.counties.has(c)) state.counties.delete(c); else state.counties.add(c);
  onChange();
});
// Active-filter chip removal
document.getElementById('active-filters').addEventListener('click', e => {
  if (!e.target.classList.contains('x')) return;
  const rk = e.target.parentElement.dataset.rk;
  if (rk === 'search') { state.search=''; document.getElementById('search').value=''; }
  else if (rk.startsWith('state:')) state.states.delete(rk.slice(6));
  else if (rk.startsWith('county:')) state.counties.delete(rk.slice(7));
  else if (rk.startsWith('tag:')) state.tags.delete(rk.slice(4));
  else if (rk === 'fha') { state.fha='any'; refreshTriseg('fha'); }
  else if (rk === 'va') { state.va='any'; refreshTriseg('va'); }
  else if (rk === 'ach') { state.ach='any'; refreshTriseg('ach'); }
  onChange();
});
function refreshTriseg(k) {
  const seg = document.querySelector(`.triseg[data-key="${k}"]`);
  seg.querySelectorAll('button').forEach(b => b.classList.remove('active','no'));
  seg.querySelector('button[data-v="any"]').classList.add('active');
}
// Modal close
document.getElementById('modal-close').addEventListener('click', () => document.getElementById('modal').classList.remove('open'));
document.getElementById('modal').addEventListener('click', e => { if (e.target.id === 'modal') document.getElementById('modal').classList.remove('open'); });
// Close MS panels on outside click
document.addEventListener('click', e => {
  if (!e.target.closest('.ms')) document.querySelectorAll('.ms.open').forEach(m => m.classList.remove('open'));
});

/* Build multi-selects */
const stateItems = allStates.map(s => ({ s, count: stateCounts[s] }));
stateMs = buildMultiSelect('ms-state', 'states', stateItems, it => it.s, it => it.count);
const countyItems = allCounties.map(c => ({ c, count: countyCounts[c] })).sort((a,b) => b.count - a.count);
countyMs = buildMultiSelect('ms-county', 'counties', countyItems, it => it.c, it => it.count);
tagMs = (function() {
  const root = document.getElementById('ms-tag');
  const btn = root.querySelector('.ms-btn');
  function refresh() {
    rebuildTagMs();
    const c = state.tags.size;
    btn.firstChild.textContent = c === 0 ? defaultLabel('ms-tag') : `${c} selected `;
    const cnt = btn.querySelector('.count');
    if (c === 0) cnt.classList.add('hidden'); else { cnt.classList.remove('hidden'); cnt.textContent = c; }
  }
  btn.addEventListener('click', () => {
    document.querySelectorAll('.ms.open').forEach(m => { if (m !== root) m.classList.remove('open'); });
    root.classList.toggle('open');
    if (root.classList.contains('open')) refresh();
  });
  root.querySelector('.ms-options').addEventListener('change', e => {
    const cb = e.target;
    if (cb.checked) state.tags.add(cb.value); else state.tags.delete(cb.value);
    onChange();
  });
  root.querySelector('.ms-search').addEventListener('input', () => refresh());
  root.querySelectorAll('.ms-actions button').forEach(b => {
    b.addEventListener('click', () => {
      if (b.dataset.act === 'clear') { state.tags = new Set(); refresh(); onChange(); }
      else if (b.dataset.act === 'close') root.classList.remove('open');
    });
  });
  return { refresh };
})();

/* Init */
filtered = DATA.map((_, i) => i);
sortFiltered();
switchView(state.view);
document.getElementById('loader').classList.add('hidden');
document.getElementById('app').classList.remove('hidden');
})();
</script>
</body>
</html>
"""

html = (HTML
        .replace("__DATA_B64__", b64)
        .replace("__TILE_GRID__", json.dumps(TILE_GRID))
        .replace("__STATE_NAMES__", json.dumps(STATE_NAMES)))

out_path = os.path.join(OUT, "vendor_explorer.html")
with open(out_path, "w") as f:
    f.write(html)
print("wrote:", out_path, "size:", os.path.getsize(out_path))
