import json
import sys
import argparse

def generate_html(data: dict) -> str:
    nodes_json = json.dumps(data["nodes"])
    edges_json = json.dumps(data["edges"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Behavior Lattice</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #0f0f10;
    --surface: #18181b;
    --border: rgba(255,255,255,0.07);
    --text-primary: rgba(255,255,255,0.92);
    --text-secondary: rgba(255,255,255,0.8);
    --text-dim: rgba(255,255,255,0.8);
    --node: rgba(255,255,255,0.78);
    --node-sel: #ffffff;
    --node-nb: rgba(255,255,255,0.92);
    --edge: rgba(255,255,255,0.065);
    --edge-sel: rgba(255,255,255,0.5);
    --glow: rgba(255,255,255,0.1);
    --glow-sel: rgba(255,255,255,0.16);
    --accent: #7F77DD;
    --accent-soft: rgba(127,119,221,0.15);
    --mono: 'JetBrains Mono', monospace;
    --sans: 'Inter', system-ui, sans-serif;
  }}

  html, body {{
    background: var(--bg);
    color: var(--text-primary);
    font-family: var(--sans);
    height: 100%;
    min-height: 100vh;
  }}

  #app {{
    display: grid;
    grid-template-columns: 1fr 340px;
    grid-template-rows: auto 1fr;
    height: 100vh;
    overflow: hidden;
  }}

  header {{
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
  }}

  header h1 {{
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 400;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
    text-transform: uppercase;
  }}

  .layer-badges {{
    display: flex;
    gap: 8px;
    margin-left: auto;
  }}

  .badge {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.06em;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid;
    text-transform: uppercase;
  }}

  .badge-obs {{ color: #7F77DD; border-color: rgba(127,119,221,0.3); background: rgba(127,119,221,0.08); }}
  .badge-l1  {{ color: #D85A30; border-color: rgba(216,90,48,0.3);  background: rgba(216,90,48,0.08); }}
  .badge-l2  {{ color: #1D9E75; border-color: rgba(29,158,117,0.3); background: rgba(29,158,117,0.08); }}

  #canvas-wrap {{
    position: relative;
    overflow: hidden;
    background: var(--bg);
  }}

  canvas {{
    display: block;
    width: 100%;
    height: 100%;
  }}

  #hint {{
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
    pointer-events: none;
    transition: opacity 0.4s;
  }}

  #panel {{
    background: var(--surface);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  #panel-header {{
    padding: 20px 20px 14px;
    border-bottom: 1px solid var(--border);
  }}

  #panel-layer {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 6px;
  }}

  #panel-title {{
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    color: var(--text-primary);
    margin-bottom: 6px;
  }}

  #panel-tagline {{
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-secondary);
    font-style: italic;
  }}

  #panel-body {{
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }}

  #panel-body::-webkit-scrollbar {{ width: 4px; }}
  #panel-body::-webkit-scrollbar-track {{ background: transparent; }}
  #panel-body::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

  .panel-empty {{
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.06em;
    text-align: center;
  }}

  .panel-empty svg {{
    opacity: 0.2;
    margin-bottom: 8px;
  }}

  .section-label {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 8px;
    margin-top: 16px;
  }}

  .section-label:first-child {{ margin-top: 0; }}

  .insight-text {{
    font-size: 13px;
    line-height: 1.65;
    color: var(--text-secondary);
  }}

  .observation-text {{
    font-size: 12px;
    line-height: 1.6;
    color: rgba(255,255,255,0.5);
  }}

  .evidence-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
    color: rgba(255,255,255,0.7);
  }}

  .evidence-list li {{
    font-size: 11px;
    line-height: 1.55;
    color: rgba(255,255,255,0.7);
    padding-left: 12px;
    position: relative;
  }}

  .evidence-list li::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 7px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--text-dim);
  }}

  .conn-stat {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    padding: 10px 0 0;
    border-top: 1px solid var(--border);
    margin-top: 14px;
  }}

  .conn-stat span {{
    color: var(--text-secondary);
  }}

  #level-toggle {{
    display: flex;
    gap: 6px;
    padding: 16px 20px;
    border-top: 1px solid var(--border);
    margin-top: auto;
  }}

  .toggle-btn {{
    flex: 1;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 7px 0;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-dim);
    cursor: pointer;
    transition: all 0.15s;
  }}

  .toggle-btn:hover {{
    border-color: rgba(255,255,255,0.2);
    color: var(--text-secondary);
  }}

  .toggle-btn.active {{
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.18);
    color: var(--text-primary);
  }}

  @media (max-width: 700px) {{
    #app {{ grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; }}
    #panel {{ max-height: 260px; border-left: none; border-top: 1px solid var(--border); }}
  }}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
<div id="app">
  <header>
    <h1>Behavior Lattice</h1>
  </header>

  <div id="canvas-wrap">
    <canvas id="lc"></canvas>
    <div id="hint">click any node to explore</div>
  </div>

  <div id="panel">
    <div id="panel-header" style="display:none">
      <div id="panel-layer"></div>
      <div id="panel-title"></div>
      <div id="panel-tagline"></div>
    </div>
    <div id="panel-body">
      <div class="panel-empty">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="8" r="4" stroke="white" stroke-width="1.5"/>
          <circle cx="8" cy="24" r="4" stroke="white" stroke-width="1.5"/>
          <circle cx="24" cy="24" r="4" stroke="white" stroke-width="1.5"/>
          <line x1="16" y1="12" x2="8" y2="20" stroke="white" stroke-width="1"/>
          <line x1="16" y1="12" x2="24" y2="20" stroke="white" stroke-width="1"/>
        </svg>
        Select a node<br>to view details
      </div>
    </div>
  </div>
</div>

<script>
const RAW = {{
  nodes: {nodes_json},
  edges: {edges_json}
}};

// ── Parse into display layers ──────────────────────────────────────────────
// nodes[0] = observations (array of obs objects)
// nodes[1] = layer-1 insights
// nodes[2] = layer-2 insights
// edges[1] = layer1-node → obs-nodes
// edges[2] = layer2-node → layer1-nodes

const obsData   = RAW.nodes[0] || [];
const l1Data    = RAW.nodes[1] || [];
const l2Data    = RAW.nodes[2] || [];
const edges1    = RAW.edges[1] || [];   // layer-1-insight → observation
const edges2    = RAW.edges[2] || [];   // layer-2-insight → layer-1-insight

// ── Canvas setup ───────────────────────────────────────────────────────────
const canvas  = document.getElementById('lc');
const ctx     = canvas.getContext('2d');
const wrap    = document.getElementById('canvas-wrap');

let W, H, DPR;
let nodes = [], edges = [], selected = null, hovered = null;
let activeLevel = 0; // 0 = obs, 1 = l1, 2 = l2

function buildGraph() {{
  DPR = window.devicePixelRatio || 1;
  W = wrap.offsetWidth;
  H = wrap.offsetHeight;
  canvas.width  = W * DPR;
  canvas.height = H * DPR;
  ctx.scale(DPR, DPR);

  nodes = [];
  edges = [];

  const PAD = 48;
  const yObs = H - 44;
  const yL1  = H * 0.5;
  const yL2  = 44;

  function makeRow(items, y, layer, rBase) {{
    const n = items.length;
    return items.map((item, i) => {{
      const x = n === 1 ? W / 2 : PAD + (i / (n - 1)) * (W - 2 * PAD);
      const node = {{ id: nodes.length, x, y, layer, r: rBase, data: item }};
      nodes.push(node);
      return node;
    }});
  }}

  const obsNodes = makeRow(obsData, yObs, 'obs', 4.5);
  const l1Nodes  = makeRow(l1Data,  yL1,  'l1',  6.5);
  const l2Nodes  = makeRow(l2Data,  yL2,  'l2',  8);

  // edges[1]: source = l1 index, target = obs index
  edges1.forEach(e => {{
    const src = l1Nodes[e.source];
    const tgt = obsNodes[e.target];
    if (src && tgt) edges.push({{ a: src.id, b: tgt.id, layer: 'l1' }});
  }});

  // edges[2]: source = l2 index, target = l1 index
  edges2.forEach(e => {{
    const src = l2Nodes[e.source];
    const tgt = l1Nodes[e.target];
    if (src && tgt) edges.push({{ a: src.id, b: tgt.id, layer: 'l2' }});
  }});

  selected = null;
  hovered  = null;
  draw();
}}

function neighbors(id) {{
  const s = new Set();
  edges.forEach(e => {{
    if (e.a === id) s.add(e.b);
    if (e.b === id) s.add(e.a);
  }});
  return s;
}}

// Get all nodes reachable within N hops (for multi-layer highlight)
function reachable(id, hops) {{
  let frontier = new Set([id]);
  let all = new Set([id]);
  for (let h = 0; h < hops; h++) {{
    const next = new Set();
    frontier.forEach(nid => neighbors(nid).forEach(nb => {{ if (!all.has(nb)) next.add(nb); }}));
    next.forEach(n => all.add(n));
    frontier = next;
  }}
  return all;
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);

  const nb = selected !== null ? reachable(selected, 2) : null;

  // Layer guide lines
  const layerY = {{
    obs: nodes.find(n => n.layer === 'obs')?.y,
    l1:  nodes.find(n => n.layer === 'l1')?.y,
    l2:  nodes.find(n => n.layer === 'l2')?.y,
  }};

  Object.values(layerY).forEach(y => {{
    if (!y) return;
    ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(W - 40, y);
    ctx.strokeStyle = 'rgba(255,255,255,0.04)'; ctx.lineWidth = 1; ctx.stroke();
  }});



  // Edges
  edges.forEach(e => {{
    const a = nodes[e.a], b = nodes[e.b];
    const active = nb && (nb.has(e.a) && nb.has(e.b));
    const dimmed  = nb && !active;
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = active ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.4)';
    ctx.lineWidth   = active ? 1 : 0.6;
    ctx.globalAlpha = dimmed ? 0.1 : 1;
    ctx.stroke();
    ctx.globalAlpha = 1;
  }});

  // Nodes
  nodes.forEach(n => {{
    const isSel  = n.id === selected;
    const isNb   = nb?.has(n.id);
    const isHov  = n.id === hovered;
    const dimmed = nb && !isSel && !isNb;

    ctx.globalAlpha = dimmed ? 0.12 : 1;

    if (isSel || isNb || isHov) {{
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r + (isSel ? 9 : isNb ? 5 : 3), 0, Math.PI * 2);
      ctx.fillStyle = isSel ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.07)';
      ctx.fill();
    }}

    ctx.beginPath();
    ctx.arc(n.x, n.y, isSel ? n.r + 1.5 : isHov ? n.r + 0.8 : n.r, 0, Math.PI * 2);
    ctx.fillStyle = isSel ? '#ffffff' : isNb ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.72)';
    ctx.fill();
    ctx.globalAlpha = 1;
  }});
}}

// ── Hit test ───────────────────────────────────────────────────────────────
function hitTest(mx, my) {{
  let best = null, bestD = 20;
  nodes.forEach(n => {{
    const d = Math.hypot(n.x - mx, n.y - my);
    if (d < bestD) {{ bestD = d; best = n; }}
  }});
  return best;
}}

// ── Panel rendering ────────────────────────────────────────────────────────
function layerLabel(layer) {{
  return {{ obs: 'Observation', l1: 'Layer 1 insight', l2: 'Layer 2 insight' }}[layer] || layer;
}}

function renderPanel(node) {{
  const header = document.getElementById('panel-header');
  const body   = document.getElementById('panel-body');
  const hint   = document.getElementById('hint');

  if (!node) {{
    header.style.display = 'none';
    hint.style.opacity = '1';
    body.innerHTML = `<div class="panel-empty">
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="8" r="4" stroke="white" stroke-width="1.5"/>
        <circle cx="8" cy="24" r="4" stroke="white" stroke-width="1.5"/>
        <circle cx="24" cy="24" r="4" stroke="white" stroke-width="1.5"/>
        <line x1="16" y1="12" x2="8" y2="20" stroke="white" stroke-width="1"/>
        <line x1="16" y1="12" x2="24" y2="20" stroke="white" stroke-width="1"/>
      </svg>
      Select a node<br>to view details
    </div>`;
    return;
  }}

  hint.style.opacity = '0';
  header.style.display = 'block';

  const d = node.data;
  document.getElementById('panel-layer').textContent = layerLabel(node.layer);

  const nb = neighbors(node.id);

  if (node.layer === 'obs') {{
    document.getElementById('panel-title').textContent = '';
    document.getElementById('panel-tagline').textContent = '';
    const conf = d.confidence !== undefined ? d.confidence : '—';
    const session = d.metadata?.input_session !== undefined ? d.metadata.input_session : '—';
    body.innerHTML = `
      <div class="section-label">Observation</div>
      <p class="observation-text">${{escHtml(d.observation || '')}}</p>
      <div class="conn-stat">
        <span>${{nb.size}}</span> connection${{nb.size !== 1 ? 's' : ''}} &nbsp;·&nbsp; session <span>${{session}}</span>
      </div>`;
  }} else if (node.layer === 'l1') {{
    document.getElementById('panel-title').textContent = d.title || '';
    document.getElementById('panel-tagline').textContent = d.tagline || '';
    const evidenceItems = (d.supporting_evidence || []).map(ev =>
      `<li>${{escHtml(ev)}}</li>`).join('');
    body.innerHTML = `
      <div class="section-label">Insight</div>
      <p class="insight-text">${{escHtml(d.insight || '')}}</p>
      ${{evidenceItems ? `<div class="section-label">Evidence</div><ul class="evidence-list">${{evidenceItems}}</ul>` : ''}}
      <div class="conn-stat">
        <span>${{nb.size}}</span> connection${{nb.size !== 1 ? 's' : ''}}
      </div>`;
  }} else {{
    document.getElementById('panel-title').textContent = d.title || '';
    document.getElementById('panel-tagline').textContent = d.tagline || '';
    const evidenceText = typeof d.supporting_evidence === 'string'
      ? d.supporting_evidence
      : (d.supporting_evidence || []).join(' ');
    body.innerHTML = `
      <div class="section-label">Synthesis</div>
      <p class="insight-text">${{escHtml(d.insight || '')}}</p>
      ${{evidenceText ? `<div class="section-label">Evidence</div><p class="observation-text">${{escHtml(evidenceText)}}</p>` : ''}}
      <div class="conn-stat">
        <span>${{nb.size}}</span> connection${{nb.size !== 1 ? 's' : ''}}
      </div>`;
  }}
}}

function escHtml(str) {{
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}}

// ── Level toggle ───────────────────────────────────────────────────────────
document.querySelectorAll('.toggle-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeLevel = +btn.dataset.level;

    const layerMap = [['obs'], ['l1'], ['l2']];
    const targetLayers = layerMap[activeLevel];

    // Find a node in that layer to select as example, or just highlight
    const firstInLayer = nodes.find(n => targetLayers.includes(n.layer));
    if (firstInLayer) {{
      selected = null;
      hovered  = null;
      draw();
      renderPanel(null);
    }}
  }});
}});

// ── Events ─────────────────────────────────────────────────────────────────
canvas.addEventListener('mousemove', e => {{
  const r  = canvas.getBoundingClientRect();
  const mx = (e.clientX - r.left);
  const my = (e.clientY - r.top);
  const n  = hitTest(mx, my);
  hovered  = n?.id ?? null;
  canvas.style.cursor = n ? 'pointer' : 'default';
  draw();
}});

canvas.addEventListener('click', e => {{
  const r  = canvas.getBoundingClientRect();
  const mx = (e.clientX - r.left);
  const my = (e.clientY - r.top);
  const n  = hitTest(mx, my);
  selected = n && n.id !== selected ? n.id : null;
  renderPanel(selected !== null ? nodes[selected] : null);
  draw();
}});

canvas.addEventListener('mouseleave', () => {{ hovered = null; draw(); }});

window.addEventListener('resize', () => {{ buildGraph(); renderPanel(null); }});

buildGraph();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate an interactive behavior lattice HTML file from a JSON input."
    )
    parser.add_argument("input", help="Path to the JSON file")
    parser.add_argument(
        "-o", "--output", default="lattice.html", help="Output HTML file path (default: lattice.html)"
    )
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    html = generate_html(data)

    with open(args.output, "w") as f:
        f.write(html)

    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()