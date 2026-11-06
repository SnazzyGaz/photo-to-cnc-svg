"""Regression tests. Run from the repo root: pytest -q"""
import json, os, subprocess, sys
import cv2, numpy as np, pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.path.join(ROOT, 'scripts', 'cnc_vector.py')
PREVIEW = os.path.join(ROOT, 'scripts', 'preview.py')
EX = os.path.join(ROOT, 'examples')

def run(*args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    return r

def trace(tmp_path, src, *flags, name='out.svg'):
    out = tmp_path / name
    r = run(TRACE, src, '-o', out, *flags)
    assert r.returncode == 0, r.stderr
    return out, json.loads(r.stdout)

def black(png):
    return (cv2.imread(str(png), cv2.IMREAD_GRAYSCALE) < 128).mean()

def test_fisherman_reproduces(tmp_path):
    """README promise: option B of the old fisherman traces to 292 paths, ~39 min."""
    src = os.path.join(EX, 'old-fisherman', 'option-b.jpg')
    _, st = trace(tmp_path, src, '--mode', 'vcarve', '--width-mm', 300, '--vbit-angle', 60, '--depth', 3,
                  '--threshold', 128, '--smooth', 0.8, '--min-feature', 0.5)
    ref = json.load(open(os.path.join(EX, 'old-fisherman', 'stats.json')))
    assert ref['paths'] == 292
    if os.environ.get('LOOSE') == '1':  # unpinned deps: same picture, path count may wobble a little
        assert st['paths'] == pytest.approx(292, rel=0.05)
    else:  # requirements-lock.txt: exact
        assert st['paths'] == 292
    assert st['estimate']['time_min'] == pytest.approx(ref['estimate']['time_min'], rel=0.05)

@pytest.mark.parametrize('flags', [
    ['--mode', 'engrave', '--width-mm', 100, '--depth', 1],
    ['--mode', 'pocket', '--width-mm', 150, '--levels', 3, '--depth', 6],
    ['--mode', 'profile', '--width-mm', 150, '--single', '--depth', 6],
])
def test_modes_run_and_preview(tmp_path, flags):
    src = os.path.join(EX, 'red-fox', 'option-a.jpg')
    png = tmp_path / 'p.png'
    _, st = trace(tmp_path, src, *flags, '--preview', png)
    assert st['paths'] > 0 and 'estimate' in st
    assert 0.001 < black(png) < 0.9

def test_border_does_not_invert_preview(tmp_path):
    src = os.path.join(EX, 'red-fox', 'option-a.jpg')
    plain, _ = trace(tmp_path, src, '--mode', 'vcarve', '--width-mm', 200, '--threshold', 128, name='a.svg')
    framed, _ = trace(tmp_path, src, '--mode', 'vcarve', '--width-mm', 200, '--threshold', 128, '--border', 10, name='b.svg')
    pa, pb = tmp_path / 'a.png', tmp_path / 'b.png'
    assert run(PREVIEW, plain, pa).returncode == 0 and run(PREVIEW, framed, pb).returncode == 0
    a, b = black(pa), black(pb)
    # the 10 mm frame shrinks the art to 200/220 of the width; carved area must shrink with it, not invert
    assert b == pytest.approx(a * (200 / 220) ** 2, rel=0.1)

def test_bad_crop_is_a_clear_error(tmp_path):
    r = run(TRACE, os.path.join(EX, 'red-fox', 'option-a.jpg'), '-o', tmp_path / 'x.svg',
            '--mode', 'vcarve', '--width-mm', 50, '--crop', '0.9,0.9,0.1,0.1')
    assert r.returncode != 0 and 'empty box' in r.stderr and 'Traceback' not in r.stderr
