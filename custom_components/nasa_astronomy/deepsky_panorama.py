"""Horizon panorama renderer for the Deep-Sky feature (pure standard library).

Draws an SVG strip the way you see the sky when you stand outside and turn
around: the horizontal axis is compass direction (N-E-S-W-N), the vertical axis
is height above the horizon. Tonight's objects are plotted at their true bearing
and altitude. When an optional horizon profile is supplied (advanced "from your
yard" feature) a dark skyline shows trees / buildings, so a dot above it clears
your view and a dot inside it is blocked; without one a flat horizon is drawn.

render() is a pure function (no Home Assistant imports) so it can be
screenshot-checked offline. It ships no personal data.
"""
from __future__ import annotations

# Canvas + plot geometry.
W, H = 1120, 486
PLOT_L = 50
PLOT_R = W - 18            # 1102
TOP = 64                   # plot top (below the title)
AXIS_Y = 430               # horizon line / alt 0
PLOT_W = PLOT_R - PLOT_L   # 1052
PLOT_H = AXIS_Y - TOP      # 366
ALT_MAX = 80.0             # top of the altitude axis (deg)

KIND_COLOR = {
    "deepsky": "#5bd6ff",
    "planet": "#ffd24a",
    "moon": "#e8e8e8",
    "sun": "#ff8c2a",
}

_CARDINALS = [(0, "N"), (45, "NE"), (90, "E"), (135, "SE"), (180, "S"),
              (225, "SW"), (270, "W"), (315, "NW"), (360, "N")]


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _x(az: float) -> float:
    return PLOT_L + (az % 360.0) / 360.0 * PLOT_W


def _y(alt: float) -> float:
    a = max(0.0, min(ALT_MAX, alt))
    return AXIS_Y - a / ALT_MAX * PLOT_H


def _skyline(prof: list[float], fill: str, opacity: float,
             stroke: str) -> str:
    """Filled silhouette path from a 360-length obstruction profile."""
    pts = ["M %.1f %.1f" % (PLOT_L, AXIS_Y)]
    for az in range(0, 361):
        pts.append("L %.1f %.1f" % (_x(az), _y(prof[az % 360])))
    pts.append("L %.1f %.1f Z" % (PLOT_R, AXIS_Y))
    d = " ".join(pts)
    return ('<path d="%s" fill="%s" fill-opacity="%.2f" stroke="%s" '
            'stroke-width="1.3" stroke-opacity="0.8"/>' % (d, fill, opacity,
                                                           stroke))


def _line(prof: list[float], stroke: str) -> str:
    pts = ["M %.1f %.1f" % (_x(0), _y(prof[0]))]
    for az in range(1, 361):
        pts.append("L %.1f %.1f" % (_x(az), _y(prof[az % 360])))
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="1.2" '
            'stroke-dasharray="5 4" stroke-opacity="0.6"/>'
            % (" ".join(pts), stroke))


def _grid() -> str:
    out = []
    for alt in (15, 30, 45, 60):
        y = _y(alt)
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#24384f" '
                   'stroke-width="0.8" stroke-dasharray="2 5"/>'
                   % (PLOT_L, y, PLOT_R, y))
        out.append('<text x="%d" y="%.1f" fill="#5f7d8f" font-size="10" '
                   'text-anchor="end" dominant-baseline="middle">%d\u00b0</text>'
                   % (PLOT_L - 6, y, alt))
    for az, _name in _CARDINALS:
        x = _x(az)
        out.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#24384f" '
                   'stroke-width="0.8" stroke-dasharray="2 5"/>'
                   % (x, TOP, x, AXIS_Y))
    return "".join(out)


def _objects(positions: list[dict]) -> str:
    out = []
    placed: list[tuple[float, float]] = []
    for o in sorted(positions, key=lambda d: _x(float(d["az"]))):
        az = float(o["az"])
        alt = float(o["alt"])
        x, y = _x(az), _y(alt)
        tier = o.get("tier", "clear")
        kind = o.get("kind", "deepsky")
        bright = o.get("bright", True)
        base = KIND_COLOR.get(kind, "#5bd6ff")
        if tier == "blocked":
            col, op, rad = "#d9534f", 0.55, 3.4
        elif tier == "step":
            col, op, rad = "#ff9f40", 0.95, 4.0
        else:
            col, op, rad = base, 1.0, (5.0 if (kind != "deepsky" and bright)
                                       else 4.0)
        if not bright and tier != "blocked":
            op *= 0.6
        if tier == "clear" and bright:
            out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" '
                       'fill-opacity="0.18"/>' % (x, y, rad + 5, col))
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" '
                   'fill-opacity="%.2f" stroke="#06101a" stroke-width="0.8"/>'
                   % (x, y, rad, col, op))

        label = _esc(o["short"])
        if tier != "blocked":
            label += " %d\u00b0" % round(alt)
        ly = y - 12
        while (any(abs(x - px) < 52 and abs(ly - py) < 13 for px, py in placed)
               and ly > TOP + 10):
            ly -= 13
        if ly <= TOP + 10:
            ly = y + 17
        placed.append((x, ly))
        anchor = "middle"
        lx = x
        if x < PLOT_L + 44:
            anchor, lx = "start", x
        elif x > PLOT_R - 44:
            anchor, lx = "end", x
        tcol = "#9fb3c4" if (tier == "blocked" or not bright) else "#eaf3fb"
        out.append('<text x="%.1f" y="%.1f" fill="%s" font-size="11.5" '
                   'text-anchor="%s" dominant-baseline="middle" '
                   'font-weight="600" paint-order="stroke" stroke="#06101a" '
                   'stroke-width="2.8">%s</text>'
                   % (lx, ly, tcol, anchor, label))
    return "".join(out)


def _compass_axis() -> str:
    out = []
    for az, name in _CARDINALS:
        x = _x(az)
        big = az % 90 == 0
        out.append('<text x="%.1f" y="%d" fill="%s" font-size="%d" '
                   'font-weight="%s" text-anchor="middle">%s</text>'
                   % (x, AXIS_Y + 18, "#cfe3f2" if big else "#7d93a6",
                      15 if big else 11, "700" if big else "500", name))
    return "".join(out)


def _legend(y: int, has_horizon: bool) -> str:
    items = [("#5bd6ff", "Deep-sky"), ("#ffd24a", "Planet"),
             ("#e8e8e8", "Moon"), ("#ff8c2a", "Sun")]
    if has_horizon:
        items += [("#ff9f40", "Open-spot only"), ("#d9534f", "Blocked")]
    out = []
    x = PLOT_L
    for col, txt in items:
        out.append('<circle cx="%d" cy="%d" r="4.5" fill="%s"/>' % (x, y, col))
        out.append('<text x="%d" y="%d" fill="#b9cad9" font-size="11" '
                   'dominant-baseline="middle">%s</text>' % (x + 9, y, txt))
        x += 24 + int(7.0 * len(txt))
    return "".join(out)


def render(positions: list[dict], horizon: dict | None,
           now_str: str) -> str:
    """Build the horizon-panorama SVG string.

    positions: list of {short, az, alt, kind, tier, where, bright}
    horizon:   dict with 360-length 'typical' (and optional 'best') lists,
               or None to draw a flat horizon.
    """
    typical = (horizon or {}).get("typical")
    best = (horizon or {}).get("best")
    has_horizon = bool(typical and len(typical) == 360)
    n_clear = sum(1 for p in positions if p.get("tier") == "clear"
                  and p.get("bright"))
    n_block = sum(1 for p in positions if p.get("tier") == "blocked")
    if has_horizon:
        title = ('Your sky now \u2014 %d clear of your skyline \u00b7 %d blocked'
                 % (n_clear, n_block))
        sub = ('Left = how high to look \u00b7 bottom = which way to face \u00b7 '
               'dots above the dark skyline clear your trees/buildings, dots '
               'inside it are blocked')
    else:
        title = ('Your sky now \u2014 %d targets above the horizon'
                 % len(positions))
        sub = ('Left = how high to look \u00b7 bottom = which way to face \u00b7 '
               'every dot shown is above your horizon')
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family="sans-serif">' % (W, H, W, H),
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#060a1a"/>'
        '<stop offset="0.65" stop-color="#0b1733"/>'
        '<stop offset="1" stop-color="#1b2f52"/></linearGradient></defs>',
        '<rect width="%d" height="%d" fill="#06101a"/>' % (W, H),
        '<rect x="%d" y="%d" width="%d" height="%d" fill="url(#sky)"/>'
        % (PLOT_L, TOP, PLOT_W, PLOT_H),
        '<text x="24" y="28" fill="#eaf3fb" font-size="18" font-weight="700">'
        '%s</text>' % _esc(title),
        '<text x="%d" y="28" fill="#8aa0b2" font-size="12" text-anchor="end">'
        '%s</text>' % (W - 22, _esc(now_str)),
        '<text x="24" y="47" fill="#8aa0b2" font-size="11.5">%s</text>'
        % _esc(sub),
        _grid(),
    ]
    if has_horizon and best and len(best) == 360:
        body.append(_line(best, "#46627d"))
    if has_horizon:
        body.append(_skyline(typical, "#0b160e", 0.97, "#38613f"))
    else:
        body.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#38613f" '
                    'stroke-width="1.3"/>' % (PLOT_L, AXIS_Y, PLOT_R, AXIS_Y))
    body.append(_objects(positions))
    body.append(_compass_axis())
    body.append(_legend(H - 12, has_horizon))
    body.append("</svg>")
    return "".join(body)
