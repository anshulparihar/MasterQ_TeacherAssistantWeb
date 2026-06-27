"""
Diagram Primitives Library for MasterQ Question Paper Generator.

Each function takes a `params: dict` and returns PNG `bytes`.
The LLM selects a primitive name + fills parameters.
All geometry is computed with exact trigonometry — not estimated.
"""

import io
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.transforms as mtransforms
import structlog

logger = structlog.get_logger(__name__)

# ── Styling Constants ────────────────────────────────────────
COLOR_PRIMARY   = '#1565C0'
COLOR_ACCENT    = '#C62828'
COLOR_GREEN     = '#2E7D32'
COLOR_FILL      = '#E3F2FD'
COLOR_FILL_ALT  = '#FFF3E0'
COLOR_GRID      = '#E0E0E0'
LABEL_BBOX      = dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.92)
FONT_MATH       = {'fontfamily': 'serif', 'fontsize': 11}
FONT_TITLE      = {'fontfamily': 'sans-serif', 'fontsize': 12, 'fontweight': 'bold'}
FONT_LABEL      = {'fontfamily': 'serif', 'fontsize': 10}


# ── Helpers ──────────────────────────────────────────────────

def _fig_to_png(fig, dpi=150) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return buf.read()

def _create_fig(figsize=(6, 5)):
    fig = Figure(figsize=figsize)
    FigureCanvasAgg(fig)
    return fig

def _safe(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _draw_right_angle_mark(ax, vertex, arm1_dir, arm2_dir, size=0.25):
    """Draw a small square at vertex indicating a right angle."""
    vx, vy = vertex
    p1 = (vx + arm1_dir[0]*size, vy + arm1_dir[1]*size)
    p2 = (vx + arm1_dir[0]*size + arm2_dir[0]*size, vy + arm1_dir[1]*size + arm2_dir[1]*size)
    p3 = (vx + arm2_dir[0]*size, vy + arm2_dir[1]*size)
    ax.plot([p1[0], p2[0], p3[0]], [p1[1], p2[1], p3[1]], 'k-', linewidth=1.0)

def _draw_angle_arc(ax, vertex, start_angle_deg, end_angle_deg, radius=0.4, label='', color='black'):
    """Draw an arc indicating an angle at a vertex."""
    arc = mpatches.Arc(vertex, 2*radius, 2*radius, angle=0,
                       theta1=start_angle_deg, theta2=end_angle_deg,
                       color=color, linewidth=1.2)
    ax.add_patch(arc)
    if label:
        mid_angle = np.radians((start_angle_deg + end_angle_deg) / 2)
        lx = vertex[0] + (radius + 0.15) * np.cos(mid_angle)
        ly = vertex[1] + (radius + 0.15) * np.sin(mid_angle)
        ax.text(lx, ly, label, ha='center', va='center', fontsize=10,
                fontfamily='serif', color=color, bbox=LABEL_BBOX)


# ═══════════════════════════════════════════════════════════════
# 1. GEOMETRY PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def render_right_triangle(params: dict) -> bytes:
    base = _safe(params.get('base', 4), 4)
    height = _safe(params.get('height', 3), 3)
    hyp = np.sqrt(base**2 + height**2)
    labels = params.get('labels', {})
    angle_label = params.get('angle_label', r'$\theta$')
    show_right = params.get('show_right_angle', True)

    fig = _create_fig(figsize=(6, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    # Vertices: A(0,0) bottom-left (right angle), B(base,0), C(0,height)
    A, B, C = (0, 0), (base, 0), (0, height)
    triangle = mpatches.Polygon([A, B, C], closed=True, fill=False,
                                 edgecolor='black', linewidth=1.8)
    ax.add_patch(triangle)

    # Right angle mark at A
    if show_right:
        _draw_right_angle_mark(ax, A, (1, 0), (0, 1), size=min(base, height)*0.08)

    # Angle at B
    angle_B = np.degrees(np.arctan2(height, base))
    _draw_angle_arc(ax, B, 180 - angle_B + 180, 180, radius=min(base, height)*0.12,
                    label=angle_label, color=COLOR_ACCENT)

    # Labels
    base_lbl = labels.get('base', f'{base:.4g}')
    height_lbl = labels.get('height', f'{height:.4g}')
    hyp_lbl = labels.get('hypotenuse', f'{hyp:.4g}')

    ax.text(base/2, -0.25, base_lbl, ha='center', va='top', **FONT_LABEL, bbox=LABEL_BBOX)
    ax.text(-0.25, height/2, height_lbl, ha='right', va='center', **FONT_LABEL,
            rotation=90, bbox=LABEL_BBOX)
    # Hypotenuse label — midpoint offset outward
    mx, my = (base/2, height/2)
    nx, ny = (height / hyp * 0.3, -base / hyp * 0.3)  # normal outward
    ax.text(mx + nx, my + ny, hyp_lbl, ha='center', va='center', **FONT_LABEL,
            rotation=-np.degrees(np.arctan2(height, base)), bbox=LABEL_BBOX)

    # Vertex labels
    ax.text(A[0]-0.15, A[1]-0.15, params.get('vertex_A', 'A'), **FONT_MATH)
    ax.text(B[0]+0.15, B[1]-0.15, params.get('vertex_B', 'B'), **FONT_MATH)
    ax.text(C[0]-0.15, C[1]+0.15, params.get('vertex_C', 'C'), **FONT_MATH)

    ax.autoscale()
    ax.margins(0.15)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_triangle(params: dict) -> bytes:
    """General triangle from vertices or SSS side lengths."""
    fig = _create_fig(figsize=(6, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    vertices = params.get('vertices')
    if vertices and len(vertices) >= 3:
        A = (float(vertices[0][0]), float(vertices[0][1]))
        B = (float(vertices[1][0]), float(vertices[1][1]))
        C = (float(vertices[2][0]), float(vertices[2][1]))
    else:
        sides = params.get('sides', [5, 4, 3])
        a, b, c = float(sides[0]), float(sides[1]), float(sides[2])
        # Place A at origin, B on x-axis
        A = (0, 0)
        B = (c, 0)
        # C via law of cosines: cos(A) = (b²+c²-a²)/(2bc)
        cos_A = (b**2 + c**2 - a**2) / (2 * b * c)
        cos_A = max(-1, min(1, cos_A))
        sin_A = np.sqrt(1 - cos_A**2)
        C = (b * cos_A, b * sin_A)

    tri = mpatches.Polygon([A, B, C], closed=True, fill=False,
                            edgecolor='black', linewidth=1.8)
    ax.add_patch(tri)

    labels = params.get('labels', {})
    verts = [A, B, C]
    default_names = ['A', 'B', 'C']
    for i, v in enumerate(verts):
        # Compute outward direction for label placement
        cx = sum(p[0] for p in verts) / 3
        cy = sum(p[1] for p in verts) / 3
        dx, dy = v[0] - cx, v[1] - cy
        dist = np.hypot(dx, dy) or 1
        lx = v[0] + dx/dist * 0.25
        ly = v[1] + dy/dist * 0.25
        name = labels.get(f'vertex_{i}', labels.get(default_names[i], default_names[i]))
        ax.text(lx, ly, name, ha='center', va='center', **FONT_MATH, bbox=LABEL_BBOX)
        ax.plot(v[0], v[1], 'ko', markersize=4)

    # Side labels
    side_pairs = [(0, 1, 'side_a'), (1, 2, 'side_b'), (2, 0, 'side_c')]
    for i, j, key in side_pairs:
        mx = (verts[i][0] + verts[j][0]) / 2
        my = (verts[i][1] + verts[j][1]) / 2
        cx = sum(p[0] for p in verts) / 3
        cy = sum(p[1] for p in verts) / 3
        dx, dy = mx - cx, my - cy
        dist = np.hypot(dx, dy) or 1
        if key in labels:
            ax.text(mx + dx/dist*0.3, my + dy/dist*0.3, labels[key],
                    ha='center', va='center', **FONT_LABEL, bbox=LABEL_BBOX)

    ax.autoscale()
    ax.margins(0.15)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_circle(params: dict) -> bytes:
    radius = _safe(params.get('radius', 2), 2)
    center = params.get('center', [0, 0])
    cx, cy = float(center[0]), float(center[1])
    labels = params.get('labels', {})
    show_radius = params.get('show_radius', True)
    show_diameter = params.get('show_diameter', False)
    show_center = params.get('show_center', True)

    fig = _create_fig(figsize=(5, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    circle = mpatches.Circle((cx, cy), radius, fill=False, edgecolor='black', linewidth=1.8)
    ax.add_patch(circle)

    if show_center:
        ax.plot(cx, cy, 'ko', markersize=4)
        lbl = labels.get('center', 'O')
        ax.text(cx - 0.15, cy - 0.2, lbl, **FONT_MATH, bbox=LABEL_BBOX)

    if show_radius:
        angle = np.pi / 4
        ex, ey = cx + radius * np.cos(angle), cy + radius * np.sin(angle)
        ax.plot([cx, ex], [cy, ey], 'k-', linewidth=1.2)
        mx, my = (cx + ex)/2, (cy + ey)/2
        lbl = labels.get('radius', f'r = {radius:.4g}')
        ax.text(mx + 0.1, my + 0.1, lbl, **FONT_LABEL, bbox=LABEL_BBOX)

    if show_diameter:
        ax.plot([cx - radius, cx + radius], [cy, cy], '--', color=COLOR_PRIMARY, linewidth=1.2)
        lbl = labels.get('diameter', f'd = {2*radius:.4g}')
        ax.text(cx, cy - 0.3, lbl, ha='center', **FONT_LABEL, color=COLOR_PRIMARY, bbox=LABEL_BBOX)

    ax.autoscale()
    ax.margins(0.2)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_quadrilateral(params: dict) -> bytes:
    qtype = params.get('type', 'rectangle')
    dims = params.get('dimensions', {})
    labels = params.get('labels', {})

    if qtype == 'square':
        side = _safe(dims.get('side', 4), 4)
        verts = [(0, 0), (side, 0), (side, side), (0, side)]
    elif qtype == 'rectangle':
        w = _safe(dims.get('width', 5), 5)
        h = _safe(dims.get('height', 3), 3)
        verts = [(0, 0), (w, 0), (w, h), (0, h)]
    elif qtype == 'parallelogram':
        base = _safe(dims.get('base', 5), 5)
        side = _safe(dims.get('side', 3), 3)
        angle = np.radians(_safe(dims.get('angle', 60), 60))
        shift = side * np.cos(angle)
        h = side * np.sin(angle)
        verts = [(0, 0), (base, 0), (base + shift, h), (shift, h)]
    elif qtype == 'trapezoid':
        bot = _safe(dims.get('bottom_base', 6), 6)
        top = _safe(dims.get('top_base', 3), 3)
        h = _safe(dims.get('height', 3), 3)
        offset = (bot - top) / 2
        verts = [(0, 0), (bot, 0), (bot - offset, h), (offset, h)]
    elif qtype == 'rhombus':
        d1 = _safe(dims.get('diagonal1', 4), 4)
        d2 = _safe(dims.get('diagonal2', 6), 6)
        verts = [(0, d1/2), (d2/2, 0), (0, -d1/2), (-d2/2, 0)]
    else:
        verts = [(0, 0), (4, 0), (4, 3), (0, 3)]

    fig = _create_fig(figsize=(6, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    poly = mpatches.Polygon(verts, closed=True, fill=True, facecolor=COLOR_FILL,
                             edgecolor='black', linewidth=1.8)
    ax.add_patch(poly)

    # Side labels
    names = ['AB', 'BC', 'CD', 'DA']
    for i in range(len(verts)):
        j = (i + 1) % len(verts)
        mx = (verts[i][0] + verts[j][0]) / 2
        my = (verts[i][1] + verts[j][1]) / 2
        cx_c = sum(v[0] for v in verts) / len(verts)
        cy_c = sum(v[1] for v in verts) / len(verts)
        dx, dy = mx - cx_c, my - cy_c
        dist = np.hypot(dx, dy) or 1
        lbl = labels.get(names[i], labels.get(f'side_{i}', ''))
        if lbl:
            ax.text(mx + dx/dist*0.3, my + dy/dist*0.3, lbl,
                    ha='center', va='center', **FONT_LABEL, bbox=LABEL_BBOX)

    # Vertex labels
    vert_names = params.get('vertex_labels', ['A', 'B', 'C', 'D'])
    for i, v in enumerate(verts):
        cx_c = sum(p[0] for p in verts) / len(verts)
        cy_c = sum(p[1] for p in verts) / len(verts)
        dx, dy = v[0] - cx_c, v[1] - cy_c
        dist = np.hypot(dx, dy) or 1
        if i < len(vert_names):
            ax.text(v[0] + dx/dist*0.2, v[1] + dy/dist*0.2,
                    vert_names[i], **FONT_MATH, bbox=LABEL_BBOX)
        ax.plot(v[0], v[1], 'ko', markersize=3)

    ax.autoscale()
    ax.margins(0.15)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_parallel_lines(params: dict) -> bytes:
    angle = _safe(params.get('angle', 60), 60)
    labels = params.get('labels', {})
    theta = np.radians(angle)

    fig = _create_fig(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    # Two horizontal parallel lines
    y1, y2 = 0, 3
    ax.plot([-2, 6], [y1, y1], 'k-', linewidth=1.8)
    ax.plot([-2, 6], [y2, y2], 'k-', linewidth=1.8)

    # Parallel line markers (arrows)
    for y in [y1, y2]:
        ax.annotate('', xy=(5.5, y), xytext=(5.8, y),
                    arrowprops=dict(arrowstyle='->', color=COLOR_PRIMARY, lw=1.2))

    # Transversal line
    # Passes through point (2, y1) on line 1
    length = 5
    x_start = 2 - length * np.cos(theta) / 2
    y_start = y1 - length * np.sin(theta) / 2
    x_end = 2 + length * np.cos(theta) / 2
    y_end = y1 + length * np.sin(theta) / 2
    ax.plot([x_start, x_end], [y_start, y_end], 'k-', linewidth=1.5)

    # Intersection points
    # Line 1 intersection at (2, 0)
    ix1 = 2
    # Line 2 intersection: solve y2 = y1 + (x - ix1)*tan(theta)
    ix2 = ix1 + (y2 - y1) / np.tan(theta) if np.tan(theta) != 0 else ix1

    # Angle arcs
    for label_key, iy, ix, start, end, pos_angle in [
        ('angle_1', y1, ix1, 0, angle, angle/2),
        ('angle_2', y1, ix1, angle, 180, (angle + 180)/2),
        ('angle_3', y2, ix2, 0, angle, angle/2),
        ('angle_4', y2, ix2, angle, 180, (angle + 180)/2),
    ]:
        lbl = labels.get(label_key, '')
        if lbl:
            _draw_angle_arc(ax, (ix, iy), start, end, radius=0.4, label=lbl)

    ax.text(-1.8, y1 + 0.2, labels.get('line_1', 'l₁'), **FONT_MATH, color=COLOR_PRIMARY)
    ax.text(-1.8, y2 + 0.2, labels.get('line_2', 'l₂'), **FONT_MATH, color=COLOR_PRIMARY)
    ax.text(x_end + 0.1, y_end + 0.1, labels.get('transversal', 't'), **FONT_MATH)

    ax.autoscale()
    ax.margins(0.1)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_coordinate_geometry(params: dict) -> bytes:
    points = params.get('points', [])
    lines = params.get('lines', [])
    curves = params.get('curves', [])
    x_range = params.get('x_range', [-5, 5])
    y_range = params.get('y_range', [-5, 5])
    show_grid = params.get('show_grid', True)

    fig = _create_fig(figsize=(6, 6))
    ax = fig.add_subplot(111)

    ax.set_xlim(x_range[0], x_range[1])
    ax.set_ylim(y_range[0], y_range[1])
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axvline(0, color='black', linewidth=0.8)
    if show_grid:
        ax.grid(True, alpha=0.3, color=COLOR_GRID)
    ax.set_xlabel('x', fontsize=11)
    ax.set_ylabel('y', fontsize=11)

    for pt in points:
        x, y = float(pt['x']), float(pt['y'])
        ax.plot(x, y, 'o', color=COLOR_PRIMARY, markersize=6, zorder=5)
        lbl = pt.get('label', f'({x}, {y})')
        ax.text(x + 0.2, y + 0.2, lbl, **FONT_LABEL, bbox=LABEL_BBOX, zorder=6)

    for line in lines:
        fr = line.get('from', [0, 0])
        to = line.get('to', [1, 1])
        ax.plot([fr[0], to[0]], [fr[1], to[1]], '-', color=COLOR_ACCENT, linewidth=1.5)
        lbl = line.get('label', '')
        if lbl:
            mx = (fr[0] + to[0]) / 2
            my = (fr[1] + to[1]) / 2
            ax.text(mx, my + 0.3, lbl, ha='center', **FONT_LABEL, color=COLOR_ACCENT, bbox=LABEL_BBOX)

    for curve in curves:
        expr = curve.get('expression', 'x')
        label = curve.get('label', expr)
        x = np.linspace(x_range[0], x_range[1], 400)
        try:
            safe_expr = expr.replace('^', '**')
            y = eval(safe_expr, {'x': x, 'np': np, 'sin': np.sin, 'cos': np.cos,
                                  'tan': np.tan, 'sqrt': np.sqrt, 'log': np.log,
                                  'exp': np.exp, 'pi': np.pi, 'e': np.e, 'abs': np.abs}, {})
            if np.isscalar(y):
                y = np.full_like(x, y)
            ax.plot(x, y, linewidth=1.5, label=label)
        except Exception:
            pass
    if curves:
        ax.legend(fontsize=9)

    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# 2. PHYSICS PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def render_inclined_plane(params: dict) -> bytes:
    angle_deg = _safe(params.get('angle', 30), 30)
    theta = np.radians(angle_deg)
    base_len = 5.0
    height = base_len * np.tan(theta)

    fig = _create_fig(figsize=(7, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    # Triangle: bottom-left, bottom-right, top-left
    A = (0, 0)
    B = (base_len, 0)
    C = (0, height)
    tri = mpatches.Polygon([A, B, C], closed=True, fill=True,
                            facecolor='#F5F5F5', edgecolor='black', linewidth=2)
    ax.add_patch(tri)

    # Ground hatching
    for i in range(0, int(base_len * 4) + 1, 1):
        x = i * 0.25
        if x <= base_len:
            ax.plot([x, x - 0.15], [0, -0.15], 'k-', linewidth=0.5)

    # Block on incline surface
    block_w, block_h = 0.8, 0.7
    # Center of block along the slope at 40% up
    t_pos = 0.4
    bx = B[0] * (1 - t_pos)
    by = 0 + height * t_pos * (B[0] - 0)  # This needs fixing
    # Correct: point on hypotenuse from B to C
    slope_x = B[0] + (C[0] - B[0]) * t_pos
    slope_y = B[1] + (C[1] - B[1]) * t_pos

    # Block corners (rotated rectangle sitting on the slope)
    # Normal to slope: (-sin(theta), cos(theta))
    # Along slope: (-cos(theta), sin(theta)) pointing from B toward C
    along = np.array([C[0] - B[0], C[1] - B[1]])
    along = along / np.linalg.norm(along)
    normal = np.array([-along[1], along[0]])

    bl = np.array([slope_x, slope_y]) - along * block_w/2
    corners = [
        bl,
        bl + along * block_w,
        bl + along * block_w + normal * block_h,
        bl + normal * block_h,
    ]
    block = mpatches.Polygon(corners, closed=True, fill=True,
                              facecolor=COLOR_FILL, edgecolor='black', linewidth=1.5)
    ax.add_patch(block)

    # Mass label
    mass_lbl = params.get('mass_label', 'm')
    block_center = np.array([slope_x, slope_y]) + normal * block_h / 2
    ax.text(block_center[0], block_center[1], mass_lbl, ha='center', va='center',
            fontsize=12, fontfamily='serif', fontweight='bold')

    # Force arrows (if requested)
    if params.get('show_forces', True):
        arrow_base = block_center
        arrow_len = 1.5

        # Weight (downward)
        w_label = params.get('weight_label', 'mg')
        ax.annotate('', xy=arrow_base + np.array([0, -arrow_len]),
                    xytext=arrow_base,
                    arrowprops=dict(arrowstyle='->', color=COLOR_ACCENT, lw=2))
        ax.text(arrow_base[0] + 0.2, arrow_base[1] - arrow_len - 0.15, w_label,
                fontsize=11, color=COLOR_ACCENT, fontfamily='serif', bbox=LABEL_BBOX)

        # Normal force (perpendicular to surface)
        n_label = params.get('normal_label', 'N')
        ax.annotate('', xy=arrow_base + normal * arrow_len,
                    xytext=arrow_base,
                    arrowprops=dict(arrowstyle='->', color=COLOR_GREEN, lw=2))
        n_tip = arrow_base + normal * arrow_len
        ax.text(n_tip[0] + 0.15, n_tip[1] + 0.15, n_label,
                fontsize=11, color=COLOR_GREEN, fontfamily='serif', bbox=LABEL_BBOX)

        # Friction (along surface, downhill)
        friction_label = params.get('friction_label', '')
        if friction_label:
            ax.annotate('', xy=arrow_base + along * arrow_len * 0.8,
                        xytext=arrow_base,
                        arrowprops=dict(arrowstyle='->', color='#FF8F00', lw=2))
            f_tip = arrow_base + along * arrow_len * 0.8
            ax.text(f_tip[0] + 0.15, f_tip[1] + 0.15, friction_label,
                    fontsize=10, color='#FF8F00', fontfamily='serif', bbox=LABEL_BBOX)

        # Applied force (optional, up the incline)
        applied_label = params.get('applied_force_label', '')
        if applied_label:
            ax.annotate('', xy=arrow_base - along * arrow_len * 0.8,
                        xytext=arrow_base,
                        arrowprops=dict(arrowstyle='->', color=COLOR_PRIMARY, lw=2))

    # Angle arc at bottom-right
    _draw_angle_arc(ax, B, 180, 180 - angle_deg + 180, radius=0.5,
                    label=f'${angle_deg}°$', color=COLOR_ACCENT)

    # Dimension labels
    if params.get('height_label'):
        ax.text(-0.3, height/2, params['height_label'], ha='right', va='center',
                **FONT_LABEL, bbox=LABEL_BBOX, rotation=90)
        ax.plot([0, 0], [0, height], '--', color=COLOR_PRIMARY, linewidth=0.8)
    if params.get('base_label'):
        ax.text(base_len/2, -0.4, params['base_label'], ha='center', va='top',
                **FONT_LABEL, bbox=LABEL_BBOX)

    ax.autoscale()
    ax.margins(0.12)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_projectile_motion(params: dict) -> bytes:
    v0 = _safe(params.get('v0', 20), 20)
    angle_deg = _safe(params.get('angle', 45), 45)
    g = _safe(params.get('g', 9.8), 9.8)
    labels = params.get('labels', {})
    theta = np.radians(angle_deg)

    # Compute trajectory
    t_flight = 2 * v0 * np.sin(theta) / g
    t = np.linspace(0, t_flight, 200)
    x = v0 * np.cos(theta) * t
    y = v0 * np.sin(theta) * t - 0.5 * g * t**2

    R = v0**2 * np.sin(2 * theta) / g
    H = v0**2 * np.sin(theta)**2 / (2 * g)

    fig = _create_fig(figsize=(7, 4))
    ax = fig.add_subplot(111)

    # Ground line
    ax.axhline(0, color='black', linewidth=1.2)
    ax.plot(x, y, color=COLOR_PRIMARY, linewidth=2, label='Trajectory')

    # Launch velocity vector
    vx_arrow = v0 * np.cos(theta) * 0.1
    vy_arrow = v0 * np.sin(theta) * 0.1
    ax.annotate('', xy=(vx_arrow, vy_arrow), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color=COLOR_ACCENT, lw=2))
    ax.text(vx_arrow + 0.3, vy_arrow + 0.3,
            labels.get('v0', f'$v_0 = {v0}$ m/s'), fontsize=10, color=COLOR_ACCENT,
            fontfamily='serif', bbox=LABEL_BBOX)

    # Angle arc
    _draw_angle_arc(ax, (0, 0), 0, angle_deg, radius=R*0.06,
                    label=labels.get('angle', f'${angle_deg}°$'), color=COLOR_ACCENT)

    # Max height dashed line
    ax.plot([R/2, R/2], [0, H], '--', color=COLOR_GREEN, linewidth=1)
    ax.annotate('', xy=(R/2 - R*0.02, H), xytext=(R/2 - R*0.02, 0),
                arrowprops=dict(arrowstyle='<->', color=COLOR_GREEN, lw=1.2))
    ax.text(R/2 - R*0.08, H/2, labels.get('H_max', f'$H_{{max}}$'),
            fontsize=10, color=COLOR_GREEN, fontfamily='serif', bbox=LABEL_BBOX)

    # Range annotation
    ax.annotate('', xy=(R, -H*0.08), xytext=(0, -H*0.08),
                arrowprops=dict(arrowstyle='<->', color='#FF8F00', lw=1.2))
    ax.text(R/2, -H*0.15, labels.get('R', f'$R = {R:.1f}$ m'),
            ha='center', fontsize=10, color='#FF8F00', fontfamily='serif', bbox=LABEL_BBOX)

    # Key points
    ax.plot(0, 0, 'ko', markersize=5)
    ax.plot(R, 0, 'ko', markersize=5)
    ax.plot(R/2, H, 'o', color=COLOR_ACCENT, markersize=5)

    ax.set_xlabel('Horizontal Distance (m)', fontsize=10)
    ax.set_ylabel('Height (m)', fontsize=10)
    ax.set_ylim(bottom=-H*0.25)
    ax.grid(alpha=0.2)
    title = params.get('title', 'Projectile Motion')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_free_body(params: dict) -> bytes:
    object_label = params.get('object_label', 'm')
    object_shape = params.get('object_shape', 'block')
    forces = params.get('forces', [])
    title = params.get('title', 'Free Body Diagram')

    fig = _create_fig(figsize=(5, 5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-4.5, 4.5)
    ax.set_ylim(-4.5, 4.5)

    # Draw object
    if object_shape == 'circle':
        obj = mpatches.Circle((0, 0), 0.5, fill=True, facecolor=COLOR_FILL,
                               edgecolor='black', linewidth=1.5)
    else:  # block or point
        obj = mpatches.FancyBboxPatch((-0.5, -0.5), 1, 1,
                                       boxstyle='round,pad=0.05', linewidth=1.5,
                                       edgecolor='black', facecolor=COLOR_FILL)
    ax.add_patch(obj)
    ax.text(0, 0, object_label, ha='center', va='center', fontsize=12,
            fontfamily='serif', fontweight='bold')

    # Normalize magnitudes for arrow lengths
    magnitudes = []
    for f in forces:
        magnitudes.append(_safe(f.get('magnitude', 1), 1))
    max_mag = max(magnitudes) if magnitudes else 1
    if max_mag == 0:
        max_mag = 1

    direction_map = {'up': 90, 'down': 270, 'left': 180, 'right': 0,
                     'up-right': 45, 'up-left': 135, 'down-right': 315, 'down-left': 225}

    for i, f in enumerate(forces):
        mag = _safe(f.get('magnitude', 1), 1)
        label = f.get('label', 'F')

        # Get angle
        if 'angle' in f:
            angle_deg = _safe(f['angle'], 0)
        else:
            dir_str = f.get('direction', 'up').lower().replace(' ', '-')
            angle_deg = direction_map.get(dir_str, 0)

        angle_rad = np.radians(angle_deg)
        arrow_len = 1.5 + (mag / max_mag) * 1.5

        dx = np.cos(angle_rad) * arrow_len
        dy = np.sin(angle_rad) * arrow_len

        # Start from edge of object
        start_x = np.cos(angle_rad) * 0.55
        start_y = np.sin(angle_rad) * 0.55

        ax.annotate('', xy=(start_x + dx, start_y + dy), xytext=(start_x, start_y),
                    arrowprops=dict(arrowstyle='->', color=COLOR_ACCENT, lw=2.5,
                                    mutation_scale=18))

        # Label at tip
        tip_x = start_x + dx + np.cos(angle_rad) * 0.3
        tip_y = start_y + dy + np.sin(angle_rad) * 0.3
        ax.text(tip_x, tip_y, label, ha='center', va='center', fontsize=11,
                color=COLOR_ACCENT, fontweight='bold', fontfamily='serif',
                bbox=dict(boxstyle='round,pad=0.12', fc='white', ec=COLOR_ACCENT,
                          lw=0.8, alpha=0.95))

    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_lens_ray_diagram(params: dict) -> bytes:
    lens_type = params.get('lens_type', 'convex')
    f = _safe(params.get('focal_length', 3), 3)
    u = _safe(params.get('object_distance', 6), 6)  # positive, on left
    h_obj = _safe(params.get('object_height', 1.5), 1.5)
    labels = params.get('labels', {})

    # Thin lens equation: 1/v = 1/f + 1/u (sign convention: u negative for real object)
    if lens_type == 'convex':
        # Real object on left: u = -|u|, f = +|f|
        # 1/v = 1/f - 1/u => v = f*u / (u - f)
        if u != f:
            v = f * u / (u - f)
        else:
            v = 100  # at infinity
        h_img = -h_obj * v / u if u != 0 else 0
    else:
        # Concave lens: f is negative
        f_neg = -abs(f)
        if u + abs(f) != 0:
            v = f_neg * u / (u + abs(f))
        else:
            v = -100
        h_img = -h_obj * v / u if u != 0 else 0

    fig = _create_fig(figsize=(8, 4))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')

    # Principal axis
    total_len = max(abs(u), abs(v), 2*abs(f)) * 1.3
    ax.axhline(0, color='black', linewidth=0.8, zorder=1)
    ax.set_xlim(-total_len, total_len)

    # Lens
    lens_height = max(abs(h_obj), abs(h_img), abs(f)*0.5) * 1.5
    if lens_type == 'convex':
        # Double-headed arrow for convex lens
        ax.annotate('', xy=(0, lens_height), xytext=(0, -lens_height),
                    arrowprops=dict(arrowstyle='<->', color=COLOR_PRIMARY, lw=2.5))
    else:
        # Diverging arrows for concave lens
        ax.annotate('', xy=(-0.2, lens_height), xytext=(0, lens_height*0.9),
                    arrowprops=dict(arrowstyle='<-', color=COLOR_PRIMARY, lw=2.5))
        ax.annotate('', xy=(-0.2, -lens_height), xytext=(0, -lens_height*0.9),
                    arrowprops=dict(arrowstyle='<-', color=COLOR_PRIMARY, lw=2.5))
        ax.plot([0, 0], [-lens_height*0.9, lens_height*0.9], color=COLOR_PRIMARY, linewidth=2)

    # Focal points
    ax.plot(f, 0, 'x', color=COLOR_ACCENT, markersize=8, markeredgewidth=2)
    ax.plot(-f, 0, 'x', color=COLOR_ACCENT, markersize=8, markeredgewidth=2)
    ax.text(f, -0.3, 'F', ha='center', fontsize=10, color=COLOR_ACCENT, fontfamily='serif')
    ax.text(-f, -0.3, "F'", ha='center', fontsize=10, color=COLOR_ACCENT, fontfamily='serif')

    # 2F points
    ax.plot(2*f, 0, '+', color=COLOR_GREEN, markersize=8, markeredgewidth=2)
    ax.plot(-2*f, 0, '+', color=COLOR_GREEN, markersize=8, markeredgewidth=2)
    ax.text(2*f, -0.3, '2F', ha='center', fontsize=9, color=COLOR_GREEN, fontfamily='serif')
    ax.text(-2*f, -0.3, "2F'", ha='center', fontsize=9, color=COLOR_GREEN, fontfamily='serif')

    # Object (arrow on left)
    obj_x = -u
    ax.annotate('', xy=(obj_x, h_obj), xytext=(obj_x, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(obj_x, h_obj + 0.2, labels.get('object', 'Object'), ha='center',
            fontsize=9, fontfamily='serif', bbox=LABEL_BBOX)

    # Image (arrow on right or left depending on sign)
    if abs(v) < 50:
        img_x = v if lens_type == 'convex' else v
        is_virtual = v < 0
        line_style = '--' if is_virtual else '-'

        ax.annotate('', xy=(img_x, h_img), xytext=(img_x, 0),
                    arrowprops=dict(arrowstyle='->', color=COLOR_GREEN, lw=2,
                                    linestyle=line_style))
        img_lbl = labels.get('image', 'Virtual Image' if is_virtual else 'Image')
        ax.text(img_x, h_img + 0.2 * np.sign(h_img), img_lbl, ha='center',
                fontsize=9, color=COLOR_GREEN, fontfamily='serif', bbox=LABEL_BBOX)

    # Ray 1: Parallel to axis → through F (or diverge from F for concave)
    ax.plot([obj_x, 0], [h_obj, h_obj], 'b-', linewidth=1, zorder=2)
    if lens_type == 'convex':
        ax.plot([0, total_len], [h_obj, h_obj - h_obj/f * total_len], 'b-', linewidth=1)
    else:
        # Diverges as if from F on same side
        ax.plot([0, total_len], [h_obj, h_obj + h_obj/abs(f) * total_len], 'b--', linewidth=1)
        ax.plot([0, -total_len*0.3], [h_obj, h_obj + h_obj/abs(f) * total_len*0.3], 'b-', linewidth=1)

    # Ray 2: Through center → straight
    ax.plot([obj_x, total_len], [h_obj, h_obj * (-total_len - obj_x)/(-obj_x) if obj_x != 0 else 0],
            'r-', linewidth=1, zorder=2)

    # Ray 3: Through F → parallel (for convex)
    if lens_type == 'convex' and abs(u) > abs(f):
        ax.plot([obj_x, 0], [h_obj, 0], 'g-', linewidth=1, zorder=2)  # simplified
        ax.plot([0, total_len], [0, 0], 'g-', linewidth=1)

    ax.set_xlabel('Distance', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_yticks([])
    title = params.get('title', f'{"Convex" if lens_type == "convex" else "Concave"} Lens Ray Diagram')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_mirror_ray_diagram(params: dict) -> bytes:
    mirror_type = params.get('mirror_type', 'concave')
    f = _safe(params.get('focal_length', 3), 3)
    u = _safe(params.get('object_distance', 6), 6)
    h_obj = _safe(params.get('object_height', 1.5), 1.5)
    labels = params.get('labels', {})

    fig = _create_fig(figsize=(8, 4))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')

    R = 2 * f
    total = max(u, 2*f) * 1.5

    # Principal axis
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlim(-total, total * 0.3)

    # Mirror (arc at x=0)
    mirror_h = max(h_obj, f * 0.5) * 2
    if mirror_type == 'concave':
        arc = mpatches.Arc((R, 0), 2*R, 2*mirror_h, angle=0,
                           theta1=90, theta2=270, color='black', linewidth=2.5)
    else:
        arc = mpatches.Arc((-R, 0), 2*R, 2*mirror_h, angle=0,
                           theta1=-90, theta2=90, color='black', linewidth=2.5)
    ax.add_patch(arc)

    # C, F, P markers
    ax.plot(0, 0, '|', color='black', markersize=10, markeredgewidth=2)
    ax.text(0.2, -0.3, 'P', fontsize=10, fontfamily='serif')
    ax.plot(-f, 0, 'x', color=COLOR_ACCENT, markersize=8, markeredgewidth=2)
    ax.text(-f, -0.3, 'F', fontsize=10, color=COLOR_ACCENT, fontfamily='serif')
    ax.plot(-R, 0, '+', color=COLOR_GREEN, markersize=8, markeredgewidth=2)
    ax.text(-R, -0.3, 'C', fontsize=10, color=COLOR_GREEN, fontfamily='serif')

    # Object
    obj_x = -u
    ax.annotate('', xy=(obj_x, h_obj), xytext=(obj_x, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(obj_x, h_obj + 0.2, labels.get('object', 'Object'),
            ha='center', fontsize=9, fontfamily='serif', bbox=LABEL_BBOX)

    # Mirror formula: 1/v + 1/u = 1/f (all negative for concave in our convention)
    if mirror_type == 'concave' and u != f:
        v = f * u / (u - f)
        h_img = -h_obj * v / u if u != 0 else 0
        img_x = -v
        is_virtual = v < 0

        style = '--' if is_virtual else '-'
        ax.annotate('', xy=(img_x, h_img), xytext=(img_x, 0),
                    arrowprops=dict(arrowstyle='->', color=COLOR_GREEN, lw=2,
                                    linestyle=style))
        ax.text(img_x, h_img - 0.3 * np.sign(h_img),
                labels.get('image', 'Image'), ha='center', fontsize=9,
                color=COLOR_GREEN, fontfamily='serif', bbox=LABEL_BBOX)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_yticks([])
    title = params.get('title', f'{"Concave" if mirror_type == "concave" else "Convex"} Mirror')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_wave_diagram(params: dict) -> bytes:
    amplitude = _safe(params.get('amplitude', 1), 1)
    wavelength = _safe(params.get('wavelength', 2), 2)
    num_cycles = _safe(params.get('num_cycles', 2), 2)
    show_annotations = params.get('show_annotations', True)

    x = np.linspace(0, num_cycles * wavelength, 500)
    y = amplitude * np.sin(2 * np.pi / wavelength * x)

    fig = _create_fig(figsize=(7, 3.5))
    ax = fig.add_subplot(111)
    ax.plot(x, y, color=COLOR_PRIMARY, linewidth=2)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')

    if show_annotations:
        # Amplitude
        peak_x = wavelength / 4
        ax.annotate('', xy=(peak_x, amplitude), xytext=(peak_x, 0),
                    arrowprops=dict(arrowstyle='<->', color=COLOR_ACCENT, lw=1.5))
        ax.text(peak_x + wavelength*0.05, amplitude/2, 'A',
                fontsize=11, color=COLOR_ACCENT, fontweight='bold', fontfamily='serif',
                bbox=LABEL_BBOX)

        # Wavelength
        ax.annotate('', xy=(wavelength, -amplitude - amplitude*0.2),
                    xytext=(0, -amplitude - amplitude*0.2),
                    arrowprops=dict(arrowstyle='<->', color=COLOR_GREEN, lw=1.5))
        ax.text(wavelength/2, -amplitude - amplitude*0.4, r'$\lambda$',
                ha='center', fontsize=12, color=COLOR_GREEN, fontfamily='serif',
                bbox=LABEL_BBOX)

        # Crest / Trough labels
        ax.text(wavelength/4, amplitude + amplitude*0.15, 'Crest',
                ha='center', fontsize=9, color=COLOR_PRIMARY, bbox=LABEL_BBOX)
        ax.text(3*wavelength/4, -amplitude - amplitude*0.15, 'Trough',
                ha='center', fontsize=9, color=COLOR_PRIMARY, bbox=LABEL_BBOX)

    ax.set_xlabel('Distance', fontsize=10)
    ax.set_ylabel('Displacement', fontsize=10)
    ax.grid(alpha=0.2)
    title = params.get('title', 'Wave Diagram')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_energy_level(params: dict) -> bytes:
    levels = params.get('levels', [
        {'n': 1, 'energy': -13.6, 'label': 'n=1'},
        {'n': 2, 'energy': -3.4, 'label': 'n=2'},
        {'n': 3, 'energy': -1.5, 'label': 'n=3'},
        {'n': 4, 'energy': -0.85, 'label': 'n=4'},
    ])
    transitions = params.get('transitions', [])
    title = params.get('title', 'Energy Level Diagram')

    energies = [_safe(l.get('energy', 0)) for l in levels]
    e_min = min(energies) if energies else -15
    e_max = max(energies) if energies else 0

    fig = _create_fig(figsize=(5, 5))
    ax = fig.add_subplot(111)
    ax.set_ylabel('Energy (eV)', fontsize=10)
    ax.set_xlim(0, 3)
    ax.set_ylim(e_min - 1, e_max + 1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])

    for lvl in levels:
        e = _safe(lvl.get('energy', 0))
        ax.hlines(e, 0.5, 2.5, colors=COLOR_PRIMARY, linewidth=2)
        lbl = lvl.get('label', f'E={e}')
        ax.text(2.6, e, lbl, va='center', fontsize=9, color=COLOR_PRIMARY, fontfamily='serif')

    # Build energy lookup by n
    energy_by_n = {int(l.get('n', i)): _safe(l.get('energy', 0)) for i, l in enumerate(levels)}

    for tr in transitions:
        e_from = energy_by_n.get(tr.get('from_n'), _safe(tr.get('from_energy', 0)))
        e_to = energy_by_n.get(tr.get('to_n'), _safe(tr.get('to_energy', 0)))
        color = tr.get('color', COLOR_ACCENT)
        ax.annotate('', xy=(1.5, e_to), xytext=(1.5, e_from),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.5, mutation_scale=15))
        if 'label' in tr:
            ax.text(1.7, (e_from + e_to)/2, tr['label'],
                    fontsize=8, color=color, fontfamily='serif', bbox=LABEL_BBOX)

    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_circuit(params: dict) -> bytes:
    """Render circuit diagrams using schemdraw."""
    try:
        import schemdraw
        import schemdraw.elements as elm
    except ImportError:
        return _placeholder_png('schemdraw not installed')

    components = params.get('components', [])
    circuit_type = params.get('circuit_type', 'series')

    comp_map = {
        'resistor': elm.Resistor, 'battery': elm.Battery, 'capacitor': elm.Capacitor,
        'switch': elm.Switch, 'wire': elm.Line, 'ground': elm.Ground,
        'ammeter': getattr(elm, 'MeterA', elm.Resistor),
        'voltmeter': getattr(elm, 'MeterV', elm.Resistor),
        'bulb': getattr(elm, 'Lamp', elm.Resistor),
        'inductor': getattr(elm, 'Inductor', elm.Resistor),
        'diode': getattr(elm, 'Diode', elm.Resistor),
        'led': getattr(elm, 'LED', elm.Resistor),
    }
    dir_map = {'right': 'right', 'left': 'left', 'up': 'up', 'down': 'down'}

    try:
        with schemdraw.Drawing(show=False) as d:
            for comp in components:
                ctype = comp.get('type', 'wire').lower()
                label = comp.get('label', '')
                value = comp.get('value', '')
                direction = dir_map.get(comp.get('direction', 'right'), 'right')
                elem_class = comp_map.get(ctype, elm.Line)
                e = elem_class()
                if direction == 'right': e = e.right()
                elif direction == 'left': e = e.left()
                elif direction == 'up': e = e.up()
                elif direction == 'down': e = e.down()
                display_label = f'{label}\n{value}' if label and value else (label or value)
                if display_label:
                    e = e.label(display_label)
                d += e

            try:
                return d.get_imagedata('png')
            except AttributeError:
                buf = io.BytesIO()
                d.save(buf, fmt='png')
                buf.seek(0)
                return buf.read()
    except Exception as e:
        logger.error(f'Circuit render failed: {e}')
        return _placeholder_png(f'Circuit error: {e}')


def render_spring_mass(params: dict) -> bytes:
    mass_label = params.get('mass_label', 'm')
    spring_label = params.get('spring_constant_label', 'k')
    displacement = params.get('displacement', 'x')
    orientation = params.get('orientation', 'horizontal')
    show_eq = params.get('show_equilibrium', True)

    fig = _create_fig(figsize=(7, 3) if orientation == 'horizontal' else (4, 6))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    if orientation == 'horizontal':
        # Wall on left
        ax.plot([0, 0], [-0.8, 0.8], 'k-', linewidth=3)
        for i in range(5):
            y = -0.8 + i * 0.4
            ax.plot([0, -0.15], [y, y - 0.15], 'k-', linewidth=0.8)

        # Spring (zigzag)
        spring_len = 3.0
        n_coils = 8
        sx = np.linspace(0.3, spring_len, n_coils * 2 + 1)
        sy = np.zeros_like(sx)
        for i in range(len(sx)):
            if i % 2 == 1:
                sy[i] = 0.25 if (i // 2) % 2 == 0 else -0.25
        ax.plot(sx, sy, 'k-', linewidth=1.5)

        # Mass block
        block_x = spring_len + 0.1
        block = mpatches.FancyBboxPatch((block_x, -0.5), 1, 1,
                                         boxstyle='round,pad=0.05', linewidth=1.5,
                                         edgecolor='black', facecolor=COLOR_FILL)
        ax.add_patch(block)
        ax.text(block_x + 0.5, 0, mass_label, ha='center', va='center',
                fontsize=13, fontweight='bold', fontfamily='serif')

        # Spring constant label
        ax.text(spring_len / 2, 0.5, spring_label, ha='center', fontsize=10,
                fontfamily='serif', color=COLOR_PRIMARY, bbox=LABEL_BBOX)

        # Equilibrium line
        if show_eq:
            eq_x = block_x + 0.5
            ax.plot([eq_x, eq_x], [-1.2, 1.2], '--', color=COLOR_GREEN, linewidth=0.8)
            ax.text(eq_x, -1.4, 'Equilibrium', ha='center', fontsize=8, color=COLOR_GREEN)

        # Displacement arrow
        if displacement:
            ax.annotate('', xy=(block_x + 1.5, -0.8), xytext=(block_x + 0.5, -0.8),
                        arrowprops=dict(arrowstyle='->', color=COLOR_ACCENT, lw=1.5))
            ax.text(block_x + 1.0, -1.1, displacement, ha='center', fontsize=10,
                    color=COLOR_ACCENT, fontfamily='serif', bbox=LABEL_BBOX)
    else:
        # Vertical orientation
        ax.plot([-0.8, 0.8], [5, 5], 'k-', linewidth=3)
        spring_len = 3.0
        n_coils = 8
        sy = np.linspace(4.7, 5 - spring_len, n_coils * 2 + 1)
        sx = np.zeros_like(sy)
        for i in range(len(sy)):
            if i % 2 == 1:
                sx[i] = 0.25 if (i // 2) % 2 == 0 else -0.25
        ax.plot(sx, sy, 'k-', linewidth=1.5)

        block_y = 5 - spring_len - 1.1
        block = mpatches.FancyBboxPatch((-0.5, block_y), 1, 1,
                                         boxstyle='round,pad=0.05', linewidth=1.5,
                                         edgecolor='black', facecolor=COLOR_FILL)
        ax.add_patch(block)
        ax.text(0, block_y + 0.5, mass_label, ha='center', va='center',
                fontsize=13, fontweight='bold', fontfamily='serif')

    ax.autoscale()
    ax.margins(0.15)
    title = params.get('title', 'Spring-Mass System')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_electric_field(params: dict) -> bytes:
    charges = params.get('charges', [{'type': '+', 'position': [0, 0], 'label': '+q'}])
    show_field_lines = params.get('show_field_lines', True)

    fig = _create_fig(figsize=(6, 6))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    for charge in charges:
        cx, cy = float(charge['position'][0]), float(charge['position'][1])
        ctype = charge.get('type', '+')
        color = COLOR_ACCENT if ctype == '+' else COLOR_PRIMARY
        circle = mpatches.Circle((cx, cy), 0.3, fill=True, facecolor=color,
                                  edgecolor='black', linewidth=1.5, zorder=5)
        ax.add_patch(circle)
        ax.text(cx, cy, ctype, ha='center', va='center', fontsize=14,
                fontweight='bold', color='white', zorder=6)
        lbl = charge.get('label', '')
        if lbl:
            ax.text(cx, cy - 0.5, lbl, ha='center', fontsize=10,
                    fontfamily='serif', bbox=LABEL_BBOX)

        if show_field_lines:
            n_lines = 8
            for i in range(n_lines):
                angle = 2 * np.pi * i / n_lines
                line_len = 2.0
                dx = np.cos(angle) * line_len
                dy = np.sin(angle) * line_len
                if ctype == '+':
                    ax.annotate('', xy=(cx + dx, cy + dy), xytext=(cx + np.cos(angle)*0.35, cy + np.sin(angle)*0.35),
                                arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.6))
                else:
                    ax.annotate('', xy=(cx + np.cos(angle)*0.35, cy + np.sin(angle)*0.35),
                                xytext=(cx + dx, cy + dy),
                                arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.6))

    ax.autoscale()
    ax.margins(0.2)
    title = params.get('title', 'Electric Field')
    ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# 3. DATA VISUALIZATION PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def render_function_graph(params: dict) -> bytes:
    functions = params.get('functions', [{'expression': 'x**2', 'label': 'y = x²'}])
    x_range = params.get('x_range', [-5, 5])
    y_range = params.get('y_range', None)
    show_grid = params.get('show_grid', True)

    fig = _create_fig(figsize=(6, 4.5))
    ax = fig.add_subplot(111)

    x = np.linspace(x_range[0], x_range[1], 400)
    import math

    colors = ['#1565C0', '#C62828', '#2E7D32', '#FF8F00', '#6A1B9A']
    for i, fn in enumerate(functions):
        expr = fn.get('expression', 'x')
        label = fn.get('label', expr)
        color = fn.get('color', colors[i % len(colors)])
        safe_expr = expr.replace('^', '**')
        if '=' in safe_expr:
            safe_expr = safe_expr.split('=')[-1].strip()
        try:
            with np.errstate(divide='ignore', invalid='ignore'):
                y = eval(safe_expr, {'x': x, 'np': np, 'math': math,
                                      'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                                      'sqrt': np.sqrt, 'log': np.log, 'log10': np.log10,
                                      'exp': np.exp, 'pi': np.pi, 'e': np.e, 'abs': np.abs}, {})
            if np.isscalar(y):
                y = np.full_like(x, y)
            # Clip asymptotes
            y_plot = np.copy(y)
            valid = y[np.isfinite(y)]
            if len(valid) > 0 and y_range is None:
                q1, q3 = np.percentile(valid, [5, 95])
                iqr = q3 - q1
                if iqr > 0:
                    y_plot[y > q3 + 10*iqr] = np.nan
                    y_plot[y < q1 - 10*iqr] = np.nan
            ax.plot(x, y_plot, color=color, linewidth=1.8, label=label)
        except Exception:
            pass

    ax.axhline(0, color='black', linewidth=0.8)
    ax.axvline(0, color='black', linewidth=0.8)
    if show_grid:
        ax.grid(alpha=0.3)
    if y_range:
        ax.set_ylim(y_range[0], y_range[1])
    ax.set_xlabel(params.get('x_label', 'x'), fontsize=10)
    ax.set_ylabel(params.get('y_label', 'y'), fontsize=10)
    if len(functions) > 1 or functions[0].get('label'):
        ax.legend(fontsize=9)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_bar_chart(params: dict) -> bytes:
    categories = params.get('categories', ['A', 'B', 'C'])
    values = [_safe(v) for v in params.get('values', [3, 7, 5])]
    colors = params.get('colors', [COLOR_PRIMARY] * len(categories))

    fig = _create_fig(figsize=(6, 4))
    ax = fig.add_subplot(111)

    bars = ax.bar(categories, values, color=colors[:len(categories)], edgecolor='white', linewidth=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{val:.4g}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel(params.get('x_label', ''), fontsize=10)
    ax.set_ylabel(params.get('y_label', ''), fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_pie_chart(params: dict) -> bytes:
    labels_list = params.get('labels', ['A', 'B', 'C'])
    values = [_safe(v) for v in params.get('values', [30, 50, 20])]
    colors = params.get('colors', ['#1565C0', '#C62828', '#2E7D32', '#FF8F00', '#6A1B9A', '#00838F'])

    fig = _create_fig(figsize=(5, 5))
    ax = fig.add_subplot(111)
    ax.pie(values, labels=labels_list, autopct='%1.1f%%', startangle=90,
           colors=colors[:len(values)], textprops={'fontsize': 10})
    ax.axis('equal')
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=15)
    return _fig_to_png(fig)


def render_histogram(params: dict) -> bytes:
    data = params.get('data')
    bins_list = params.get('bins')
    frequencies = params.get('frequencies')

    fig = _create_fig(figsize=(6, 4))
    ax = fig.add_subplot(111)

    if data:
        ax.hist([_safe(v) for v in data], bins=params.get('num_bins', 10),
                color=COLOR_PRIMARY, edgecolor='white', alpha=0.8)
    elif bins_list and frequencies:
        ax.bar(bins_list, [_safe(v) for v in frequencies], width=0.8,
               color=COLOR_PRIMARY, edgecolor='white')

    ax.set_xlabel(params.get('x_label', ''), fontsize=10)
    ax.set_ylabel(params.get('y_label', 'Frequency'), fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


def render_number_line(params: dict) -> bytes:
    range_vals = params.get('range', [-5, 5])
    points = params.get('points', [])
    intervals = params.get('intervals', [])

    fig = _create_fig(figsize=(8, 2))
    ax = fig.add_subplot(111)
    ax.set_ylim(-1, 1.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])

    # Main line with arrow tips
    ax.annotate('', xy=(range_vals[1] + 0.5, 0), xytext=(range_vals[0] - 0.5, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.annotate('', xy=(range_vals[0] - 0.5, 0), xytext=(range_vals[1] + 0.5, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

    # Tick marks
    for i in range(int(range_vals[0]), int(range_vals[1]) + 1):
        ax.plot([i, i], [-0.1, 0.1], 'k-', linewidth=1)
        ax.text(i, -0.3, str(i), ha='center', fontsize=9)

    # Points
    for pt in points:
        val = _safe(pt.get('value', 0))
        ax.plot(val, 0, 'o', color=COLOR_ACCENT, markersize=8, zorder=5)
        lbl = pt.get('label', '')
        if lbl:
            ax.text(val, 0.3, lbl, ha='center', fontsize=10, color=COLOR_ACCENT,
                    fontfamily='serif', bbox=LABEL_BBOX)

    # Intervals
    for intv in intervals:
        fr = _safe(intv.get('from', 0))
        to = _safe(intv.get('to', 1))
        ax.plot([fr, to], [0.6, 0.6], color=COLOR_PRIMARY, linewidth=3, solid_capstyle='round')
        lbl = intv.get('label', '')
        if lbl:
            ax.text((fr + to)/2, 0.85, lbl, ha='center', fontsize=9, color=COLOR_PRIMARY,
                    bbox=LABEL_BBOX)

    ax.set_xlim(range_vals[0] - 1, range_vals[1] + 1)
    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# 4. BIOLOGY PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def render_punnett_square(params: dict) -> bytes:
    parent1 = params.get('parent1', ['A', 'a'])
    parent2 = params.get('parent2', ['A', 'a'])
    title = params.get('title', 'Punnett Square')
    n = len(parent1)

    fig = _create_fig(figsize=(4.5, 5))
    ax = fig.add_subplot(111)
    ax.set_xlim(-0.5, n + 0.5)
    ax.set_ylim(-1, n + 0.8)
    ax.axis('off')
    ax.set_title(title, **FONT_TITLE, pad=12)

    # Parent1 headers (top)
    for j, allele in enumerate(parent1):
        ax.text(j + 0.5, n + 0.2, allele, ha='center', va='bottom',
                fontsize=13, fontweight='bold', color=COLOR_PRIMARY, fontfamily='serif')

    # Parent2 headers (left)
    for i, allele in enumerate(parent2):
        ax.text(-0.2, n - i - 0.5, allele, ha='right', va='center',
                fontsize=13, fontweight='bold', color=COLOR_ACCENT, fontfamily='serif')

    # Grid cells
    genotype_counts = {}
    for i in range(n):
        for j in range(n):
            combo = parent2[i] + parent1[j]
            genotype_counts[combo] = genotype_counts.get(combo, 0) + 1
            # Alternate cell colors
            fc = COLOR_FILL if (i + j) % 2 == 0 else COLOR_FILL_ALT
            rect = mpatches.FancyBboxPatch((j, n - i - 1), 1, 1,
                                            boxstyle='round,pad=0.05',
                                            linewidth=1, edgecolor='#555', facecolor=fc)
            ax.add_patch(rect)
            ax.text(j + 0.5, n - i - 0.5, combo,
                    ha='center', va='center', fontsize=12, fontfamily='serif')

    # Phenotype ratio summary
    total = n * n
    ratio_parts = []
    for genotype, count in sorted(genotype_counts.items()):
        ratio_parts.append(f'{genotype}: {count}/{total}')
    ratio_str = '  |  '.join(ratio_parts)
    ax.text(n/2, -0.5, f'Ratio: {ratio_str}', ha='center', fontsize=9,
            color='#555', fontfamily='serif')

    return _fig_to_png(fig)


def render_venn_diagram(params: dict) -> bytes:
    sets = params.get('sets', [{'label': 'A'}, {'label': 'B'}])
    title = params.get('title', '')
    intersection_label = params.get('intersection_label', '')

    fig = _create_fig(figsize=(5, 4.5))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.axis('off')

    if len(sets) >= 3:
        positions = [(2, 2.8), (1.2, 1.4), (2.8, 1.4)]
        colors = [COLOR_PRIMARY, COLOR_ACCENT, COLOR_GREEN]
        for pos, color, s in zip(positions, colors, sets[:3]):
            c = mpatches.Circle(pos, 1.1, alpha=0.2, color=color)
            ax.add_patch(c)
            ax.text(pos[0], pos[1], s.get('label', ''), ha='center', va='center',
                    fontsize=12, fontweight='bold', color=color)
            items = s.get('items', [])
            if items:
                ax.text(pos[0], pos[1] - 0.3, '\n'.join(str(x) for x in items[:3]),
                        ha='center', fontsize=8, color=color)
        if intersection_label:
            ax.text(2, 1.9, intersection_label, ha='center', fontsize=9, bbox=LABEL_BBOX)
        ax.set_xlim(0, 4.2)
        ax.set_ylim(0.2, 4.2)
    else:
        c1 = mpatches.Circle((1.5, 2), 1.3, alpha=0.2, color=COLOR_PRIMARY)
        c2 = mpatches.Circle((2.8, 2), 1.3, alpha=0.2, color=COLOR_ACCENT)
        ax.add_patch(c1)
        ax.add_patch(c2)
        ax.text(1.0, 2, sets[0].get('label', 'A'), ha='center', fontsize=12,
                fontweight='bold', color=COLOR_PRIMARY)
        if len(sets) > 0 and sets[0].get('items'):
            ax.text(1.0, 1.6, '\n'.join(str(x) for x in sets[0]['items'][:3]),
                    ha='center', fontsize=8, color=COLOR_PRIMARY)
        if len(sets) > 1:
            ax.text(3.3, 2, sets[1].get('label', 'B'), ha='center', fontsize=12,
                    fontweight='bold', color=COLOR_ACCENT)
            if sets[1].get('items'):
                ax.text(3.3, 1.6, '\n'.join(str(x) for x in sets[1]['items'][:3]),
                        ha='center', fontsize=8, color=COLOR_ACCENT)
        if intersection_label:
            ax.text(2.15, 2, intersection_label, ha='center', fontsize=10, bbox=LABEL_BBOX)
        ax.set_xlim(0, 4.5)
        ax.set_ylim(0.5, 3.5)

    if title:
        ax.set_title(title, **FONT_TITLE, pad=12)
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# 5. CHEMISTRY PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def render_molecular_structure(params: dict) -> bytes:
    smiles = params.get('smiles', '')
    if not smiles:
        return _placeholder_png('No SMILES string provided')
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return _placeholder_png(f'Invalid SMILES: {smiles}')
        img = Draw.MolToImage(mol, size=(400, 300))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.read()
    except ImportError:
        return _placeholder_png('rdkit not installed')
    except Exception as e:
        return _placeholder_png(f'Chemistry error: {e}')


# ═══════════════════════════════════════════════════════════════
# 6. CS / TREES / GRAPHS
# ═══════════════════════════════════════════════════════════════

def render_tree_graph(params: dict) -> bytes:
    try:
        import networkx as nx
    except ImportError:
        return _placeholder_png('networkx not installed')

    nodes = params.get('nodes', [])
    edges = params.get('edges', [])
    directed = params.get('directed', True)
    layout = params.get('layout', 'spring')

    G = nx.DiGraph() if directed else nx.Graph()
    for node in nodes:
        G.add_node(node.get('id'), label=node.get('label', node.get('id')))
    for edge in edges:
        src = edge.get('from', edge.get('from_node', ''))
        dst = edge.get('to', '')
        if src and dst:
            G.add_edge(src, dst, weight=edge.get('weight', ''))

    fig = _create_fig(figsize=(6, 5))
    ax = fig.add_subplot(111)
    ax.axis('off')

    if layout == 'tree':
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except Exception:
            pos = nx.spring_layout(G, seed=42)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)

    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=700,
                           node_color=COLOR_FILL, edgecolors=COLOR_PRIMARY, linewidths=1.5)
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=9)
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=directed,
                           arrowstyle='->', arrowsize=15, edge_color='#555')
    edge_labels = nx.get_edge_attributes(G, 'weight')
    edge_labels = {k: v for k, v in edge_labels.items() if v}
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=8)

    title = params.get('title', '')
    if title:
        ax.set_title(title, **FONT_TITLE, pad=10)
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# PLACEHOLDER HELPER
# ═══════════════════════════════════════════════════════════════

def _placeholder_png(reason: str = '') -> bytes:
    fig = _create_fig(figsize=(5, 3))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.add_patch(mpatches.FancyBboxPatch((0.05, 0.1), 0.9, 0.8,
                                          boxstyle='round,pad=0.02', linewidth=1,
                                          edgecolor='#CCC', facecolor='#F5F5F5'))
    ax.text(0.5, 0.65, 'Diagram unavailable', ha='center', va='center',
            fontsize=11, color='#666')
    ax.text(0.5, 0.38, reason[:70], ha='center', va='center', fontsize=8, color='#999')
    return _fig_to_png(fig)


# ═══════════════════════════════════════════════════════════════
# REGISTRY
# ═══════════════════════════════════════════════════════════════

PRIMITIVE_REGISTRY: dict[str, callable] = {
    'right_triangle': render_right_triangle,
    'triangle': render_triangle,
    'circle': render_circle,
    'quadrilateral': render_quadrilateral,
    'parallel_lines': render_parallel_lines,
    'coordinate_geometry': render_coordinate_geometry,
    'inclined_plane': render_inclined_plane,
    'projectile_motion': render_projectile_motion,
    'free_body': render_free_body,
    'lens_ray_diagram': render_lens_ray_diagram,
    'mirror_ray_diagram': render_mirror_ray_diagram,
    'wave_diagram': render_wave_diagram,
    'energy_level': render_energy_level,
    'circuit': render_circuit,
    'spring_mass': render_spring_mass,
    'electric_field': render_electric_field,
    'function_graph': render_function_graph,
    'bar_chart': render_bar_chart,
    'pie_chart': render_pie_chart,
    'histogram': render_histogram,
    'number_line': render_number_line,
    'punnett_square': render_punnett_square,
    'venn_diagram': render_venn_diagram,
    'molecular_structure': render_molecular_structure,
    'tree_graph': render_tree_graph,
}

# ═══════════════════════════════════════════════════════════════
# PRIMITIVE CATALOG (for LLM prompt injection)
# ═══════════════════════════════════════════════════════════════

PRIMITIVE_CATALOG = """Available diagram primitives. Pick ONE and fill its params as JSON.

GEOMETRY:
- right_triangle: {base, height, labels: {base, height, hypotenuse}, angle_label, show_right_angle, vertex_A, vertex_B, vertex_C, title}
- triangle: {vertices: [[x,y],...] OR sides: [a,b,c], labels: {vertex_0, side_a, side_b, side_c}, title}
- circle: {radius, center: [x,y], labels: {radius, diameter, center}, show_radius, show_diameter, show_center, title}
- quadrilateral: {type: square|rectangle|parallelogram|trapezoid|rhombus, dimensions: {side|width+height|base+side+angle|top_base+bottom_base+height|diagonal1+diagonal2}, labels, vertex_labels, title}
- parallel_lines: {angle, labels: {angle_1..angle_4, line_1, line_2, transversal}, title}
- coordinate_geometry: {points: [{x,y,label}], lines: [{from:[x,y],to:[x,y],label}], curves: [{expression,label}], x_range, y_range, show_grid, title}

PHYSICS:
- inclined_plane: {angle, mass_label, friction_label, height_label, base_label, show_forces, normal_label, weight_label, applied_force_label, title}
- projectile_motion: {v0, angle, g, labels: {v0, angle, H_max, R}, title}
- free_body: {object_label, object_shape: block|circle|point, forces: [{direction: up|down|left|right OR angle, magnitude, label}], title}
- lens_ray_diagram: {lens_type: convex|concave, focal_length, object_distance, object_height, labels: {object, image}, title}
- mirror_ray_diagram: {mirror_type: concave|convex, focal_length, object_distance, object_height, labels: {object, image}, title}
- wave_diagram: {amplitude, wavelength, num_cycles, show_annotations, title}
- energy_level: {levels: [{n, energy, label}], transitions: [{from_n, to_n, label, color}], title}
- circuit: {components: [{type: resistor|battery|capacitor|switch|wire|ground|ammeter|voltmeter|bulb|inductor, label, direction: right|left|up|down, value}], circuit_type: series|parallel, title}
- spring_mass: {mass_label, spring_constant_label, displacement, orientation: horizontal|vertical, show_equilibrium, title}
- electric_field: {charges: [{type: +|-, position: [x,y], label}], show_field_lines, title}

DATA:
- function_graph: {functions: [{expression, label, color}], x_range, y_range, show_grid, x_label, y_label, title}
- bar_chart: {categories, values, x_label, y_label, colors, title}
- pie_chart: {labels, values, colors, title}
- histogram: {data OR bins+frequencies, num_bins, x_label, y_label, title}
- number_line: {range: [min,max], points: [{value,label}], intervals: [{from,to,label}], title}

BIOLOGY:
- punnett_square: {parent1: [alleles], parent2: [alleles], title}
- venn_diagram: {sets: [{label, items}], intersection_label, title}

CHEMISTRY:
- molecular_structure: {smiles, title}

CS:
- tree_graph: {nodes: [{id,label}], edges: [{from,to,weight}], directed, layout: tree|spring|circular, title}
"""
