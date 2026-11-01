#!/usr/bin/env python3
"""preview.py - render a cnc_vector.py SVG as a true-to-cut PNG preview.

The SVG holds regions as separate outline paths. Filling them one by one makes
holes look solid, so this merges every path into one even-odd fill: black is
what gets carved, white is what stays.

Usage: python3 preview.py in.svg out.png [--width 1600]
"""
import argparse, re
import cairosvg

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('svg'); p.add_argument('png')
    p.add_argument('--width', type=int, default=1600, help='output width in px (default 1600)')
    a = p.parse_args()
    s = open(a.svg, encoding='utf-8').read()
    ds = re.findall(r'<path d="([^"]+)"', s)
    if not ds:
        raise SystemExit('no <path d="..."> elements found in ' + a.svg)
    head = s.split('<g')[0]
    svg = (head + '<rect width="100%" height="100%" fill="white"/>'
           '<path fill="black" fill-rule="evenodd" d="' + ' '.join(ds) + '"/></svg>')
    cairosvg.svg2png(bytestring=svg.encode(), write_to=a.png, output_width=a.width)
    print(f'{a.png}: {len(ds)} paths merged, {a.width}px wide')

if __name__ == '__main__':
    main()
