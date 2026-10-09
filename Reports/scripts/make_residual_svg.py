#!/usr/bin/env python3
"""Parse log.buoyantBoussinesqSimpleFoam → residuals.csv + residuals.svg."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

CASE = Path(__file__).resolve().parents[2]
LOG = CASE / "log.buoyantBoussinesqSimpleFoam"
OUT_CSV = CASE / "Reports" / "data" / "residuals.csv"
OUT_SVG = CASE / "Reports" / "figures" / "residuals.svg"

SERIES = (
    ("Ux", "#1f77b4"),
    ("Uy", "#ff7f0e"),
    ("Uz", "#2ca02c"),
    ("T", "#d62728"),
    ("p_rgh", "#9467bd"),
    ("k", "#8c564b"),
    ("epsilon", "#e377c2"),
)

TIME_RE = re.compile(r"^Time = ([0-9.eE+-]+)\s*$", re.M)
RES_RE = re.compile(
    r"Solving for (Ux|Uy|Uz|T|p_rgh|k|epsilon), Initial residual = ([0-9.eE+-]+)"
)


def parse_residuals(path: Path) -> list[dict[str, float]]:
    text = path.read_text(errors="replace")
    time_matches = list(TIME_RE.finditer(text))
    rows: list[dict[str, float]] = []
    for i, tm in enumerate(time_matches):
        t = float(tm.group(1))
        start = tm.start()
        end = time_matches[i + 1].start() if i + 1 < len(time_matches) else len(text)
        block = text[start:end]
        row: dict[str, float] = {"time": t}
        for m in RES_RE.finditer(block):
            key = m.group(1)
            if key not in row:  # first p_rgh (predictor) only
                row[key] = float(m.group(2))
        if len(row) > 1:
            rows.append(row)
    by_t = {r["time"]: r for r in rows}
    return [by_t[t] for t in sorted(by_t)]


def log_ticks(ymin: float, ymax: float) -> list[float]:
    lo = int(math.floor(math.log10(ymin)))
    hi = int(math.ceil(math.log10(ymax)))
    ticks: list[float] = []
    for e in range(lo, hi + 1):
        ticks.append(10.0**e)
    return ticks


def fmt_sci(v: float) -> str:
    if v == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(v))))
    mant = v / (10.0**exp)
    if abs(mant - 1.0) < 1e-9:
        return f"10^{exp}"
    return f"{mant:g}×10^{exp}"


def write_svg(path: Path, rows: list[dict[str, float]], title: str) -> None:
    width, height = 820, 480
    ml, mr, mt, mb = 72, 160, 44, 52
    pw, ph = width - ml - mr, height - mt - mb
    times = [r["time"] for r in rows]
    xmin, xmax = min(times), max(times)
    if xmax <= xmin:
        xmax = xmin + 1.0
    vals = [r[k] for r in rows for k, _ in SERIES if k in r and r[k] > 0]
    if not vals:
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<text x="20" y="40">No residuals in log</text></svg>\n'
        )
        return
    ymin = max(min(vals) / 2.0, 1e-12)
    ymax = max(vals) * 2.0

    def X(t: float) -> float:
        return ml + (t - xmin) / (xmax - xmin) * pw

    def Y(v: float) -> float:
        v = max(v, ymin)
        return mt + (
            1.0
            - (math.log10(v) - math.log10(ymin))
            / (math.log10(ymax) - math.log10(ymin))
        ) * ph

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2:.1f}" y="26" text-anchor="middle" '
        f'font-family="Helvetica,Arial,sans-serif" font-size="14" font-weight="600" fill="#111">'
        f"{title}</text>",
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>',
        f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>',
        f'<text x="{ml-10}" y="{mt-8}" text-anchor="end" '
        f'font-family="Helvetica,Arial,sans-serif" font-size="11" fill="#444">initial residual</text>',
        f'<text x="{ml+pw/2:.1f}" y="{height-14}" text-anchor="middle" '
        f'font-family="Helvetica,Arial,sans-serif" font-size="11" fill="#444">iteration</text>',
    ]
    for yv in log_ticks(ymin, ymax):
        if yv < ymin * 0.999 or yv > ymax * 1.001:
            continue
        yy = Y(yv)
        parts.append(
            f'<line x1="{ml}" y1="{yy:.2f}" x2="{ml+pw}" y2="{yy:.2f}" stroke="#eee" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{ml-8}" y="{yy+3:.2f}" text-anchor="end" '
            f'font-family="Helvetica,Arial,sans-serif" font-size="10" fill="#555">{fmt_sci(yv)}</text>'
        )
    for i in range(9):
        t = xmin + (xmax - xmin) * i / 8
        xx = X(t)
        parts.append(
            f'<line x1="{xx:.2f}" y1="{mt}" x2="{xx:.2f}" y2="{mt+ph}" stroke="#f3f3f3" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{xx:.2f}" y="{mt+ph+16}" text-anchor="middle" '
            f'font-family="Helvetica,Arial,sans-serif" font-size="10" fill="#555">{t:.0f}</text>'
        )
    for key, color in SERIES:
        pts = [(r["time"], r[key]) for r in rows if key in r and r[key] > 0]
        if len(pts) < 2:
            continue
        if len(pts) > 2500:
            step = max(1, len(pts) // 2000)
            pts = pts[::step] + [pts[-1]]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{X(t):.2f},{Y(v):.2f}" for i, (t, v) in enumerate(pts)
        )
        parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round" opacity="0.92"/>'
        )
    lx, ly = ml + pw + 16, mt + 8
    parts.append(
        f'<text x="{lx}" y="{ly}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="11" font-weight="600" fill="#222">fields</text>'
    )
    for i, (key, color) in enumerate(SERIES):
        y = ly + 18 + i * 18
        parts.append(
            f'<line x1="{lx}" y1="{y}" x2="{lx+22}" y2="{y}" stroke="{color}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{lx+28}" y="{y+4}" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="11" fill="#222">{key}</text>'
        )
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    if not LOG.is_file():
        raise SystemExit(f"Missing {LOG}")
    rows = parse_residuals(LOG)
    if not rows:
        raise SystemExit("No residual rows parsed from log")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    keys = ["time"] + [k for k, _ in SERIES]
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})

    write_svg(
        OUT_SVG,
        rows,
        "Saiyad2022_rackLevel — residuals (buoyantBoussinesqSimpleFoam)",
    )
    print(f"Parsed {len(rows)} iterations  ({rows[0]['time']:.0f} → {rows[-1]['time']:.0f})")
    print(f"Wrote {OUT_CSV.relative_to(CASE)}")
    print(f"Wrote {OUT_SVG.relative_to(CASE)}")


if __name__ == "__main__":
    main()
