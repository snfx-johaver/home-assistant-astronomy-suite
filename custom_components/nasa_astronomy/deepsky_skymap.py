"""Top-down sky-map renderer for the Deep-Sky feature (pure standard library).

Draws an SVG, North-up, centred on the observer. A compass ring carries every
object's direction as an arrow; the arrow length encodes altitude (short = high
overhead, long = near the horizon) and the number on it is the degrees to tilt
up. When an optional per-azimuth horizon profile is supplied (advanced "from
your yard" feature) a grey silhouette band shows where trees / buildings block
the sky; without one the map simply shows where every target is in the sky.

render_svg() is a pure function (no Home Assistant imports) so it can be
unit-tested and screenshot-checked offline. It ships no personal data: there is
no aerial photo and no site-specific yard outline.
"""
from __future__ import annotations

import math

# Canvas + compass geometry.
W, H = 660, 620
CX, CY = 330, 298
R = 216                  # outer compass ring radius (px)
R_ZENITH = 46            # arrow tip radius for alt 90 (px)
R_HORIZON = 206          # arrow tip radius for alt 0 (px)
LABEL_PAD = 76           # keep label text this far from canvas edges
BAND_PX_PER_DEG = 2.2    # horizon silhouette thickness per degree of blockage

KIND_COLOR = {
    "deepsky": "#5bd6ff",
    "planet": "#ffd24a",
    "moon": "#e8e8e8",
    "sun": "#ff8c2a",
}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _pt(az: float, r: float) -> tuple[float, float]:
    a = math.radians(az)
    return CX + r * math.sin(a), CY - r * math.cos(a)


def _r_for_alt(alt: float) -> float:
    alt = max(0.0, min(90.0, alt))
    return R_HORIZON - (R_HORIZON - R_ZENITH) * (alt / 90.0)


def _horizon_band(typical: list[float]) -> str:
    """Grey silhouette annulus: outer = ring, inner dips in where blocked."""
    outer, inner = [], []
    for az in range(0, 361, 2):
        a = az % 360
        outer.append(_pt(az, R))
        rin = R - max(0.0, typical[a]) * BAND_PX_PER_DEG
        rin = max(rin, 124.0)
        inner.append(_pt(az, rin))
    d = "M %.1f %.1f " % outer[0]
    d += " ".join("L %.1f %.1f" % p for p in outer[1:])
    for p in reversed(inner):
        d += " L %.1f %.1f" % p
    d += " Z"
    return ('<path d="%s" fill="#0a1320" fill-opacity="0.7" '
            'fill-rule="evenodd" stroke="none"/>' % d)


def _compass() -> str:
    out = ['<circle cx="%d" cy="%d" r="%d" fill="none" '
           'stroke="#5a6b7d" stroke-width="1.6"/>' % (CX, CY, R)]
    for az in range(0, 360, 10):
        long = az % 30 == 0
        r0 = R - (12 if long else 6)
        x0, y0 = _pt(az, r0)
        x1, y1 = _pt(az, R)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                   'stroke="#46586a" stroke-width="%s"/>'
                   % (x0, y0, x1, y1, "1.4" if long else "0.8"))
    labels = [(0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
              (180, "S"), (225, "SW"), (270, "W"), (315, "NW")]
    for az, name in labels:
        lx, ly = _pt(az, R + 15)
        big = az % 90 == 0
        out.append('<text x="%.1f" y="%.1f" fill="%s" font-size="%d" '
                   'font-weight="%s" text-anchor="middle" '
                   'dominant-baseline="middle" font-family="sans-serif">%s</text>'
                   % (lx, ly, "#cfe3f2" if big else "#7d93a6",
                      17 if big else 12, "700" if big else "500", name))
    return "".join(out)


def _scope() -> str:
    return (
        '<g>'
        '<circle cx="%d" cy="%d" r="9" fill="none" stroke="#ffffff" stroke-width="1.6"/>'
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-width="1.2"/>'
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-width="1.2"/>'
        '<circle cx="%d" cy="%d" r="2.2" fill="#ffffff"/>'
        '</g>'
        % (CX, CY, CX - 13, CY, CX + 13, CY, CX, CY - 13, CX, CY + 13, CX, CY))


def _arrow(o: dict) -> str:
    az = float(round(float(o["az"]))) % 360.0
    altd = round(float(o["alt"]))
    r = _r_for_alt(altd)
    tip = _pt(az, r)
    base = _pt(az, 22)
    a = math.radians(az)
    dx, dy = math.sin(a), -math.cos(a)
    px, py = math.cos(a), math.sin(a)
    tier = o.get("tier", "clear")
    kind = o.get("kind", "deepsky")
    bright = o.get("bright", True)

    if tier == "blocked":
        col, dash, wid, op = "#d9534f", "4 4", 1.4, 0.5
    elif tier == "step":
        col, dash, wid, op = "#ff9f40", "6 4", 2.2, 0.95
    else:
        col, dash, wid, op = KIND_COLOR.get(kind, "#5bd6ff"), "", 2.6, 1.0
    if not bright and tier != "blocked":
        op *= 0.5

    parts = ['<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
             'stroke-width="%.1f" stroke-opacity="%.2f" %s/>'
             % (base[0], base[1], tip[0], tip[1], col, wid, op,
                ('stroke-dasharray="%s"' % dash) if dash else "")]
    if tier != "blocked":
        h1 = (tip[0] - 11 * dx + 5 * px, tip[1] - 11 * dy + 5 * py)
        h2 = (tip[0] - 11 * dx - 5 * px, tip[1] - 11 * dy - 5 * py)
        parts.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" '
                     'fill="%s" fill-opacity="%.2f"/>'
                     % (tip[0], tip[1], h1[0], h1[1], h2[0], h2[1], col, op))

    lr = min(r + 14, R - 6)
    lx, ly = _pt(az, lr)
    anchor = "middle"
    if math.sin(a) > 0.25:
        anchor = "start"
    elif math.sin(a) < -0.25:
        anchor = "end"
    lx = max(LABEL_PAD, min(W - LABEL_PAD, lx))
    ly = max(60.0, min(H - 56.0, ly))
    label = _esc(o["short"])
    if tier != "blocked":
        label += " %d\u00b0" % round(float(o["alt"]))
    if tier == "step" and o.get("where"):
        label += " \u2192%s" % _esc(o["where"])
    tcol = "#9fb3c4" if (tier == "blocked" or not bright) else "#eaf3fb"
    parts.append('<text x="%.1f" y="%.1f" fill="%s" font-size="11.5" '
                 'text-anchor="%s" dominant-baseline="middle" '
                 'font-family="sans-serif" font-weight="600" '
                 'paint-order="stroke" stroke="#06101a" stroke-width="2.6">%s</text>'
                 % (lx, ly, tcol, anchor, label))
    return "".join(parts)


def _legend(y: int, has_horizon: bool) -> str:
    items = [
        ("#5bd6ff", "Deep-sky"), ("#ffd24a", "Planet"),
        ("#e8e8e8", "Moon"), ("#ff8c2a", "Sun"),
    ]
    if has_horizon:
        items += [("#ff9f40", "Step to edge"), ("#d9534f", "Blocked")]
    out = []
    x = 24
    for col, txt in items:
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" '
                   'stroke-width="3"/>' % (x, y, x + 20, y, col))
        out.append('<text x="%d" y="%d" fill="#b9cad9" font-size="11.5" '
                   'dominant-baseline="middle" font-family="sans-serif">%s</text>'
                   % (x + 25, y, txt))
        x += 38 + 7.2 * len(txt)
    if has_horizon:
        out.append('<rect x="24" y="%d" width="20" height="11" fill="#5a6470" '
                   'fill-opacity="0.45"/>' % (y + 14))
        out.append('<text x="49" y="%d" fill="#b9cad9" font-size="11.5" '
                   'dominant-baseline="middle" font-family="sans-serif">'
                   'Grey = your horizon (trees / buildings); thicker = higher</text>'
                   % (y + 20))
    return "".join(out)


def render_svg(positions: list[dict], typical: list[float],
               now_str: str) -> str:
    """Build the top-down sky-map SVG string.

    positions: list of {short, az, alt, kind, tier, where, bright}
    typical:   optional 360-length list, obstruction altitude (deg) per azimuth
               for an advanced horizon profile; empty/None draws a clear sky.
    """
    has_horizon = bool(typical and len(typical) == 360)
    n_clear = sum(1 for p in positions if p.get("tier") == "clear")
    n_step = sum(1 for p in positions if p.get("tier") == "step")
    n_block = sum(1 for p in positions if p.get("tier") == "blocked")
    if has_horizon:
        title = ('Tonight from your yard \u2014 %d clear \u00b7 %d step \u00b7 '
                 '%d blocked' % (n_clear, n_step, n_block))
        sub = ('Stand at the centre \u2295 \u00b7 arrow = way to face \u00b7 '
               'number = degrees to tilt up \u00b7 longer arrow = lower in the sky')
    else:
        title = 'Tonight\u2019s sky \u2014 %d targets up' % len(positions)
        sub = ('You are at the centre \u2295 \u00b7 arrow = compass direction to '
               'face \u00b7 number = degrees to tilt up \u00b7 longer arrow = lower')
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family="sans-serif">' % (W, H, W, H),
        '<rect width="%d" height="%d" fill="#06101a"/>' % (W, H),
        '<text x="24" y="28" fill="#eaf3fb" font-size="18" font-weight="700">'
        '%s</text>' % _esc(title),
        '<text x="%d" y="28" fill="#8aa0b2" font-size="12" text-anchor="end">'
        '%s</text>' % (W - 24, _esc(now_str)),
        '<text x="24" y="46" fill="#8aa0b2" font-size="11.5">%s</text>'
        % _esc(sub),
        '<circle cx="%d" cy="%d" r="%d" fill="#0b1622"/>' % (CX, CY, R),
    ]
    body.append(_compass())
    if has_horizon:
        body.append(_horizon_band(typical))
    # blocked first (under), then step, then clear (on top)
    order = {"blocked": 0, "step": 1, "clear": 2}
    for o in sorted(positions, key=lambda d: order.get(d.get("tier"), 2)):
        body.append(_arrow(o))
    body.append(_scope())
    body.append(_legend(H - 40, has_horizon))
    body.append("</svg>")
    return "".join(body)
