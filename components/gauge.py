"""
Custom circular SVG gauge rendered via streamlit.components.v1.html
This is a custom component — goes beyond built-in Streamlit widgets.
"""
import streamlit.components.v1 as components
import math

def render_co2e_gauge(value: float, max_val: float = 10.0, label: str = "kg CO₂e"):
    """Render a half-circle SVG gauge for a CO₂e value."""
    pct = min(value / max_val, 1.0)
    R   = 80
    cx, cy = 110, 110

    # Arc from 180° to 0° (half circle, left to right)
    start_angle = math.pi          # 180 deg
    end_angle   = math.pi * (1 - pct)  # sweeping clockwise

    x1 = cx + R * math.cos(start_angle)
    y1 = cy + R * math.sin(start_angle)
    x2 = cx + R * math.cos(end_angle)
    y2 = cy + R * math.sin(end_angle)
    large_arc = 1 if pct > 0.5 else 0

    color = "#22c55e" if value < 2 else "#f59e0b" if value < 5 else "#ef4444"

    html = f"""
    <svg width="220" height="140" viewBox="0 0 220 140"
         style="font-family:Inter,sans-serif">
      <!-- Background track -->
      <path d="M {cx-R},{cy} A {R},{R} 0 0,1 {cx+R},{cy}"
            fill="none" stroke="#2d2d4e" stroke-width="18" stroke-linecap="round"/>
      <!-- Value arc -->
      <path d="M {x1:.2f},{y1:.2f} A {R},{R} 0 {large_arc},0 {x2:.2f},{y2:.2f}"
            fill="none" stroke="{color}" stroke-width="18"
            stroke-linecap="round"/>
      <!-- Center text -->
      <text x="{cx}" y="{cy+10}" text-anchor="middle"
            font-size="22" font-weight="700" fill="{color}">{value:.1f}</text>
      <text x="{cx}" y="{cy+28}" text-anchor="middle"
            font-size="11" fill="#9ca3af">{label}</text>
      <!-- Scale labels -->
      <text x="{cx-R-4}" y="{cy+14}" text-anchor="end"
            font-size="10" fill="#6b7280">0</text>
      <text x="{cx+R+4}" y="{cy+14}" text-anchor="start"
            font-size="10" fill="#6b7280">{max_val}</text>
    </svg>
    """
    components.html(html, height=145)
