#!/usr/bin/env python3
"""
colourful-research-charts :: renderer

Turns a CSV (or inline values) into one self-contained HTML file containing a
hand-built SVG chart: real axes, tick labels, axis titles, a title, a caption,
and the value / count printed on every mark.

Standard library only. No matplotlib, no Node, no network, no API key.

    python3 render.py bar          --data f.csv --x group [--y score] [--agg mean]
    python3 render.py grouped-bar  --data f.csv --x group --y score --series wave
    python3 render.py line         --data f.csv --x time --y score [--group arm]
    python3 render.py area         --data f.csv --x time --y score [--group arm]
    python3 render.py histogram    --data f.csv --x score [--bins 8]
    python3 render.py scatter      --data f.csv --x pre --y post [--group arm]
    python3 render.py boxplot      --data f.csv --x group --y score
    python3 render.py radar        --data f.csv --x dim --y score [--group arm]
    python3 render.py pie          --data f.csv --x group [--y score]
    python3 render.py donut        --data f.csv --x group [--y score]
    python3 render.py heatmap      --data f.csv --x row --series col --y value
    python3 render.py funnel       --data f.csv --x stage [--y value]
    python3 render.py flowchart    --data f.csv --x step [--cols 4]
    python3 render.py gantt        --data f.csv --x task --start begin --end finish

    python3 render.py list
"""

import argparse
import csv
import datetime
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------- colour ----

def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(round(v)))) for v in c)


def mix(a, b, t):
    ra, rb = hex2rgb(a), hex2rgb(b)
    return rgb2hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def lum(h):
    r, g, b = hex2rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def on(bg):
    """Readable text colour on top of a filled shape."""
    return '#FFFFFF' if lum(bg) < 0.60 else '#2B2521'


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ------------------------------------------------------------ palette/font ----

def _load(fn):
    with open(os.path.join(HERE, fn), encoding='utf-8') as f:
        return json.load(f)


def get_palette(name=None):
    d = _load('palettes.json')['palettes']
    keys = list(d.keys())
    picked = (not name) or name == 'random'
    if picked:
        name = random.choice(keys)
    if name not in d:
        raise SystemExit('Unknown palette %r. Known: %s' % (name, ', '.join(keys)))
    p = dict(d[name])
    p['key'] = name
    p['picked'] = 'random' if picked else 'fixed'
    p['muted'] = mix(p['text'], p['ground'], 0.42)
    p['grid'] = mix(p['ground'], p['text'], 0.14)
    p['track'] = mix(p['ground'], p['text'], 0.07)
    return p


def theme(a):
    """Load the palette and font, and publish the body font for SVG text."""
    global FONT_BODY_ESC
    pal = get_palette(a.palette)
    font = get_font(a.font)
    FONT_BODY_ESC = font['body'].replace('"', "'")
    return pal, font


def get_font(name=None):
    d = _load('fonts.json')['pairings']
    picked = (not name) or name == 'random'
    if picked:
        name = random.choice([p['name'] for p in d])
    for p in d:
        if p['name'] == name:
            f = dict(p)
            f['picked'] = 'random' if picked else 'fixed'
            return f
    raise SystemExit('Unknown font %r. Known: %s' % (name, ', '.join(p['name'] for p in d)))


# ------------------------------------------------------------------ ticks ----

def nice_ticks(vmin, vmax, target=5):
    if vmax <= vmin:
        vmax = vmin + 1.0
    raw = (vmax - vmin) / float(target)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
    step = 10 * mag
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag + 1e-12:
            step = m * mag
            break
    start = math.floor(vmin / step) * step
    end = math.ceil(vmax / step) * step
    out, v, k = [], start, 0
    while v <= end + step * 1e-9 and k < 60:
        out.append(round(v, 10))
        v += step
        k += 1
    return out, start, end


def fmt(v, dp=1):
    v = float(v)
    if abs(v - round(v)) < 1e-9 and abs(v) < 1e7:
        return str(int(round(v)))
    if abs(v) >= 1000:
        return '{:,.1f}'.format(v)
    return '{:.{dp}f}'.format(v, dp=dp)


# ------------------------------------------------------------------- data ----

def read_rows(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        s = str(v).strip()
        if s == '':
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def pairs_from(values):
    """--values "A:10,B:20" -> [('A', 10.0), ...]"""
    out = []
    for chunk in values.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ':' in chunk:
            k, v = chunk.rsplit(':', 1)
        else:
            k, v = chunk, '1'
        out.append((k.strip(), num(v) if num(v) is not None else 0.0))
    return out


def agg(vals, how):
    vals = [v for v in vals if v is not None]
    if not vals:
        return 0.0, 0
    if how == 'sum':
        return float(sum(vals)), len(vals)
    if how == 'count':
        return float(len(vals)), len(vals)
    if how == 'median':
        s = sorted(vals)
        n = len(s)
        return (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0), n
    return float(sum(vals)) / len(vals), len(vals)


# ------------------------------------------------------------------ canvas ----

class Fig(object):
    def __init__(self, w=940, h=580, m=None):
        self.w, self.h = w, h
        self.m = m or dict(l=92, r=36, t=58, b=92)
        self.p = []

    @property
    def pw(self):
        return self.w - self.m['l'] - self.m['r']

    @property
    def ph(self):
        return self.h - self.m['t'] - self.m['b']

    @property
    def x0(self):
        return self.m['l']

    @property
    def y0(self):
        return self.m['t']

    def add(self, s):
        self.p.append(s)

    def out(self):
        return ('<svg viewBox="0 0 %d %d" width="100%%" role="img" '
                'xmlns="http://www.w3.org/2000/svg" font-family="%s">'
                % (self.w, self.h, FONT_BODY_ESC)) + ''.join(self.p) + '</svg>'


FONT_BODY_ESC = "sans-serif"


def frame(f, pal, title=None):
    """Optional soft plot background."""
    f.add('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" rx="14"/>'
          % (f.x0, f.y0, f.pw, f.ph, pal['track']))


def y_axis(f, pal, ticks, vmin, vmax, label, dp=1):
    ph, x0, y0, pw = f.ph, f.x0, f.y0, f.pw
    for t in ticks:
        y = y0 + ph - (t - vmin) / float(vmax - vmin) * ph
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (x0, y, x0 + pw, y, pal['grid']))
        f.add('<text x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle" '
              'font-size="15" fill="%s">%s</text>'
              % (x0 - 10, y, pal['muted'], fmt(t, dp)))
    f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
          % (x0, y0, x0, y0 + ph, pal['muted']))
    if label:
        cx, cy = x0 - 58, y0 + ph / 2.0
        f.add('<text x="%.1f" y="%.1f" transform="rotate(-90 %.1f %.1f)" text-anchor="middle" '
              'font-size="18" font-weight="600" fill="%s">%s</text>'
              % (cx, cy, cx, cy, pal['text'], esc(label)))


def x_axis_line(f, pal):
    f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
          % (f.x0, f.y0 + f.ph, f.x0 + f.pw, f.y0 + f.ph, pal['muted']))


def x_cat_labels(f, pal, cats, cx):
    """Category tick labels under a bar-style axis."""
    longest = max(len(str(c)) for c in cats) if cats else 0
    fs = 16 if longest <= 12 else 14
    for c, x in zip(cats, cx):
        if longest > 10:
            f.add('<text x="%.1f" y="%.1f" transform="rotate(-28 %.1f %.1f)" text-anchor="end" '
                  'font-size="%d" fill="%s">%s</text>'
                  % (x, f.y0 + f.ph + 20, x, f.y0 + f.ph + 20, fs, pal['text'], esc(c)))
        else:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%d" fill="%s">%s</text>'
                  % (x, f.y0 + f.ph + 22, fs, pal['text'], esc(c)))


def x_num_axis(f, pal, ticks, vmin, vmax, label, dp=1):
    ph, x0, y0, pw = f.ph, f.x0, f.y0, f.pw
    for t in ticks:
        x = x0 + (t - vmin) / float(vmax - vmin) * pw
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (x, y0, x, y0 + ph, pal['grid']))
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" fill="%s">%s</text>'
              % (x, y0 + ph + 22, pal['muted'], fmt(t, dp)))
    x_axis_line(f, pal)
    if label:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>' % (x0 + pw / 2.0, y0 + ph + 58, pal['text'], esc(label)))


# ------------------------------------------------------------- html shell ----

CSS = """
*{box-sizing:border-box}
body{margin:0;padding:40px 22px;background:__GROUND__;color:__TEXT__;
     font-family:__BODY__;line-height:1.55;-webkit-font-smoothing:antialiased}
.figure{max-width:1000px;margin:0 auto;background:__PAPER__;border-radius:20px;
        box-shadow:0 14px 34px rgba(43,37,33,.10);overflow:hidden}
.head{padding:26px 34px 0}
.head h1{margin:0 0 6px;font-family:__HEADING__;font-size:29px;font-weight:700;
        letter-spacing:-.02em;color:__TEXT__}
.head p{margin:0;font-size:15.5px;color:__MUTED__}
.body{padding:18px 34px 26px}
.legend{display:flex;flex-wrap:wrap;gap:8px 22px;margin:0 0 10px;font-size:14px;color:__MUTED__}
.legend span{display:inline-flex;align-items:center;gap:7px}
.legend i{width:12px;height:12px;border-radius:50%;display:inline-block}
.foot{padding:18px 34px 24px;background:__SOFT__}
.foot .cap{margin:0 0 6px;font-size:14.5px;font-weight:600;color:__TEXT__}
.foot .note{margin:0;font-size:12.5px;color:__MUTED__}
"""

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="__FONTS__" rel="stylesheet">
<style>__CSS__</style></head>
<body><div class="figure">
<div class="head"><h1>__TITLE__</h1><p>__SUB__</p></div>
<div class="body">__LEGEND____SVG__</div>
<div class="foot"><p class="cap">Figure. __CAP__</p><p class="note">__NOTE__</p></div>
</div></body></html>"""


def build_html(title, sub, legend, svg, cap, note, pal, font):
    global FONT_BODY_ESC
    FONT_BODY_ESC = font['body'].replace('"', "'")
    css = (CSS.replace('__GROUND__', pal['ground'])
              .replace('__TEXT__', pal['text'])
              .replace('__PAPER__', '#FFFFFF')
              .replace('__SOFT__', pal['soft'])
              .replace('__MUTED__', pal['muted'])
              .replace('__BODY__', font['body'])
              .replace('__HEADING__', font['heading']))
    legend_html = ''
    if legend:
        items = ''.join('<span><i style="background:%s"></i>%s</span>' % (c, esc(n))
                        for c, n in legend)
        legend_html = '<div class="legend">%s</div>' % items
    return (HTML.replace('__TITLE__', esc(title))
                .replace('__SUB__', esc(sub))
                .replace('__LEGEND__', legend_html)
                .replace('__SVG__', svg)
                .replace('__CAP__', esc(cap))
                .replace('__NOTE__', esc(note))
                .replace('__FONTS__', font['google_url'])
                .replace('__CSS__', css))


def write_out(path, html):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return os.path.abspath(path)


# --------------------------------------------------------------- chart: bar ----

def cmd_bar(a):
    pal, font = theme(a)
    if a.values:
        data = pairs_from(a.values)
        dropped, src, total = 0, 'inline values', sum(1 for _ in data)
        counts = []
    else:
        rows = read_rows(a.data)
        src = os.path.basename(a.data)
        if a.y:
            keep = [r for r in rows if r.get(a.x) not in (None, '') and num(r.get(a.y)) is not None]
            dropped = len(rows) - len(keep)
            buckets = {}
            for r in keep:
                buckets.setdefault(str(r[a.x]).strip(), []).append(num(r[a.y]))
            data = [(k, agg(v, a.agg)[0]) for k, v in buckets.items()]
            counts = {k: agg(v, a.agg)[1] for k, v in buckets.items()}
            total = sum(counts.values())
        else:
            keep = [r for r in rows if r.get(a.x) not in (None, '')]
            dropped = len(rows) - len(keep)
            buckets = {}
            for r in keep:
                buckets[str(r[a.x]).strip()] = buckets.get(str(r[a.x]).strip(), 0) + 1
            data = list(buckets.items())
            counts = dict(buckets)
            total = sum(counts.values())
    if not data:
        raise SystemExit('No data to plot.')
    if a.order == 'desc':
        data.sort(key=lambda t: -t[1])
    elif a.order == 'asc':
        data.sort(key=lambda t: t[1])
    cats = [d[0] for d in data]
    vals = [d[1] for d in data]

    dp = 0 if (a.y is None or a.agg == 'count') else 1
    ticks, vmin, vmax = nice_ticks(0, max(vals) * 1.08 or 1.0, a.ticks)

    f = Fig()
    frame(f, pal)
    y_axis(f, pal, ticks, vmin, vmax, a.ylabel or (a.y and '%s (%s)' % (a.y, a.agg)) or 'Count', dp)

    n = len(cats)
    slot = f.pw / float(n)
    bw = min(slot * 0.62, 96)
    cx = []
    for i, (c, v) in enumerate(zip(cats, vals)):
        x = f.x0 + slot * (i + 0.5)
        cx.append(x)
        h = (v - vmin) / float(vmax - vmin) * f.ph
        top = f.y0 + f.ph - h
        col = pal['ramp'][i % len(pal['ramp'])]
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="7" fill="%s"/>'
              % (x - bw / 2.0, top, bw, max(h, 1.0), col))
        if h >= 30:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" font-weight="700" '
                  'fill="%s">%s</text>' % (x, top + 19, on(col), fmt(v, dp)))
        else:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15.5" font-weight="700" '
                  'fill="%s">%s</text>' % (x, top - 7, pal['text'], fmt(v, dp)))
        if a.show_n:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">n=%d</text>'
                  % (x, f.y0 + f.ph + 40, pal['muted'], counts.get(c, 0) if counts else 0))
    x_axis_line(f, pal)
    x_cat_labels(f, pal, cats, cx)
    if a.xlabel:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>' % (f.x0 + f.pw / 2.0, f.h - 12, pal['text'], esc(a.xlabel)))

    title = a.title or ('%s by %s' % ((a.y and a.agg.capitalize() + ' of ' + a.y) or 'Count', a.x))
    cap = a.caption or ('%s for each %s, %s.' % (
        ('Mean ' + a.y) if (a.y and a.agg == 'mean') else ('Count' if not a.y else a.agg + ' of ' + a.y),
        a.x, 'ordered highest to lowest' if a.order == 'desc' else 'in data order'))
    note = 'Data: %s. N = %d%s. Palette: %s. Font: %s.' % (
        src, total, (' (%d rows dropped)' % dropped) if dropped else '', pal['key'], font['name'])
    return title, a.subtitle or '', [], f.out(), cap, note, pal, font


# ------------------------------------------------------- chart: grouped bar ----

def cmd_grouped_bar(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    keep = [r for r in rows if r.get(a.x) not in (None, '') and r.get(a.series) not in (None, '')
            and num(r.get(a.y)) is not None]
    dropped = len(rows) - len(keep)
    series, buckets = [], {}
    for r in keep:
        s = str(r[a.series]).strip()
        if s not in series:
            series.append(s)
        buckets.setdefault(str(r[a.x]).strip(), {}).setdefault(s, []).append(num(r[a.y]))
    if not buckets:
        raise SystemExit('No data to plot.')
    cats = list(buckets.keys())
    vals = {c: [agg(buckets[c].get(s, []), a.agg)[0] for s in series] for c in cats}
    top = max(max(v) for v in vals.values())
    ticks, vmin, vmax = nice_ticks(0, top * 1.1 or 1.0, a.ticks)

    f = Fig(h=600)
    frame(f, pal)
    y_axis(f, pal, ticks, vmin, vmax, a.ylabel or ('%s (%s)' % (a.y, a.agg)))
    slot = f.pw / float(len(cats))
    gw = slot * 0.74
    bw = gw / float(len(series)) * 0.86
    cx = []
    for i, c in enumerate(cats):
        xc = f.x0 + slot * (i + 0.5)
        cx.append(xc)
        for j, s in enumerate(series):
            v = vals[c][j]
            h = (v - vmin) / float(vmax - vmin) * f.ph
            bx = xc - gw / 2.0 + gw / float(len(series)) * (j + 0.5)
            col = pal['ramp'][j % len(pal['ramp'])]
            f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="%s"/>'
                  % (bx - bw / 2.0, f.y0 + f.ph - h, bw, max(h, 1.0), col))
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" font-weight="700" '
                  'fill="%s">%s</text>'
                  % (bx, f.y0 + f.ph - h - 6, pal['text'], fmt(v, 1)))
    x_axis_line(f, pal)
    x_cat_labels(f, pal, cats, cx)
    if a.xlabel:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>' % (f.x0 + f.pw / 2.0, f.h - 12, pal['text'], esc(a.xlabel)))
    legend = [(pal['ramp'][j % len(pal['ramp'])], s) for j, s in enumerate(series)]
    title = a.title or '%s of %s by %s and %s' % (a.agg.capitalize(), a.y, a.x, a.series)
    note = 'Data: %s. N = %d%s. Palette: %s. Font: %s.' % (
        src, len(keep), (' (%d rows dropped)' % dropped) if dropped else '', pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), a.caption or (
        '%s of %s, grouped by %s within each %s.' % (a.agg.capitalize(), a.y, a.series, a.x)), note, pal, font


# ---------------------------------------------------------- chart: histogram ----

def cmd_histogram(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    vals = [num(r.get(a.x)) for r in rows]
    vals = [v for v in vals if v is not None]
    dropped = len(rows) - len(vals)
    if not vals:
        raise SystemExit('Column %r has no numeric values.' % a.x)
    lo, hi = min(vals), max(vals)
    nb = a.bins or max(5, min(14, int(math.ceil(math.log(len(vals), 2)) + 1)))
    if hi <= lo:
        hi = lo + 1
    width = (hi - lo) / float(nb)
    counts = [0] * nb
    for v in vals:
        k = int((v - lo) / width)
        if k >= nb:
            k = nb - 1
        counts[k] += 1
    ticks, vmin, vmax = nice_ticks(0, max(counts) * 1.08 or 1.0, a.ticks)

    f = Fig()
    frame(f, pal)
    y_axis(f, pal, ticks, vmin, vmax, a.ylabel or 'Frequency', 0)
    slot = f.pw / float(nb)
    bw = slot * 0.9
    for i in range(nb):
        c = counts[i]
        h = (c - vmin) / float(vmax - vmin) * f.ph
        x = f.x0 + slot * (i + 0.5)
        top = f.y0 + f.ph - h
        col = pal['ramp'][i % len(pal['ramp'])]
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="5" fill="%s"/>'
              % (x - bw / 2.0, top, bw, max(h, 1.0), col))
        if c:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15.5" font-weight="700" '
                  'fill="%s">%d</text>' % (x, top - 7, pal['text'], c))
    ylab = f.y0 + f.ph + 22
    for i in range(nb):
        ex = f.x0 + slot * i
        anchor = 'middle'
        if i == 0:
            anchor = 'start'
        f.add('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="14" fill="%s">%s</text>'
              % (ex, ylab, anchor, pal['muted'], fmt(lo + width * i, 1)))
    f.add('<text x="%.1f" y="%.1f" text-anchor="end" font-size="14" fill="%s">%s</text>'
          % (f.x0 + f.pw, ylab, pal['muted'], fmt(hi, 1)))
    x_axis_line(f, pal)
    f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
          'fill="%s">%s</text>' % (f.x0 + f.pw / 2.0, f.h - 12, pal['text'],
                                   esc(a.xlabel or a.x)))
    title = a.title or 'How is %s distributed?' % a.x
    note = 'Data: %s. n = %d%s. %d bins of width %s. Palette: %s. Font: %s.' % (
        src, len(vals), (' (%d rows dropped)' % dropped) if dropped else '', nb,
        fmt(width, 2), pal['key'], font['name'])
    return title, a.subtitle or '', [], f.out(), a.caption or (
        'Distribution of %s across %d bins. Bar labels are counts.' % (a.x, nb)), note, pal, font


# ------------------------------------------------------------ chart: scatter ----

def cmd_scatter(a, connect=False):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    cols = [a.x, a.y] + ([a.group] if a.group else [])
    keep = [r for r in rows if all(num(r.get(c)) is not None for c in (a.x, a.y))]
    dropped = len(rows) - len(keep)
    if not keep:
        raise SystemExit('No complete pairs for %s / %s.' % (a.x, a.y))
    xs = [num(r[a.x]) for r in keep]
    ys = [num(r[a.y]) for r in keep]
    xt, xmin, xmax = nice_ticks(min(xs), max(xs), a.ticks)
    yt, ymin, ymax = nice_ticks(min(ys), max(ys), a.ticks)

    groups = []
    if a.group:
        for r in keep:
            g = str(r.get(a.group, '')).strip() or '(missing)'
            if g not in groups:
                groups.append(g)
    series = []
    if groups:
        for g in groups:
            pts = [(num(r[a.x]), num(r[a.y])) for r in keep
                   if (str(r.get(a.group, '')).strip() or '(missing)') == g]
            series.append((g, pts))
    else:
        series.append(('All points', list(zip(xs, ys))))

    f = Fig(h=600)
    frame(f, pal)
    y_axis(f, pal, yt, ymin, ymax, a.ylabel or a.y)
    for t in xt:
        x = f.x0 + (t - xmin) / float(xmax - xmin) * f.pw
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (x, f.y0, x, f.y0 + f.ph, pal['grid']))
    x_num_axis(f, pal, xt, xmin, xmax, a.xlabel or a.x)

    def px(v, lo, hi):
        return f.x0 + (v - lo) / float(hi - lo) * f.pw

    def py(v, lo, hi):
        return f.y0 + f.ph - (v - lo) / float(hi - lo) * f.ph

    r = 3.4 if len(keep) > 220 else 4.6
    legend = []
    for gi, (g, pts) in enumerate(series):
        col = pal['ramp'][gi % len(pal['ramp'])]
        legend.append((col, '%s (n=%d)' % (g, len(pts))))
        if connect and not a.group:
            pts = sorted(pts)
        if connect:
            d = ' '.join('%.1f,%.1f' % (px(x, xmin, xmax), py(y, ymin, ymax)) for x, y in pts)
            f.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" '
                  'stroke-linejoin="round" stroke-linecap="round" opacity=".9"/>' % (d, col))
        for x, y in pts:
            f.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity=".82" stroke="#fff" '
                  'stroke-width="1"/>' % (px(x, xmin, xmax), py(y, ymin, ymax), r, col))
    title = a.title or ('%s against %s' % (a.y, a.x))
    note = 'Data: %s. n = %d complete pairs%s. Palette: %s. Font: %s.' % (
        src, len(keep), (' (%d rows dropped)' % dropped) if dropped else '', pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), a.caption or (
        'Scatter plot of %s against %s. Each point is one observation.' % (a.y, a.x)), note, pal, font


# -------------------------------------------------------------- chart: radar ----

def cmd_radar(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    keep = [r for r in rows if r.get(a.x) not in (None, '') and num(r.get(a.y)) is not None]
    dropped = len(rows) - len(keep)
    if not keep:
        raise SystemExit('No complete rows for %s / %s.' % (a.x, a.y))
    dims = []
    for r in keep:
        d = str(r[a.x]).strip()
        if d not in dims:
            dims.append(d)
    if len(dims) < 3:
        raise SystemExit('A radar chart needs at least 3 dimensions (found %d).' % len(dims))
    groups = []
    if a.group:
        for r in keep:
            g = str(r.get(a.group, '')).strip() or '(missing)'
            if g not in groups:
                groups.append(g)
        series = []
        for g in groups:
            agg_v = {}
            for r in keep:
                if (str(r.get(a.group, '')).strip() or '(missing)') == g:
                    agg_v.setdefault(str(r[a.x]).strip(), []).append(num(r[a.y]))
            series.append((g, [agg(agg_v.get(d, []), a.agg)[0] for d in dims]))
    else:
        agg_v = {}
        for r in keep:
            agg_v.setdefault(str(r[a.x]).strip(), []).append(num(r[a.y]))
        series = [(a.y, [agg(agg_v.get(d, []), a.agg)[0] for d in dims])]

    hi = max(max(s[1]) for s in series)
    ticks, vmin, vmax = nice_ticks(0, hi * 1.12 or 1.0, 4)
    if vmin != 0:
        ticks = [0] + ticks
        vmin = 0

    f = Fig(w=940, h=660, m=dict(l=60, r=60, t=50, b=60))
    cx, cy = f.w / 2.0, (f.h - 30) / 2.0 + 10
    R = min(f.w, f.h) / 2.0 - 92
    n = len(dims)

    def pt(i, v):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        rr = R * (v - vmin) / float(vmax - vmin)
        return cx + rr * math.cos(ang), cy + rr * math.sin(ang)

    for t in ticks[1:]:
        ring = ' '.join('%.1f,%.1f' % pt(i, t) for i in range(n))
        f.add('<polygon points="%s" fill="none" stroke="%s" stroke-width="1"/>' % (ring, pal['grid']))
    for i in range(n):
        x, y = pt(i, vmax)
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (cx, cy, x, y, pal['grid']))
    for t in ticks[1:]:
        x, y = pt(0, t)
        f.add('<text x="%.1f" y="%.1f" font-size="13.5" fill="%s">%s</text>'
              % (x + 5, y + 3, pal['muted'], fmt(t, 1)))

    for i, d in enumerate(dims):
        x, y = pt(i, vmax)
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1
        lx, ly = cx + dx / ln * (R + 30), cy + dy / ln * (R + 30)
        anchor = 'middle'
        if lx > cx + 12:
            anchor = 'start'
        elif lx < cx - 12:
            anchor = 'end'
        f.add('<text x="%.1f" y="%.1f" text-anchor="%s" dominant-baseline="middle" font-size="16.5" '
              'font-weight="600" fill="%s">%s</text>' % (lx, ly, anchor, pal['text'], esc(d)))

    legend = []
    for gi, (g, vals) in enumerate(series):
        col = pal['ramp'][gi % len(pal['ramp'])]
        legend.append((col, '%s (%s)' % (g, a.agg)))
        poly = ' '.join('%.1f,%.1f' % pt(i, v) for i, v in enumerate(vals))
        f.add('<polygon points="%s" fill="%s" fill-opacity=".26" stroke="%s" stroke-width="2.4" '
              'stroke-linejoin="round"/>' % (poly, col, col))
        for i, v in enumerate(vals):
            x, y = pt(i, v)
            f.add('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="#fff" stroke-width="1.6"/>'
                  % (x, y, col))
            if len(series) == 1:
                dx, dy = x - cx, y - cy
                ln = math.hypot(dx, dy) or 1
                f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" '
                      'font-weight="700" fill="%s">%s</text>'
                      % (x + dx / ln * 19, y + dy / ln * 19, pal['text'], fmt(v, 1)))
    title = a.title or '%s across %s' % (a.y, a.x)
    note = 'Data: %s. N = %d%s. %d axes, %s of %s. Palette: %s. Font: %s.' % (
        src, len(keep), (' (%d rows dropped)' % dropped) if dropped else '', n, a.agg, a.y,
        pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), a.caption or (
        'Radar plot of %s across %d levels of %s.' % (a.y, n, a.x)), note, pal, font


# ------------------------------------------------------------- chart: boxplot ----

def cmd_boxplot(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    keep = [r for r in rows if r.get(a.x) not in (None, '') and num(r.get(a.y)) is not None]
    dropped = len(rows) - len(keep)
    buckets = {}
    for r in keep:
        buckets.setdefault(str(r[a.x]).strip(), []).append(num(r[a.y]))
    if not buckets:
        raise SystemExit('No data to plot.')
    cats = list(buckets.keys())
    stats = {}
    for c in cats:
        s = sorted(buckets[c])
        n = len(s)

        def q(p):
            i = p * (n - 1)
            lo = int(math.floor(i))
            hi = int(math.ceil(i))
            return s[lo] + (s[hi] - s[lo]) * (i - lo)

        stats[c] = (s[0], q(.25), q(.5), q(.75), s[-1], n)
    vmax_data = max(stats[c][4] for c in cats)
    vmin_data = min(stats[c][0] for c in cats)
    ticks, vmin, vmax = nice_ticks(vmin_data, vmax_data, a.ticks)

    f = Fig(h=600)
    frame(f, pal)
    y_axis(f, pal, ticks, vmin, vmax, a.ylabel or a.y)
    slot = f.pw / float(len(cats))
    bw = min(slot * 0.42, 74)
    cx = []
    for i, c in enumerate(cats):
        lo, q1, med, q3, hi, n = stats[c]
        x = f.x0 + slot * (i + 0.5)
        cx.append(x)
        col = pal['ramp'][i % len(pal['ramp'])]

        def Y(v):
            return f.y0 + f.ph - (v - vmin) / float(vmax - vmin) * f.ph

        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6"/>'
              % (x, Y(lo), x, Y(hi), pal['muted']))
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6" '
              'stroke-linecap="round"/>' % (x - 11, Y(lo), x + 11, Y(lo), pal['muted']))
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6" '
              'stroke-linecap="round"/>' % (x - 11, Y(hi), x + 11, Y(hi), pal['muted']))
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="%s" '
              'fill-opacity=".88"/>' % (x - bw / 2.0, Y(q3), bw, max(Y(q1) - Y(q3), 2), col))
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>'
              % (x - bw / 2.0, Y(med), x + bw / 2.0, Y(med), on(col)))
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" font-weight="700" '
              'fill="%s">%s</text>' % (x, Y(q3) - 8, pal['text'], fmt(med, 1)))
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">n=%d</text>'
              % (x, f.y0 + f.ph + 40, pal['muted'], n))
    x_axis_line(f, pal)
    x_cat_labels(f, pal, cats, cx)
    if a.xlabel:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>' % (f.x0 + f.pw / 2.0, f.h - 12, pal['text'], esc(a.xlabel)))
    title = a.title or 'How does %s spread across %s?' % (a.y, a.x)
    note = ('Data: %s. N = %d%s. Box = interquartile range, line = median, whiskers = min and max. '
            'Palette: %s. Font: %s.' % (src, len(keep),
                                        (' (%d rows dropped)' % dropped) if dropped else '',
                                        pal['key'], font['name']))
    return title, a.subtitle or '', [], f.out(), a.caption or (
        'Distribution of %s by %s. Boxes span the middle 50%% of scores.' % (a.y, a.x)), note, pal, font


# ------------------------------------------------------------- geo helpers ----

def wrap_text(s, width=20, maxlines=3):
    words, lines, cur = str(s).split(), [], ''
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += ' ' + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1][:max(1, width - 1)] + '\u2026'
    return lines or ['']


def polar(cx, cy, r, deg):
    a = math.radians(deg - 90.0)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def seg_path(cx, cy, r_out, r_in, a0, a1):
    """Wedge or donut segment between two angles, 0 deg = 12 o'clock, clockwise."""
    large = 1 if (a1 - a0) > 180.0 else 0
    x0, y0 = polar(cx, cy, r_out, a0)
    x1, y1 = polar(cx, cy, r_out, a1)
    if r_in > 0:
        x2, y2 = polar(cx, cy, r_in, a1)
        x3, y3 = polar(cx, cy, r_in, a0)
        return ('M%.2f %.2f A%.2f %.2f 0 %d 1 %.2f %.2f L%.2f %.2f '
                'A%.2f %.2f 0 %d 0 %.2f %.2f Z'
                % (x0, y0, r_out, r_out, large, x1, y1, x2, y2, r_in, r_in, large, x3, y3))
    return ('M%.2f %.2f A%.2f %.2f 0 %d 1 %.2f %.2f L%.2f %.2f Z'
            % (x0, y0, r_out, r_out, large, x1, y1, cx, cy))


def part_data(a):
    """Shared prep for pie / donut / funnel. -> data, counts, total, src, dropped."""
    if a.values and a.x is None and a.y is None:
        data = pairs_from(a.values)
        if a.order == 'desc':
            data.sort(key=lambda t: -t[1])
        elif a.order == 'asc':
            data.sort(key=lambda t: t[1])
        return data, {}, sum(v for _, v in data), 'inline values', 0
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    if a.y:
        keep = [r for r in rows if r.get(a.x) not in (None, '') and num(r.get(a.y)) is not None]
        buckets = {}
        for r in keep:
            buckets.setdefault(str(r[a.x]).strip(), []).append(num(r[a.y]))
        data = [(k, agg(v, a.agg)[0]) for k, v in buckets.items()]
        counts = {k: agg(v, a.agg)[1] for k, v in buckets.items()}
    else:
        keep = [r for r in rows if r.get(a.x) not in (None, '')]
        buckets = {}
        for r in keep:
            k = str(r[a.x]).strip()
            buckets[k] = buckets.get(k, 0) + 1
        data = list(buckets.items())
        counts = dict(buckets)
    dropped = len(rows) - len(keep)
    if a.order == 'desc':
        data.sort(key=lambda t: -t[1])
    elif a.order == 'asc':
        data.sort(key=lambda t: t[1])
    return data, counts, sum(v for _, v in data), src, dropped


# ------------------------------------------------------------ chart: pie -----

def cmd_pie(a):
    return _pie(a, donut=False)


def cmd_donut(a):
    return _pie(a, donut=True)


def _pie(a, donut):
    pal, font = theme(a)
    data, counts, total, src, dropped = part_data(a)
    if not data:
        raise SystemExit('No data to plot.')
    if total <= 0:
        raise SystemExit('Every value is zero, so there is no slice to draw.')
    kind = 'donut' if donut else 'pie'
    f = Fig(w=940, h=620, m=dict(l=28, r=28, t=28, b=28))
    cx, cy = f.w / 2.0, f.h / 2.0 + 6
    R = min(f.w, f.h) / 2.0 - 96
    hole = R * 0.55 if donut else 0.0

    legend = [(pal['ramp'][i % len(pal['ramp'])], '%s  %.1f%%' % (k, v / total * 100.0))
              for i, (k, v) in enumerate(data)]

    ang = 0.0
    for i, (k, v) in enumerate(data):
        col = pal['ramp'][i % len(pal['ramp'])]
        frac = v / total
        a0, a1 = ang, ang + frac * 360.0
        if ang >= 359.999:
            a1 = 360.0
        if len(data) == 1 or frac > 0.9999:
            f.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (cx, cy, R, col))
            if donut:
                f.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#FFFFFF"/>' % (cx, cy, hole))
        else:
            f.add('<path d="%s" fill="%s" stroke="#FFFFFF" stroke-width="2"/>'
                  % (seg_path(cx, cy, R, hole, a0, a1), col))
        mid = (a0 + a1) / 2.0
        pct = frac * 100.0
        if pct >= 8.0:
            lx, ly = polar(cx, cy, (R + hole) / 2.0 if donut else R * 0.64, mid)
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16.5" '
                  'font-weight="700" fill="%s">%s</text>'
                  % (lx, ly - 3, on(col), fmt(v, 1)))
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" fill="%s">'
                  '%.1f%%</text>' % (lx, ly + 14, on(col), pct))
        else:
            x0, y0 = polar(cx, cy, R + 3, mid)
            x1, y1 = polar(cx, cy, R + 17, mid)
            x2, y2 = polar(cx, cy, R + 30, mid)
            right = x2 >= cx
            f.add('<polyline points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="none" '
                  'stroke="%s" stroke-width="1.3"/>' % (x0, y0, x1, y1, x2, y2, pal['muted']))
            f.add('<text x="%.1f" y="%.1f" text-anchor="%s" dominant-baseline="middle" '
                  'font-size="15" fill="%s">%.1f (%.1f%%)</text>'
                  % (x2 + (6 if right else -6), y2, 'start' if right else 'end',
                     pal['text'], fmt(v, 1), pct))
        ang = a1

    if donut:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="34" font-weight="700" '
              'fill="%s">%s</text>' % (cx, cy - 2, pal['text'], fmt(total, 1)))
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" fill="%s">%s</text>'
              % (cx, cy + 26, pal['muted'],
                 esc(a.center_label or ('total ' + (a.y or 'records')))))

    unit = a.y or 'records'
    if a.title:
        title = a.title
    elif a.y:
        title = 'How does %s split across %s?' % (a.agg + ' of ' + a.y, a.x)
    else:
        title = 'How do the %s split by %s?' % (unit, a.x)
    cap = a.caption or ('%s chart of %s across %s. Each slice shows its share of the total.'
                        % (kind.capitalize(), a.agg + ' of ' + a.y if a.y else 'records', a.x))
    note = 'Data: %s. Total = %s across %d categories%s. Palette: %s. Font: %s.' % (
        src, fmt(total, 1), len(data),
        (' (%d rows dropped)' % dropped) if dropped else '', pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), cap, note, pal, font


# -------------------------------------------------------- chart: heatmap -----

def cmd_heatmap(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    if a.series:
        keep = [r for r in rows
                if r.get(a.x) not in (None, '') and r.get(a.series) not in (None, '')
                and num(r.get(a.y)) is not None]
        dropped = len(rows) - len(keep)
        if not keep:
            raise SystemExit('No complete %s / %s / %s rows.' % (a.x, a.series, a.y))
        rk, ck, buckets = [], [], {}
        for r in keep:
            k1, k2 = str(r[a.x]).strip(), str(r[a.series]).strip()
            if k1 not in rk:
                rk.append(k1)
            if k2 not in ck:
                ck.append(k2)
            buckets.setdefault((k1, k2), []).append(num(r[a.y]))
        cells, ns = {}, {}
        for k, v in buckets.items():
            cells[k], ns[k] = agg(v, a.agg)
        rowlab, collab, valuecol = a.x, a.series, a.y
    else:
        if not rows:
            raise SystemExit('The file is empty.')
        cols = [c for c in rows[0].keys()
                if c != a.x and any(num(r.get(c)) is not None for r in rows)]
        if not cols:
            raise SystemExit('No numeric columns to build a heatmap from.')
        rk = [(str(r[a.x]).strip() if a.x else 'Row %d' % (i + 1)) for i, r in enumerate(rows)]
        ck, cells, ns, dropped = cols, {}, {}, 0
        for i, r in enumerate(rows):
            for c in cols:
                v = num(r.get(c))
                cells[(rk[i], c)] = v if v is not None else 0.0
                ns[(rk[i], c)] = 1 if v is not None else 0
        rowlab, collab, valuecol = (a.x or 'row'), 'column', (a.y or 'value')

    vals = list(cells.values())
    vmin, vmax = min(vals), max(vals)
    span = (vmax - vmin) or 1.0
    dp = 0 if span >= 20 else (1 if span >= 1 else 2)
    low, high = mix(pal['soft'], '#FFFFFF', 0.55), pal['ramp'][0]

    nrow, ncol = len(rk), len(ck)
    row_h, max_w = 60, 178
    f = Fig(w=max(940, 320 + ncol * 178), h=140 + nrow * row_h,
            m=dict(l=210, r=64, t=142, b=86))
    cw = min(f.pw / float(ncol), max_w)
    ch = row_h
    gx = f.x0 + max(0.0, (f.pw - cw * ncol) / 2.0)
    gy = f.y0 + max(0.0, (f.ph - ch * nrow) / 2.0)
    for j, c in enumerate(ck):
        x = gx + cw * (j + 0.5)
        if max(len(str(c)) for c in ck) > 8:
            f.add('<text x="%.1f" y="%.1f" transform="rotate(-32 %.1f %.1f)" text-anchor="start" '
                  'font-size="16" font-weight="600" fill="%s">%s</text>'
                  % (x, gy - 12, x, gy - 12, pal['text'], esc(c)))
        else:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" font-weight="600" '
                  'fill="%s">%s</text>' % (x, gy - 14, pal['text'], esc(c)))
    for i, r in enumerate(rk):
        y = gy + ch * (i + 0.5)
        f.add('<text x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle" '
              'font-size="16" fill="%s">%s</text>'
              % (gx - 14, y, pal['text'], esc(r)))
        for j, c in enumerate(ck):
            v = cells[(r, c)]
            t = (v - vmin) / span
            col = mix(low, high, t)
            x = gx + cw * j
            f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="7" fill="%s"/>'
                  % (x + 4, gy + ch * i + 4, cw - 8, ch - 8, col))
            if ns.get((r, c), 1) == 0:
                continue
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" dominant-baseline="middle" '
                  'font-size="16" font-weight="700" fill="%s">%s</text>'
                  % (x + cw / 2.0, gy + ch * (i + 0.5), on(col), fmt(v, dp)))
    if a.xlabel:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>' % (gx + cw * ncol / 2.0, f.h - 20, pal['text'], esc(a.xlabel)))
    if a.ylabel:
        cx, cy = 34, gy + ch * nrow / 2.0
        f.add('<text x="%.1f" y="%.1f" transform="rotate(-90 %.1f %.1f)" text-anchor="middle" '
              'font-size="18" font-weight="600" fill="%s">%s</text>'
              % (cx, cy, cx, cy, pal['text'], esc(a.ylabel)))
    title = a.title or ('%s of %s by %s and %s' % (a.agg.capitalize(), valuecol, rowlab, collab)
                        if a.series else 'How does %s vary across %s?' % (valuecol, rowlab))
    cap = a.caption or ('Heatmap of %s across %d %s and %d %s. Darker cells are higher.'
                        % (valuecol, nrow, rowlab, ncol, collab))
    note = ('Data: %s. %d cells%s. Range %s to %s. Palette: %s. Font: %s.'
            % (src, nrow * ncol, ('; %d rows dropped' % dropped) if dropped else '',
               fmt(vmin, dp), fmt(vmax, dp), pal['key'], font['name']))
    return title, a.subtitle or '', [], f.out(), cap, note, pal, font


# ------------------------------------------------------------- chart: area ----

def cmd_area(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    keep = [r for r in rows if num(r.get(a.x)) is not None and num(r.get(a.y)) is not None]
    dropped = len(rows) - len(keep)
    if not keep:
        raise SystemExit('No complete pairs for %s / %s.' % (a.x, a.y))
    groups = []
    if a.group:
        for r in keep:
            g = str(r.get(a.group, '')).strip() or '(missing)'
            if g not in groups:
                groups.append(g)
    if groups:
        series = [(g, sorted((num(r[a.x]), num(r[a.y])) for r in keep
                             if (str(r.get(a.group, '')).strip() or '(missing)') == g))
                  for g in groups]
    else:
        series = [(a.y, sorted((num(r[a.x]), num(r[a.y])) for r in keep))]
    xs = [p[0] for s in series for p in s[1]]
    ys = [p[1] for s in series for p in s[1]]
    xt, xmin, xmax = nice_ticks(min(xs), max(xs), a.ticks)
    yt, ymin, ymax = nice_ticks(min(0.0, min(ys)), max(ys), a.ticks)
    ymin = min(ymin, 0.0)

    f = Fig(h=600)
    frame(f, pal)
    y_axis(f, pal, yt, ymin, ymax, a.ylabel or a.y)
    for t in xt:
        x = f.x0 + (t - xmin) / float(xmax - xmin) * f.pw
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (x, f.y0, x, f.y0 + f.ph, pal['grid']))
    x_num_axis(f, pal, xt, xmin, xmax, a.xlabel or a.x)

    def px(v):
        return f.x0 + (v - xmin) / float(xmax - xmin) * f.pw

    def py(v):
        return f.y0 + f.ph - (v - ymin) / float(ymax - ymin) * f.ph

    base = py(0.0)
    legend = []
    for gi, (g, pts) in enumerate(series):
        col = pal['ramp'][gi % len(pal['ramp'])]
        legend.append((col, '%s (n=%d)' % (g, len(pts))))
        line = ' '.join('%.1f,%.1f' % (px(x), py(y)) for x, y in pts)
        poly = '%.1f,%.1f %s %.1f,%.1f' % (px(pts[0][0]), base, line, px(pts[-1][0]), base)
        f.add('<polygon points="%s" fill="%s" fill-opacity=".30"/>' % (poly, col))
        f.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.6" '
              'stroke-linejoin="round" stroke-linecap="round"/>' % (line, col))
        for x, y in pts:
            f.add('<circle cx="%.1f" cy="%.1f" r="4.2" fill="%s" stroke="#fff" stroke-width="1.6"/>'
                  % (px(x), py(y), col))
        if len(pts) <= 12:
            for k, (x, y) in enumerate(pts):
                f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" '
                      'font-weight="700" fill="%s">%s</text>'
                      % (px(x), py(y) - 12, pal['text'], fmt(y, 1)))
        elif pts:
            x, y = pts[-1]
            f.add('<text x="%.1f" y="%.1f" text-anchor="end" font-size="16" font-weight="700" '
                  'fill="%s">%s</text>' % (px(x), py(y) - 12, pal['text'], fmt(y, 1)))
    title = a.title or ('How does %s build up across %s?' % (a.y, a.x))
    cap = a.caption or ('Area chart of %s against %s. The shaded band is the area under the line.'
                        % (a.y, a.x))
    note = 'Data: %s. n = %d complete pairs%s. Palette: %s. Font: %s.' % (
        src, len(keep), (' (%d rows dropped)' % dropped) if dropped else '',
        pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), cap, note, pal, font


# ----------------------------------------------------------- chart: funnel ----

def cmd_funnel(a):
    pal, font = theme(a)
    data, counts, total, src, dropped = part_data(a)
    if not data:
        raise SystemExit('No data to plot.')
    top = max(v for _, v in data) or 1.0
    first = data[0][1] or 1.0

    rowh = 118
    f = Fig(w=940, h=170 + len(data) * rowh, m=dict(l=44, r=44, t=34, b=46))
    frame(f, pal)
    for i, (k, v) in enumerate(data):
        col = pal['ramp'][i % len(pal['ramp'])]
        w = f.pw * (v / top)
        x = f.x0 + (f.pw - w) / 2.0
        y = f.y0 + i * rowh
        h = rowh - 44
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="9" fill="%s"/>'
              % (x, y, max(w, 3), h, col))
        name = str(k)[:36]
        lab = '%s  (%.1f%%)' % (fmt(v, 1), v / first * 100.0)
        name_w, lab_w = len(name) * 9.6, len(lab) * 10.2
        name_in = (w - 40) >= name_w
        lab_in = name_in and (w - 60) >= (name_w + lab_w)
        if name_in:
            f.add('<text x="%.1f" y="%.1f" dominant-baseline="middle" font-size="18" '
                  'font-weight="600" fill="%s">%s</text>'
                  % (x + 20, y + h / 2.0, on(col), esc(name)))
        else:
            f.add('<text x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle" '
                  'font-size="18" font-weight="600" fill="%s">%s</text>'
                  % (x - 20, y + h / 2.0, pal['text'], esc(name)))
        if lab_in or (x + w + 26 + lab_w > f.x0 + f.pw and not name_in):
            f.add('<text x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle" '
                  'font-size="18" font-weight="700" fill="%s">%s</text>'
                  % (x + w - 20, y + h / 2.0, on(col), lab))
        else:
            f.add('<text x="%.1f" y="%.1f" dominant-baseline="middle" font-size="18" '
                  'font-weight="700" fill="%s">%s</text>'
                  % (x + w + 20, y + h / 2.0, pal['text'], lab))
        if i:
            drop = data[i - 1][1] - v
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="14.5" fill="%s">'
                  '%s lost from the step above</text>'
                  % (f.x0 + f.pw / 2.0, y - 16, pal['muted'], fmt(drop, 1)))
    title = a.title or ('Where do %s drop off across %s?' % (a.y or 'records', a.x or 'the stages'))
    cap = a.caption or ('Funnel chart of %s across %d stages. Bar width is proportional to the value.'
                        % (a.y or 'records', len(data)))
    note = 'Data: %s. Total = %s across %d stages%s. Palette: %s. Font: %s.' % (
        src, fmt(total, 1), len(data),
        (' (%d rows dropped)' % dropped) if dropped else '', pal['key'], font['name'])
    return title, a.subtitle or '', [], f.out(), cap, note, pal, font


# -------------------------------------------------------- chart: flowchart ----

def cmd_flowchart(a):
    pal, font = theme(a)
    if a.labels:
        steps = [(s.strip(), None) for s in a.labels.replace('|', ',').split(',') if s.strip()]
        src, dropped = 'inline labels', 0
    elif a.values and not a.data:
        steps = [(k, None) for k, _ in pairs_from(a.values)]
        src, dropped = 'inline values', 0
    else:
        rows = read_rows(a.data)
        src = os.path.basename(a.data)
        keep = [r for r in rows if r.get(a.x) not in (None, '')]
        dropped = len(rows) - len(keep)
        steps = [(str(r[a.x]).strip(),
                  (fmt(num(r[a.y]), 1) if (a.y and num(r.get(a.y)) is not None) else None))
                 for r in keep]
    if not steps:
        raise SystemExit('No steps to draw.')

    cols = max(1, min(a.cols, len(steps)))
    gap_x, gap_y = 44, 88
    bw = (900 - 40 * 2 - (cols - 1) * gap_x) / float(cols)
    bh = 94
    nrow = int(math.ceil(len(steps) / float(cols)))
    f = Fig(w=900, h=80 + nrow * (bh + gap_y), m=dict(l=40, r=40, t=40, b=40))

    pos = []
    for i, (label, val) in enumerate(steps):
        r, c = divmod(i, cols)
        x = f.x0 + c * (bw + gap_x)
        y = f.y0 + r * (bh + gap_y)
        pos.append((x, y))
        col = pal['ramp'][i % len(pal['ramp'])]
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="12" fill="%s"/>'
              % (x, y, bw, bh, col))
        lines = wrap_text(label, max(12, int(bw / 9.5)), 2)
        ty = y + bh / 2.0 - (len(lines) - 1) * 10 - (11 if val else 0)
        for ln in lines:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" dominant-baseline="middle" '
                  'font-size="16.5" font-weight="600" fill="%s">%s</text>'
                  % (x + bw / 2.0, ty, on(col), esc(ln)))
            ty += 21
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="14.5" fill="%s">%d</text>'
              % (x + bw / 2.0, y + bh - 14, on(col), i + 1))
        if val:
            f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" font-weight="700" '
                  'fill="%s">%s</text>' % (x + bw / 2.0, y + bh + 17, pal['text'], esc(val)))
        if c < cols - 1 and i + 1 < len(steps):
            ax, ay = x + bw + 7, y + bh / 2.0
            f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2.2"/>'
                  % (ax, ay, ax + gap_x - 17, ay, pal['muted']))
            f.add('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" fill="%s"/>'
                  % (ax + gap_x - 15, ay - 6, ax + gap_x - 15, ay + 6, ax + gap_x - 4, ay, pal['muted']))
    for i in range(len(steps) - 1):
        r = i // cols
        if (i + 1) // cols == r:
            continue
        x_last, y_last = pos[i]
        x_first, y_first = pos[i + 1]
        ymid = y_last + bh + gap_y / 2.0
        f.add('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f" fill="none" stroke="%s" '
              'stroke-width="2.2"/>'
              % (x_last + bw / 2.0, y_last + bh, x_last + bw / 2.0, ymid,
                 x_first + bw / 2.0, ymid, x_first + bw / 2.0, y_first - 6, pal['muted']))
        f.add('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" fill="%s"/>'
              % (x_first + bw / 2.0 - 6, y_first - 12, x_first + bw / 2.0 + 6, y_first - 12,
                 x_first + bw / 2.0, y_first - 1, pal['muted']))
    title = a.title or 'How does the process flow?'
    cap = a.caption or ('Flow chart of %d steps, read left to right then top to bottom.'
                        % len(steps))
    note = 'Source: %s. %d steps%s. Palette: %s. Font: %s.' % (
        src, len(steps), (' (%d rows dropped)' % dropped) if dropped else '',
        pal['key'], font['name'])
    return title, a.subtitle or '', [], f.out(), cap, note, pal, font


# ------------------------------------------------------------ chart: gantt ----

def cmd_gantt(a):
    pal, font = theme(a)
    rows = read_rows(a.data)
    src = os.path.basename(a.data)
    if not a.start:
        raise SystemExit('A Gantt chart needs --start (and --end or --duration).')
    tasks, starts, ends, groups = [], [], [], []
    dropped = 0
    dated = True
    for r in rows:
        s_raw = str(r.get(a.start, '')).strip()
        d0 = None
        try:
            d0 = datetime.date.fromisoformat(s_raw.replace('/', '-')[:10]).toordinal()
        except ValueError:
            d0 = None
        if d0 is None:
            dated = False
            break
    for r in rows:
        lab = str(r.get(a.x, '')).strip() if a.x else ''
        if not lab:
            dropped += 1
            continue
        if dated:
            s = datetime.date.fromisoformat(str(r[a.start]).strip().replace('/', '-')[:10]).toordinal()
            if a.end:
                e = datetime.date.fromisoformat(str(r[a.end]).strip().replace('/', '-')[:10]).toordinal()
            else:
                e = s + (num(r.get(a.duration)) or 1) - 1
        else:
            s = num(r.get(a.start))
            e = num(r.get(a.end)) if a.end else (s + (num(r.get(a.duration)) or 0) if s is not None else None)
        if s is None or e is None:
            dropped += 1
            continue
        if e < s:
            s, e = e, s
        tasks.append(lab)
        starts.append(s)
        ends.append(e)
        groups.append(str(r.get(a.group, '')).strip() if a.group else '')
    if not tasks:
        raise SystemExit('No usable task rows.')
    uniq = []
    for g in groups:
        if g not in uniq:
            uniq.append(g)

    lo, hi = min(starts), max(ends)
    if hi <= lo:
        hi = lo + 1
    span = float(hi - lo)
    f = Fig(w=960, h=170 + len(tasks) * 48, m=dict(l=214, r=136, t=54, b=88))
    frame(f, pal)

    def X(v):
        return f.x0 + (v - lo) / span * f.pw

    for i, (lab, s, e, g) in enumerate(zip(tasks, starts, ends, groups)):
        y = f.y0 + 20 + i * 48
        gi = uniq.index(g) if uniq else i
        col = pal['ramp'][gi % len(pal['ramp'])]
        f.add('<text x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle" '
              'font-size="16.5" fill="%s">%s</text>'
              % (f.x0 - 16, y + 12, pal['text'], esc(lab)))
        f.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="7" fill="%s"/>'
              % (X(s), y, max(X(e) - X(s), 6), 25, col))
        dur = e - s + (1 if dated else 0)
        lab_d = ('%dd' % int(dur)) if dated else fmt(float(dur), 1)
        f.add('<text x="%.1f" y="%.1f" dominant-baseline="middle" font-size="15" '
              'font-weight="700" fill="%s">%s</text>'
              % (X(e) + 9, y + 12, pal['text'], lab_d))

    tmin, tmax = math.floor(lo), math.ceil(hi)
    tks, _, _ = nice_ticks(float(tmin), float(tmax), a.ticks)
    by = f.y0 + 26 + len(tasks) * 48
    for t in tks:
        ti = int(round(t))
        if ti < tmin or ti > tmax:
            continue
        x = X(ti)
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
              % (x, f.y0 + 8, x, by - 6, pal['grid']))
        lab = (datetime.date.fromordinal(ti).strftime('%d %b') if dated else fmt(t, 0))
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15.5" fill="%s">%s</text>'
              % (x, by + 20, pal['muted'], lab))
    f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
          % (f.x0, by, f.x0 + f.pw, by, pal['muted']))
    if a.xlabel:
        f.add('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="18" font-weight="600" '
              'fill="%s">%s</text>'
              % (f.x0 + f.pw / 2.0, by + 52, pal['text'], esc(a.xlabel)))
    if a.ylabel:
        cx, cy = 28, f.y0 + f.ph / 2.0
        f.add('<text x="%.1f" y="%.1f" transform="rotate(-90 %.1f %.1f)" text-anchor="middle" '
              'font-size="18" font-weight="600" fill="%s">%s</text>'
              % (cx, cy, cx, cy, pal['text'], esc(a.ylabel)))
    legend = [(pal['ramp'][uniq.index(g) % len(pal['ramp'])], g) for g in uniq] if a.group else []
    title = a.title or 'What is the schedule?'
    cap = a.caption or ('Gantt chart of %d tasks%s. Bar length is the duration.'
                        % (len(tasks), ' by ' + a.group if a.group else ''))
    note = 'Data: %s. %d tasks%s. Palette: %s. Font: %s.' % (
        src, len(tasks), (' (%d rows dropped)' % dropped) if dropped else '',
        pal['key'], font['name'])
    return title, a.subtitle or '', legend, f.out(), cap, note, pal, font


# -------------------------------------------------------------------- main ----

def common(p):
    p.add_argument('--data', help='CSV file')
    p.add_argument('--values', help='inline "label:value,label:value" instead of a CSV')
    p.add_argument('--x', help='category / x column')
    p.add_argument('--y', help='numeric / value column')
    p.add_argument('--group', help='series column (scatter, radar, line)')
    p.add_argument('--series', help='series column (grouped-bar)')
    p.add_argument('--title')
    p.add_argument('--subtitle', default='')
    p.add_argument('--xlabel')
    p.add_argument('--ylabel')
    p.add_argument('--caption')
    p.add_argument('--labels', help='inline comma-separated steps (flowchart)')
    p.add_argument('--cols', type=int, default=4, help='boxes per row (flowchart)')
    p.add_argument('--start', help='start column (gantt)')
    p.add_argument('--end', help='end column (gantt)')
    p.add_argument('--duration', help='duration column (gantt)')
    p.add_argument('--center-label', help='text inside a donut hole')
    p.add_argument('--palette', help='palette key, or random. Default: random')
    p.add_argument('--font', help='font pairing name, or random. Default: random')
    p.add_argument('--out', default='outputs/chart.html')
    p.add_argument('--ticks', type=int, default=5)
    p.add_argument('--seed', type=int)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='render.py', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')

    def add(name, fn):
        s = sub.add_parser(name)
        common(s)
        s.set_defaults(fn=fn)

    AGGS = ['mean', 'sum', 'count', 'median']

    def with_agg(p, order=None):
        p.add_argument('--agg', default='mean', choices=AGGS)
        if order:
            p.add_argument('--order', default=order, choices=['desc', 'asc', 'asis'])

    b = sub.add_parser('bar'); common(b); with_agg(b, 'desc')
    b.add_argument('--show-n', action='store_true'); b.set_defaults(fn=cmd_bar)

    g = sub.add_parser('grouped-bar'); common(g); with_agg(g)
    g.set_defaults(fn=cmd_grouped_bar)

    h = sub.add_parser('histogram'); common(h); h.add_argument('--bins', type=int)
    h.set_defaults(fn=cmd_histogram)

    for nm, fn in (('scatter', cmd_scatter), ('line', lambda a: cmd_scatter(a, connect=True))):
        s = sub.add_parser(nm); common(s); s.set_defaults(fn=fn)

    ar = sub.add_parser('area'); common(ar); ar.set_defaults(fn=cmd_area)

    r = sub.add_parser('radar'); common(r); with_agg(r); r.set_defaults(fn=cmd_radar)

    x = sub.add_parser('boxplot'); common(x); x.set_defaults(fn=cmd_boxplot)

    for nm, fn in (('pie', cmd_pie), ('donut', cmd_donut)):
        s = sub.add_parser(nm); common(s); with_agg(s, 'desc')
        s.set_defaults(fn=fn)

    hm = sub.add_parser('heatmap'); common(hm); with_agg(hm)
    hm.set_defaults(fn=cmd_heatmap)

    fn_ = sub.add_parser('funnel'); common(fn_); with_agg(fn_, 'asis')
    fn_.set_defaults(fn=cmd_funnel)

    fl = sub.add_parser('flowchart'); common(fl); fl.set_defaults(fn=cmd_flowchart)

    ga = sub.add_parser('gantt'); common(ga); ga.set_defaults(fn=cmd_gantt)

    sub.add_parser('list').set_defaults(fn=None)

    a = ap.parse_args(argv)
    if not getattr(a, 'cmd', None):
        ap.print_help()
        return 0
    if a.cmd == 'list':
        print('Palettes:', ', '.join(_load('palettes.json')['palettes'].keys()))
        print('Fonts:   ', ', '.join(p['name'] for p in _load('fonts.json')['pairings']))
        return 0
    if getattr(a, 'seed', None) is not None:
        random.seed(a.seed)
    if not a.data and not a.values and not getattr(a, 'labels', None):
        raise SystemExit('Give --data a CSV path, or --values "A:1,B:2".')
    title, sub_, legend, svg, cap, note, pal, font = a.fn(a)
    html = build_html(title, sub_, legend, svg, cap, note, pal, font)
    out = write_out(a.out, html)
    print('Wrote %s' % out)
    print('  chart   : %s' % a.cmd)
    print('  palette : %s (%s)%s' % (pal['key'], pal['name'],
                                     '  drawn at random' if pal.get('picked') == 'random' else ''))
    print('  font    : %s%s' % (font['name'],
                                '  drawn at random' if font.get('picked') == 'random' else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
