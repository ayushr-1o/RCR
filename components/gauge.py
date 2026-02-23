"""
Custom SVG half-circle gauge via streamlit.components.v1.html
Zones: Green (0-2kg), Amber (2-5kg), Red (5kg+)
"""
import streamlit.components.v1 as components
import math

def render_co2e_gauge(value: float, max_val: float = 10.0, label: str = "kg CO₂e"):
    pct     = min(max(value / max_val, 0.0), 1.0)
    W, H    = 280, 168
    cx, cy  = 140, 152   # pivot point (bottom centre)
    R       = 102        # arc radius
    sw      = 20         # track stroke width
    arc_len = math.pi * R  # half-circle path length ≈ 320

    # Zone boundaries along the arc path (in pixels from start)
    green_end = (2.0 / max_val) * arc_len
    amber_end = (5.0 / max_val) * arc_len
    a_len     = max(0.0, amber_end - green_end)
    r_len     = max(0.0, arc_len   - amber_end)

    # SVG half-circle path: LEFT (value=0) → TOP → RIGHT (value=max)
    # sweep=0 = counter-clockwise in SVG = arc goes UPWARD ✓
    left_x, right_x = cx - R, cx + R
    track = f"M {left_x},{cy} A {R},{R} 0 0,0 {right_x},{cy}"

    # Needle tip
    angle = math.pi * (1.0 - pct)        # π at left (0), 0 at right (max)
    ndl_r = R - sw // 2 - 4
    tip_x = cx + ndl_r * math.cos(angle)
    tip_y = cy - ndl_r * math.sin(angle) # minus: SVG y-axis goes downward

    # Dynamic colour
    color = "#22c55e" if value < 2 else "#f59e0b" if value < 5 else "#ef4444"

    # Zone divider helper
    def divider(frac):
        a = math.pi * (1.0 - frac)
        i, o = R - sw // 2 - 1, R + sw // 2 + 1
        return (cx + i*math.cos(a), cy - i*math.sin(a),
                cx + o*math.cos(a), cy - o*math.sin(a))

    ga = divider(2.0 / max_val)
    ar = divider(5.0 / max_val)

    # Zone micro-label positions
    def zlabel(frac_mid, lr):
        a = math.pi * (1.0 - frac_mid)
        return cx + lr*math.cos(a), cy - lr*math.sin(a)

    gl = zlabel(1.0 / max_val,                    R - sw//2 - 11)
    al = zlabel(3.5 / max_val,                    R - sw//2 - 11)
    rl = zlabel((5 + (max_val - 5)/2) / max_val,  R - sw//2 - 11)

    html = f"""
    <div style="display:flex;justify-content:center;padding:4px 0">
    <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
         style="font-family:'Inter',sans-serif;overflow:visible">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2.5" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      <!-- Track background -->
      <path d="{track}" fill="none" stroke="#0d0d1f"
            stroke-width="{sw + 6}" stroke-linecap="butt"/>

      <!-- Green zone 0→2 kg -->
      <path d="{track}" fill="none" stroke="#16a34a" opacity="0.9"
            stroke-width="{sw}"
            stroke-dasharray="{green_end:.1f} {arc_len:.1f}"
            stroke-linecap="butt"/>

      <!-- Amber zone 2→5 kg -->
      <path d="{track}" fill="none" stroke="#d97706" opacity="0.9"
            stroke-width="{sw}"
            stroke-dasharray="0 {green_end:.1f} {a_len:.1f} {arc_len:.1f}"
            stroke-linecap="butt"/>

      <!-- Red zone 5→max kg -->
      <path d="{track}" fill="none" stroke="#dc2626" opacity="0.9"
            stroke-width="{sw}"
            stroke-dasharray="0 {amber_end:.1f} {r_len:.1f} {arc_len:.1f}"
            stroke-linecap="butt"/>

      <!-- Zone dividers -->
      <line x1="{ga[0]:.1f}" y1="{ga[1]:.1f}" x2="{ga[2]:.1f}" y2="{ga[3]:.1f}"
            stroke="#08080f" stroke-width="2.5"/>
      <line x1="{ar[0]:.1f}" y1="{ar[1]:.1f}" x2="{ar[2]:.1f}" y2="{ar[3]:.1f}"
            stroke="#08080f" stroke-width="2.5"/>

      <!-- Zone labels -->
      <text x="{gl[0]:.1f}" y="{gl[1]:.1f}" text-anchor="middle"
            font-size="8" fill="#16a34a" opacity="0.8">Low</text>
      <text x="{al[0]:.1f}" y="{al[1]:.1f}" text-anchor="middle"
            font-size="8" fill="#d97706" opacity="0.8">Med</text>
      <text x="{rl[0]:.1f}" y="{rl[1]:.1f}" text-anchor="middle"
            font-size="8" fill="#dc2626" opacity="0.8">High</text>

      <!-- Scale numbers -->
      <text x="{left_x - 2}"   y="{cy + 16}" text-anchor="middle"
            font-size="10" fill="#4b5563">0</text>
      <text x="{cx}"           y="{cy - R - 10}" text-anchor="middle"
            font-size="10" fill="#4b5563">{int(max_val // 2)}</text>
      <text x="{right_x + 2}"  y="{cy + 16}" text-anchor="middle"
            font-size="10" fill="#4b5563">{int(max_val)}</text>

      <!-- Needle shadow -->
      <line x1="{cx}" y1="{cy}" x2="{tip_x:.1f}" y2="{tip_y:.1f}"
            stroke="#000" stroke-width="6" stroke-linecap="round" opacity="0.2"/>
      <!-- Needle -->
      <line x1="{cx}" y1="{cy}" x2="{tip_x:.1f}" y2="{tip_y:.1f}"
            stroke="{color}" stroke-width="3.5" stroke-linecap="round"
            filter="url(#glow)"/>

      <!-- Hub -->
      <circle cx="{cx}" cy="{cy}" r="9" fill="{color}"/>
      <circle cx="{cx}" cy="{cy}" r="4" fill="#08080f"/>

      <!-- Value -->
      <text x="{cx}" y="{cy - 22}" text-anchor="middle"
            font-size="30" font-weight="700" fill="{color}">{value:.1f}</text>
      <text x="{cx}" y="{cy - 5}"  text-anchor="middle"
            font-size="11" fill="#9ca3af">{label}</text>
    </svg>
    </div>
    """
    components.html(html, height=H + 10)
