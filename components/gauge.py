"""
Custom SVG half-circle speedometer gauge.
Uses separate arc segments per colour zone — no dasharray.
sweep=1 (clockwise in SVG Y-down) → arc goes through the TOP. ✓
"""
import streamlit.components.v1 as components
import math


def _pt(frac, cx, cy, R):
    """SVG coords of point at fraction `frac` along upper half-circle.
    frac=0 → left (35, cy), frac=0.5 → top (cx, cy-R), frac=1 → right (245, cy)
    """
    a = math.pi * (1.0 - max(0.0, min(frac, 1.0)))
    return cx + R * math.cos(a), cy - R * math.sin(a)


def _arc(x1, y1, x2, y2, R, color, sw, opacity=0.92):
    """SVG arc segment from (x1,y1) to (x2,y2).
    sweep=1 → clockwise in SVG → goes upward. large-arc=0 (segments < 180°).
    """
    if abs(x2 - x1) < 0.5 and abs(y2 - y1) < 0.5:
        return ""   # skip zero-length segments
    return (
        f'<path d="M {x1:.2f},{y1:.2f} A {R},{R} 0 0,1 {x2:.2f},{y2:.2f}" '
        f'fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="butt" opacity="{opacity}"/>'
    )


def render_co2e_gauge(value: float, max_val: float = 10.0, label: str = "kg CO₂e"):
    pct   = min(max(value / max_val, 0.0), 1.0)
    W, H  = 280, 165
    cx, cy = 140, 150
    R, sw  = 105, 18

    # Zone boundary fractions (clamped to [0,1])
    g_frac = min(2.0 / max_val, 1.0)
    a_frac = min(5.0 / max_val, 1.0)

    # Key arc points
    s  = _pt(0.0,    cx, cy, R)   # left  (value = 0)
    ge = _pt(g_frac, cx, cy, R)   # green → amber
    ae = _pt(a_frac, cx, cy, R)   # amber → red
    e  = _pt(1.0,    cx, cy, R)   # right (value = max)

    # Needle
    nr  = R - 8
    tip = _pt(pct, cx, cy, nr)

    # Colour
    col = "#22c55e" if value < 2 else "#f59e0b" if value < 5 else "#ef4444"

    # Top-centre label position
    top_lbl = _pt(0.5, cx, cy, R + 16)

    html = f"""
<div style="display:flex;justify-content:center;margin:0;padding:0">
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     style="font-family:Inter,sans-serif;overflow:visible">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Outer shadow track -->
  <path d="M {s[0]:.1f},{s[1]:.1f} A {R},{R} 0 0,1 {e[0]:.1f},{e[1]:.1f}"
        fill="none" stroke="#050510" stroke-width="{sw+8}" stroke-linecap="butt"/>

  <!-- Dark base track -->
  <path d="M {s[0]:.1f},{s[1]:.1f} A {R},{R} 0 0,1 {e[0]:.1f},{e[1]:.1f}"
        fill="none" stroke="#1e1b4b" stroke-width="{sw}" stroke-linecap="butt"/>

  <!-- Green zone (0 → 2 kg) -->
  {_arc(*s,  *ge, R, "#16a34a", sw)}

  <!-- Amber zone (2 → 5 kg) -->
  {_arc(*ge, *ae, R, "#d97706", sw)}

  <!-- Red zone (5 → max) -->
  {_arc(*ae, *e,  R, "#dc2626", sw)}

  <!-- Zone boundary ticks (inner–outer radii) -->
  <line x1="{_pt(g_frac, cx, cy, R-sw//2-2)[0]:.1f}"
        y1="{_pt(g_frac, cx, cy, R-sw//2-2)[1]:.1f}"
        x2="{_pt(g_frac, cx, cy, R+sw//2+2)[0]:.1f}"
        y2="{_pt(g_frac, cx, cy, R+sw//2+2)[1]:.1f}"
        stroke="#050510" stroke-width="2.5"/>
  <line x1="{_pt(a_frac, cx, cy, R-sw//2-2)[0]:.1f}"
        y1="{_pt(a_frac, cx, cy, R-sw//2-2)[1]:.1f}"
        x2="{_pt(a_frac, cx, cy, R+sw//2+2)[0]:.1f}"
        y2="{_pt(a_frac, cx, cy, R+sw//2+2)[1]:.1f}"
        stroke="#050510" stroke-width="2.5"/>

  <!-- Scale labels -->
  <text x="{s[0]-4:.0f}"      y="{s[1]+18:.0f}"   text-anchor="end"
        font-size="11" fill="#6b7280" font-weight="500">0</text>
  <text x="{top_lbl[0]:.0f}" y="{top_lbl[1]:.0f}" text-anchor="middle"
        font-size="11" fill="#6b7280" font-weight="500">{max_val/2:.0f}</text>
  <text x="{e[0]+4:.0f}"      y="{e[1]+18:.0f}"   text-anchor="start"
        font-size="11" fill="#6b7280" font-weight="500">{max_val:.0f}</text>

  <!-- Needle shadow -->
  <line x1="{cx}" y1="{cy}" x2="{tip[0]:.2f}" y2="{tip[1]:.2f}"
        stroke="#000" stroke-width="7" stroke-linecap="round" opacity="0.3"/>

  <!-- Needle -->
  <line x1="{cx}" y1="{cy}" x2="{tip[0]:.2f}" y2="{tip[1]:.2f}"
        stroke="{col}" stroke-width="4" stroke-linecap="round"
        filter="url(#glow)"/>

  <!-- Hub -->
  <circle cx="{cx}" cy="{cy}" r="10" fill="{col}"/>
  <circle cx="{cx}" cy="{cy}" r="5"  fill="#0d0d1f"/>

  <!-- Value text -->
  <text x="{cx}" y="{cy-24}" text-anchor="middle"
        font-size="30" font-weight="700" fill="{col}">{value:.1f}</text>
  <text x="{cx}" y="{cy-7}"  text-anchor="middle"
        font-size="11" fill="#9ca3af">{label}</text>

</svg>
</div>
"""
    components.html(html, height=H + 10)
