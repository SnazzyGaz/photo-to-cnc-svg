#!/usr/bin/env python3
"""preview.py - render a cnc_vector.py SVG as a true-to-cut PNG preview.

Closed regions are merged into one even-odd fill, so holes read correctly:
black is what gets carved, white is what stays. Open paths (engrave mode) are
drawn as lines. The profile border layer is shown as a thin grey outline, not
filled. Pure OpenCV/numpy: no Cairo needed.

Usage: python3 preview.py in.svg out.png [--width 1600]
"""
import argparse, re, sys
import numpy as np, cv2

_NUM = r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?'
_TOK = re.compile(r'[MLHVCZmlhvcz]|' + _NUM)

def parse_path(d, steps=12):
    """Absolute M/L/H/V/C/Z path -> list of (points Nx2 float, closed)."""
    toks = _TOK.findall(d)
    subs, cur, pos, start, i, cmd = [], [], (0.0, 0.0), (0.0, 0.0), 0, None
    t = np.linspace(0, 1, steps + 1)[1:, None]
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]; i += 1
            if cmd.islower():
                raise ValueError('relative path commands are not supported: ' + cmd)
        if cmd == 'M':
            if len(cur) > 1: subs.append((np.array(cur), False))
            pos = start = (num(), num()); cur = [pos]; cmd = 'L'
        elif cmd == 'L':
            pos = (num(), num()); cur.append(pos)
        elif cmd == 'H':
            pos = (num(), pos[1]); cur.append(pos)
        elif cmd == 'V':
            pos = (pos[0], num()); cur.append(pos)
        elif cmd == 'C':
            p0 = np.array(pos); c1 = np.array([num(), num()]); c2 = np.array([num(), num()]); p3 = np.array([num(), num()])
            b = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p3
            cur += [tuple(q) for q in b]; pos = tuple(p3)
        elif cmd == 'Z':
            if len(cur) > 2: subs.append((np.array(cur), True))
            cur = []; pos = start
        else:
            raise ValueError('unexpected token in path: ' + toks[i])
    if len(cur) > 1: subs.append((np.array(cur), False))
    return subs

def render(svg_text, out_png, width=1600, supersample=3):
    """Render SVG text from cnc_vector.py to a PNG. Returns (n_paths, size)."""
    vb = re.search(r'viewBox="([^"]+)"', svg_text)
    if not vb:
        raise SystemExit('SVG has no viewBox')
    x0, y0, vw, vh = (float(v) for v in vb.group(1).split())
    W = width * supersample
    s = W / vw
    H = int(round(vh * s))
    fill = np.zeros((H, W), np.uint8)
    lines = np.zeros((H, W), np.uint8)
    border = np.zeros((H, W), np.uint8)
    n = 0
    for gm in re.finditer(r'<g\b([^>]*)>(.*?)</g>', svg_text, re.S):
        attrs, body = gm.groups()
        gid = re.search(r'id="([^"]*)"', attrs)
        tr = re.search(r'translate\(\s*(' + _NUM + r')[ ,]+(' + _NUM + r')\s*\)', attrs)
        ox, oy = (float(tr.group(1)), float(tr.group(2))) if tr else (0.0, 0.0)
        is_border = gid is not None and gid.group(1) == 'profile_border'
        closed_polys = []
        for d in re.findall(r'<path d="([^"]+)"', body):
            n += 1
            for pts, closed in parse_path(d):
                px = np.round((pts + (ox - x0, oy - y0)) * s).astype(np.int32)
                if is_border:
                    cv2.polylines(border, [px], closed, 255, max(1, supersample))
                elif closed:
                    closed_polys.append(px)
                else:
                    cv2.polylines(lines, [px], False, 255, max(1, int(round(0.35 * s))), cv2.LINE_AA)
        if closed_polys:  # one call per layer: overlapping contours toggle (even-odd)
            layer = np.zeros((H, W), np.uint8)
            cv2.fillPoly(layer, closed_polys, 255)
            fill = np.maximum(fill, layer)
    if n == 0:
        raise SystemExit('no <path d="..."> elements found')
    img = 255 - np.maximum(fill, lines)
    img = np.where(border > 0, np.minimum(img, 150), img).astype(np.uint8)
    img = cv2.resize(img, (width, max(1, int(round(H / supersample)))), interpolation=cv2.INTER_AREA)
    if not cv2.imwrite(out_png, img):
        raise SystemExit('cannot write ' + out_png)
    return n, img.shape[::-1]

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('svg'); p.add_argument('png')
    p.add_argument('--width', type=int, default=1600, help='output width in px (default 1600)')
    a = p.parse_args()
    n, (w, h) = render(open(a.svg, encoding='utf-8').read(), a.png, a.width)
    print(f'{a.png}: {n} paths, {w}x{h}px')

if __name__ == '__main__':
    main()
