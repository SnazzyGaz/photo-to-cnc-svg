#!/usr/bin/env python3
"""cnc_vector.py - photo/region -> clean, CNC-ready SVG (mm units).

Modes:
  vcarve   closed filled regions for V-bit carving
  pocket   closed regions, geometry constrained to end-mill diameter; optional multi-level
  engrave  single-line centreline paths (open polylines -> smooth curves)
  profile  outer silhouette only, for cutting the shape free

Deps: numpy scipy opencv-python-headless scikit-image potracer cairosvg
"""
import argparse, json, math, sys
import numpy as np, cv2
import potrace
from skimage.morphology import skeletonize

# ---------------------------------------------------------------- helpers
def disk(r_px):
    r = max(1, int(round(r_px)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def remove_small(mask, min_area_px):
    """Drop specks AND fill tiny holes (both are machining noise)."""
    out = mask.copy()
    for target in (1, 0):  # 1: specks of material, 0: pin holes
        m = (out == target).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < min_area_px:
                out[lab == i] = 1 - target
    return out

def parse_crop(s, w, h):
    v = [float(x) for x in s.split(',')]
    if all(0 <= x <= 1 for x in v):  # fractions
        v = [v[0] * w, v[1] * h, v[2] * w, v[3] * h]
    x0, y0, x1, y1 = [int(round(x)) for x in v]
    return max(0, x0), max(0, y0), min(w, x1), min(h, y1)

# ---------------------------------------------------------------- image -> mask
def load_and_prepare(a):
    img = cv2.imread(a.input, cv2.IMREAD_UNCHANGED)
    if img is None:
        sys.exit(f"cannot read {a.input}")
    alpha = None
    if img.ndim == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        img = img[:, :, :3]
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    h, w = img.shape[:2]
    isolate = None
    if a.crop:
        x0, y0, x1, y1 = parse_crop(a.crop, w, h)
        if a.isolate:  # GrabCut the subject inside the box, then crop
            m = np.zeros((h, w), np.uint8)
            bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
            cv2.grabCut(img, m, (x0, y0, x1 - x0, y1 - y0), bg, fg, 6, cv2.GC_INIT_WITH_RECT)
            isolate = np.where((m == 1) | (m == 3), 1, 0).astype(np.uint8)[y0:y1, x0:x1]
        img = img[y0:y1, x0:x1]
        if alpha is not None:
            alpha = alpha[y0:y1, x0:x1]
    if alpha is not None and isolate is None:
        isolate = (alpha > 127).astype(np.uint8)
    return img, isolate

def working_scale(a, h, w):
    """Choose output size (mm) and raster px/mm so the smallest cuttable feature spans >= ~6 px."""
    aspect = w / h
    W, H = a.width_mm, a.height_mm
    if W and H:  # fit inside box, keep aspect
        if W / H > aspect: W = H * aspect
        else: H = W / aspect
    elif W: H = W / aspect
    elif H: W = H * aspect
    else: sys.exit("give --width-mm and/or --height-mm")
    ppm = min(max(6.0 / a.min_feature, 8.0), 3000.0 / max(W, H))
    return W, H, ppm

def tone_mask(gray, a):
    """1 = material to cut (dark by default)."""
    g = gray
    if a.smooth > 0:  # edge-preserving denoise, kills photo grain
        d = int(a.smooth * 4) | 1
        g = cv2.bilateralFilter(g, d, 40 + a.smooth * 15, d)
        g = cv2.GaussianBlur(g, (0, 0), a.smooth * 0.6)
    if a.threshold == 'auto':
        _, m = cv2.threshold(g, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    elif a.threshold == 'adaptive':
        bs = int(max(g.shape) / 12) | 1
        m = cv2.adaptiveThreshold(g, 1, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, bs, 6)
    else:
        _, m = cv2.threshold(g, int(a.threshold), 1, cv2.THRESH_BINARY_INV)
    if a.invert:
        m = 1 - m
    return m.astype(np.uint8)

def make_tool_safe(m, a, ppm, mode):
    tool_r = a.tool_dia / 2 * ppm
    feat_r = a.min_feature / 2 * ppm
    min_area = (a.min_feature * ppm) ** 2 * 4
    # close first (bridges hairline gaps), then open (removes slivers)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(feat_r * 0.5))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, disk(feat_r * 0.5))
    if mode == 'pocket':
        # anything narrower than the end mill cannot be cleared -> remove it;
        # this also rounds inside corners to tool radius automatically
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, disk(tool_r))
        # islands left standing must be at least min_feature wide
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(feat_r))
    if mode == 'profile':
        # tool runs outside the part: concave corners get tool radius
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(tool_r))
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        keep = np.zeros_like(m)
        if cnts:
            if a.single:
                cnts = [max(cnts, key=cv2.contourArea)]
            cv2.drawContours(keep, cnts, -1, 1, thickness=-1)  # fill holes
        m = keep
    m = remove_small(m, min_area)
    return m

# ---------------------------------------------------------------- tracing
def trace_regions(m, ppm, a):
    """Potrace -> list of closed Bezier path strings in mm."""
    bm = potrace.Bitmap(~m.astype(bool))  # potracer: True=white/background
    turd = int((a.min_feature * ppm) ** 2)
    plist = bm.trace(turdsize=turd, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                     alphamax=a.alphamax, opticurve=True, opttolerance=a.opttol)
    s = 1.0 / ppm
    paths, nodes = [], 0
    for curve in plist:
        st = curve.start_point
        d = [f"M{st.x*s:.3f},{st.y*s:.3f}"]
        for seg in curve.segments:
            nodes += 1
            if seg.is_corner:
                d.append(f"L{seg.c.x*s:.3f},{seg.c.y*s:.3f}L{seg.end_point.x*s:.3f},{seg.end_point.y*s:.3f}")
            else:
                d.append(f"C{seg.c1.x*s:.3f},{seg.c1.y*s:.3f} {seg.c2.x*s:.3f},{seg.c2.y*s:.3f} {seg.end_point.x*s:.3f},{seg.end_point.y*s:.3f}")
        d.append("Z")
        paths.append(((st.x * s, st.y * s), "".join(d)))
    return paths, nodes

def skeleton_polylines(m, ppm, a):
    """Centreline graph -> pruned, simplified polylines (in px)."""
    sk = skeletonize(m.astype(bool)).astype(np.uint8)
    H, W = sk.shape
    nbrs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    pts = set(zip(*np.nonzero(sk)))
    def nb(p):
        return [(p[0] + dy, p[1] + dx) for dy, dx in nbrs if (p[0] + dy, p[1] + dx) in pts]
    deg = {p: len(nb(p)) for p in pts}
    nodes = {p for p, d in deg.items() if d != 2}
    seen_edges, lines = set(), []
    def walk(a0, b0):
        line = [a0, b0]; prev, cur = a0, b0
        while cur not in nodes:
            nxt = [q for q in nb(cur) if q != prev and (min(cur, q), max(cur, q)) not in seen_edges]
            if not nxt: break
            seen_edges.add((min(cur, nxt[0]), max(cur, nxt[0])))
            prev, cur = cur, nxt[0]; line.append(cur)
        return line
    for n0 in nodes:
        for q in nb(n0):
            e = (min(n0, q), max(n0, q))
            if e in seen_edges: continue
            seen_edges.add(e)
            lines.append(walk(n0, q))
    # pure loops (no nodes)
    rest = {p for p in pts if p not in nodes and all((min(p, q), max(p, q)) not in seen_edges for q in nb(p))}
    while rest:
        p = rest.pop(); q = nb(p)[0]
        seen_edges.add((min(p, q), max(p, q)))
        l = walk(p, q); l.append(p); lines.append(l)
        rest -= set(l)
    # prune short spurs (one end free) iteratively
    min_len = a.min_feature * ppm * 3
    for _ in range(3):
        endcount = {}
        for l in lines:
            for e in (l[0], l[-1]): endcount[e] = endcount.get(e, 0) + 1
        lines = [l for l in lines if not (len(l) < min_len and (endcount[l[0]] == 1 or endcount[l[-1]] == 1)
                                          and not (endcount[l[0]] == 1 and endcount[l[-1]] == 1 and len(l) > min_len / 2))]
    lines = join_gaps(lines, 0.5)  # merge chains meeting at junctions
    lines = join_gaps(lines, a.min_feature * ppm * 1.5)
    out = []
    win = max(3, int(a.min_feature * ppm * 1.2) | 1)
    for l in lines:
        arr = np.array([[p[1], p[0]] for p in l], np.float32)
        closed = len(l) > 3 and l[0] == l[-1]
        if cv2.arcLength(arr.reshape(-1, 1, 2), False) < min_len: continue
        arr = smooth_poly(arr, win, closed).astype(np.float32)  # kill pixel stair-steps before simplifying
        eps = max(0.6, a.min_feature * ppm * 0.12 * (a.opttol / 0.4))
        simp = cv2.approxPolyDP(arr.reshape(-1, 1, 2), eps, closed).reshape(-1, 2)
        if len(simp) >= 2:
            if closed: simp = np.vstack([simp, simp[:1]])
            out.append((simp, closed))
    return out

def smooth_poly(arr, win, closed):
    if len(arr) < win + 2: return arr
    k = np.ones(win) / win; h = win // 2
    if closed:
        body = arr[:-1] if (arr[0] == arr[-1]).all() else arr
        ext = np.vstack([body[-h:], body, body[:h]])
        sm = np.column_stack([np.convolve(ext[:, i], k, 'valid') for i in range(2)])
        return np.vstack([sm, sm[:1]])
    ext = np.vstack([np.repeat(arr[:1], h, 0), arr, np.repeat(arr[-1:], h, 0)])
    sm = np.column_stack([np.convolve(ext[:, i], k, 'valid') for i in range(2)])
    sm[0], sm[-1] = arr[0], arr[-1]
    return sm

def join_gaps(lines, gap):
    """Bridge free endpoints that nearly touch so the bit doesn't lift for a tiny hop (KD-tree, greedy)."""
    from scipy.spatial import cKDTree
    if len(lines) < 2: return lines
    pts = np.array([l[e] for l in lines for e in (0, -1)], float)
    isfree = np.array([l[0] != l[-1] for l in lines for _ in (0, 1)])
    pairs = cKDTree(pts).query_pairs(gap, output_type='ndarray')
    if len(pairs) == 0: return lines
    dist = np.linalg.norm(pts[pairs[:, 0]] - pts[pairs[:, 1]], axis=1)
    parent = list(range(len(lines)))
    def root(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    partner = {}
    for k in np.argsort(dist):
        a_, b_ = pairs[k]
        if not (isfree[a_] and isfree[b_]) or a_ in partner or b_ in partner: continue
        ra, rb = root(a_ // 2), root(b_ // 2)
        if ra == rb: continue
        parent[ra] = rb; partner[a_] = b_; partner[b_] = a_
    out, used = [], set()
    for i in range(len(lines)):
        if i in used: continue
        e0 = 2 * i if (2 * i) not in partner else (2 * i + 1 if (2 * i + 1) not in partner else None)
        if e0 is None: continue  # middle of a chain; reached from its head
        chain, cur = [], e0
        while True:
            li = cur // 2; used.add(li)
            seg = lines[li] if cur % 2 == 0 else lines[li][::-1]
            chain += seg[1:] if chain and chain[-1] == seg[0] else seg
            o = cur ^ 1
            if o not in partner: break
            cur = partner[o]
        out.append(chain)
    return out

def catmull_rom_path(pts, closed, s):
    """Smooth polyline -> cubic Bezier through the same points (C1-continuous, few nodes)."""
    P = [tuple(p) for p in pts]
    if closed and P[0] == P[-1]: P = P[:-1]
    n = len(P)
    f = lambda p: f"{p[0]*s:.3f},{p[1]*s:.3f}"
    if n < 3:
        return "M" + f(P[0]) + "".join("L" + f(p) for p in P[1:]) + ("Z" if closed else "")
    d = ["M" + f(P[0])]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1)} {f(c2)} {f(p2)}")
    if closed: d.append("Z")
    return "".join(d)

def order_paths(items):
    """Greedy nearest-neighbour ordering of (start, end, d) to cut rapid travel."""
    if not items: return [], 0.0
    rem = items[:]; out = []; cur = (0.0, 0.0); travel = 0.0
    while rem:
        k = min(range(len(rem)), key=lambda i: (rem[i][0][0] - cur[0]) ** 2 + (rem[i][0][1] - cur[1]) ** 2)
        it = rem.pop(k); travel += math.dist(cur, it[0]); out.append(it[2]); cur = it[1]
    return out, travel

# ---------------------------------------------------------------- estimate
def region_stats(m, ppm):
    """Per connected region: (area mm2, perimeter mm incl. holes)."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        sub = np.pad(sub, 1)
        cnts, _ = cv2.findContours(sub, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        per = sum(cv2.arcLength(c, True) for c in cnts)
        out.append((area / ppm ** 2, per / ppm * 0.92))  # 0.92: pixel-staircase correction
    return out

def estimate(a, geo, ppm, nlevels):
    """Rough machining estimate. Real numbers come from the CAM; expect +/-30%."""
    D = a.tool_dia
    tan = math.tan(math.radians(a.vbit_angle / 2))
    pd = a.pass_depth or (a.depth if a.mode == 'vcarve' else D / 2)
    cut = plunges = travel = 0.0; notes = []
    for li, (name, m, polys, tr) in enumerate(geo):
        if a.mode == 'engrave':
            passes = math.ceil(a.depth / pd)
            cut += sum(polys) * passes; plunges += len(polys) * passes; travel += tr
        elif a.mode == 'profile':
            passes = math.ceil(a.depth / pd)
            for A, P in region_stats(m, ppm):
                cut += (P + math.pi * D) * passes; plunges += passes
            travel += tr
        elif a.mode == 'pocket':
            step = a.depth / nlevels; passes = math.ceil(step / pd)
            for A, P in region_stats(m, ppm):
                cut += (A / (a.stepover * D) + P) * passes; plunges += passes
            travel += tr * passes
        else:  # vcarve: strip model, width ~ 2A/P per region
            for A, P in region_stats(m, ppm):
                w = 2 * A / max(P, 1e-6)
                z = min(w / 2 / tan, a.depth); wv = 2 * z * tan
                passes = math.ceil(z / pd) if a.pass_depth else 1
                if w <= wv * 1.05: path = P / 2              # pure V: one centreline sweep
                else: path = A / max(wv * a.stepover, 0.2) + P  # flat-bottom clearing with the V-bit
                cut += path * passes; plunges += passes
            travel += tr
            notes.append('flat areas wider than %.1f mm hit max depth: CAM will want a clearance end mill there' % (2 * a.depth * tan))
    plunge_t = plunges * (pd / a.plunge + 2 * a.safe_z / a.rapid)
    mins = (cut / a.feed + travel / a.rapid + plunge_t) * 1.15  # accel/decel overhead
    return {'plunges': int(plunges), 'cut_length_m': round(cut / 1000, 2), 'rapid_travel_m': round(travel / 1000, 2),
            'pass_depth_mm': round(pd, 2), 'time_min': round(mins, 1),
            'time_range_min': [round(mins * 0.7, 1), round(mins * 1.3, 1)],
            'assumes': f'feed {a.feed} plunge {a.plunge} rapid {a.rapid} mm/min, safe Z {a.safe_z} mm, stepover {a.stepover}',
            'notes': notes}

# ---------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser()
    p.add_argument('input'); p.add_argument('-o', '--out', required=True)
    p.add_argument('--mode', choices=['vcarve', 'pocket', 'engrave', 'profile'], required=True)
    p.add_argument('--width-mm', type=float); p.add_argument('--height-mm', type=float)
    p.add_argument('--tool-dia', type=float, default=3.175, help='end mill / profile tool diameter mm')
    p.add_argument('--min-feature', type=float, default=None, help='smallest kept detail mm')
    p.add_argument('--crop', help='x0,y0,x1,y1 in px or 0-1 fractions')
    p.add_argument('--isolate', action='store_true', help='GrabCut subject inside --crop box')
    p.add_argument('--threshold', default='auto', help="auto | adaptive | 0-255")
    p.add_argument('--invert', action='store_true', help='cut the light areas instead of dark')
    p.add_argument('--use-isolation-as-mask', action='store_true', help='silhouette = isolated subject')
    p.add_argument('--levels', type=int, default=1, help='pocket: number of depth levels')
    p.add_argument('--smooth', type=float, default=2.0, help='0-5 denoise strength')
    p.add_argument('--alphamax', type=float, default=1.1, help='potrace corner smoothness 0-1.33')
    p.add_argument('--opttol', type=float, default=0.4, help='curve simplification tolerance (px)')
    p.add_argument('--lines', choices=['dark', 'edges'], default='dark', help='engrave source')
    p.add_argument('--single', action='store_true', help='profile: keep largest outline only')
    p.add_argument('--border', type=float, default=0, help='add rectangular profile border, margin mm')
    p.add_argument('--preview', help='write PNG preview')
    g = p.add_argument_group('job estimate (all optional; mm and mm/min)')
    g.add_argument('--depth', type=float, help='total cut depth (vcarve: max/flat depth)')
    g.add_argument('--pass-depth', type=float, help='depth per pass (default = tool dia/2, vcarve = depth)')
    g.add_argument('--feed', type=float, default=1200); g.add_argument('--plunge', type=float, default=300)
    g.add_argument('--rapid', type=float, default=3000); g.add_argument('--safe-z', type=float, default=5)
    g.add_argument('--stepover', type=float, default=0.4, help='fraction of tool/V width')
    g.add_argument('--vbit-angle', type=float, default=60)
    a = p.parse_args()
    if a.min_feature is None:
        a.min_feature = {'vcarve': 0.6, 'pocket': a.tool_dia, 'engrave': 0.8, 'profile': a.tool_dia}[a.mode]

    img, iso = load_and_prepare(a)
    h0, w0 = img.shape[:2]
    W, H, ppm = working_scale(a, h0, w0)
    size = (int(round(W * ppm)), int(round(H * ppm)))
    img = cv2.resize(img, size, interpolation=cv2.INTER_AREA if size[0] < w0 else cv2.INTER_CUBIC)
    if iso is not None:
        iso = cv2.resize(iso, size, interpolation=cv2.INTER_NEAREST)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(2.0, (8, 8)).apply(gray)

    layers, stats = [], {'mode': a.mode, 'size_mm': [round(W, 2), round(H, 2)], 'px_per_mm': round(ppm, 2),
                         'min_feature_mm': a.min_feature, 'tool_dia_mm': a.tool_dia}
    total_nodes = 0; total_travel = 0.0; npaths = 0
    geo = []  # (layer, mask|None, polylines_mm|None, travel)

    if a.mode == 'engrave':
        if a.lines == 'edges':
            g = cv2.bilateralFilter(gray, 9, 60, 9)
            e = cv2.Canny(g, 40, 110)
            m = cv2.dilate(e, disk(a.min_feature * ppm * 0.4)) // 255
        else:
            m = tone_mask(gray, a)
        if iso is not None: m = m * iso
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, disk(a.min_feature * ppm * 0.4))
        m = remove_small(m, (a.min_feature * ppm) ** 2 * 3)
        polys = skeleton_polylines(m, ppm, a)
        s = 1 / ppm
        items = []
        for pts, closed in polys:
            d = catmull_rom_path(pts, closed, s)
            items.append(((pts[0][0] * s, pts[0][1] * s), (pts[-1][0] * s, pts[-1][1] * s), d))
            total_nodes += len(pts)
        ds, total_travel = order_paths(items); npaths = len(ds)
        layers.append(('engrave', ds, False))
        geo.append(('engrave', None, [cv2.arcLength(np.float32(p).reshape(-1, 1, 2), False) / ppm for p, _ in polys], total_travel))
        stats['open_paths'] = sum(1 for _, c in polys if not c)
    else:
        if a.use_isolation_as_mask and iso is not None:
            base = iso
        else:
            base = tone_mask(gray, a)
            if iso is not None: base = base * iso
        if a.mode == 'pocket' and a.levels > 1:
            g = cv2.bilateralFilter(gray, 9, 60, 9)
            if iso is not None: g = np.where(iso > 0, g, 255).astype(np.uint8)
            edges = np.quantile(g[g < 255] if (g < 255).any() else g, np.linspace(0, 1, a.levels + 2)[1:-1])
            masks = [(g <= t).astype(np.uint8) for t in edges[::-1]]  # shallow->deep, nested
        else:
            masks = [base]
        for li, m in enumerate(masks):
            m = make_tool_safe(m.astype(np.uint8), a, ppm, a.mode)
            paths, n = trace_regions(m, ppm, a); total_nodes += n
            items = [(st, st, d) for st, d in paths]
            ds, tr = order_paths(items); total_travel += tr; npaths += len(ds)
            name = a.mode if len(masks) == 1 else f"pocket_level_{li+1}"
            layers.append((name, ds, True))
            geo.append((name, m, None, tr))
    if a.border > 0:
        b = a.border
        layers.append(('profile_border', [f"M{-b:.3f},{-b:.3f}H{W+b:.3f}V{H+b:.3f}H{-b:.3f}Z"], True))

    ox = oy = a.border
    TW, TH = W + 2 * a.border, H + 2 * a.border
    colors = ['#000000', '#d62728', '#1f77b4', '#2ca02c', '#9467bd', '#ff7f0e']
    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{TW:.3f}mm" height="{TH:.3f}mm" viewBox="0 0 {TW:.3f} {TH:.3f}">',
           f'<!-- CNC vector | mode={a.mode} tool={a.tool_dia}mm min_feature={a.min_feature}mm | units: mm -->']
    for i, (name, ds, closed) in enumerate(layers):
        out.append(f'<g id="{name}" fill="none" stroke="{colors[i % len(colors)]}" stroke-width="0.1" transform="translate({ox:.3f},{oy:.3f})">')
        out += [f'<path d="{d}"/>' for d in ds]
        out.append('</g>')
    out.append('</svg>')
    open(a.out, 'w').write("\n".join(out))
    stats.update({'paths': npaths, 'nodes': total_nodes, 'rapid_travel_mm_est': round(total_travel, 1),
                  'layers': [l[0] for l in layers]})
    if a.depth:
        stats['estimate'] = estimate(a, geo, ppm, len(masks) if a.mode == 'pocket' else 1)
    if a.preview:
        import cairosvg
        svg = "\n".join(out)
        if a.mode != 'engrave':  # show cut regions solid, even-odd so holes read correctly
            for k, shade in enumerate(['#bbb', '#888', '#555', '#222', '#000'][-len(layers):] if len(layers) > 1 else ['#000']):
                svg = svg.replace('fill="none"', f'fill="{shade}" fill-rule="evenodd"', 1)
        svg = svg.replace('stroke-width="0.1"', 'stroke-width="0.35"')
        cairosvg.svg2png(bytestring=svg.encode(), write_to=a.preview, output_width=1200, background_color='white')
    print(json.dumps(stats, indent=1))

if __name__ == '__main__':
    main()
