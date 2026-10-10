#!/usr/bin/env python3
"""Build Saiyad Fig.4 / Fig.5 / Fig.8 validation SVGs (CFD vs digitized experiment).

Experiment CSVs: Reports/data/experiment/
CFD: latest probes_simulators/T (see probe_utils.py)

Outputs:
  Reports/figures/cold_aisle_Tin_profile.svg
  Reports/figures/rack_T_locations.svg
  Reports/figures/Tin_by_simulator.svg
  Reports/figures/Tout_by_simulator.svg
  Reports/figures/Tin_Tout_history.svg
  Reports/data/cfd_Tin_Tout_latest.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_utils import (  # noqa: E402
    FIG4_LABELS,
    K_to_C,
    latest_probe_row,
    read_probe_history,
)

EXP = CASE / "Reports" / "data" / "experiment"
OUT_FIG = CASE / "Reports" / "figures"
OUT_DATA = CASE / "Reports" / "data"

EXP_COLOR = "#555555"
CFD_COLOR = "#d62728"
FONT = "Helvetica,Arial,sans-serif"


def read_exp_kv(path: Path, key: str, val: str) -> list[tuple[str, float]]:
    rows = []
    with path.open(newline="") as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows.append((row[key].strip(), float(row[val])))
    return rows


def svg_header(w: float, h: float, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{title}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{w/2:.1f}" y="26" text-anchor="middle" font-family="{FONT}" '
        f'font-size="14" font-weight="600" fill="#111">{title}</text>',
    ]


def axes(ml, mt, pw, ph, xmin, xmax, ymin, ymax, xlabel, ylabel) -> list[str]:
    parts = [
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>',
        f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>',
        f'<text x="{ml-8}" y="{mt-10}" text-anchor="end" font-family="{FONT}" '
        f'font-size="11" fill="#444">{ylabel}</text>',
        f'<text x="{ml+pw/2:.1f}" y="{mt+ph+36}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="11" fill="#444">{xlabel}</text>',
    ]
    return parts


def cfd_from_probes(row: dict[str, float] | None) -> dict[str, float] | None:
    if not row:
        return None
    need = [f"s{i}_in" for i in range(1, 5)] + [f"s{i}_out" for i in range(1, 5)]
    if any(k not in row for k in need):
        return None
    Tin = [K_to_C(row[f"s{i}_in"]) for i in range(1, 5)]
    Tout = [K_to_C(row[f"s{i}_out"]) for i in range(1, 5)]
    out = {
        "Tin": Tin,
        "Tout": Tout,
        "Tin_avg": sum(Tin) / 4.0,
        "Tout_avg": sum(Tout) / 4.0,
        "time": row["time"],
    }
    fig4 = []
    for lab in FIG4_LABELS:
        if lab in row:
            fig4.append(K_to_C(row[lab]))
    if fig4:
        out["fig4"] = fig4
    else:
        # Fallback: map 4 sim-inlet probes onto sensors 2,4,6,8
        out["fig4_fallback"] = {
            2: Tin[0],
            4: Tin[1],
            6: Tin[2],
            8: Tin[3],
        }
    return out


def fig4_sensor_z(i: int, z_max: float = 1.98) -> float:
    """Sensor i=1..8: uniform from tile inlet (z=0) to domain max Z."""
    return (i - 0.5) / 8.0 * z_max


def write_fig4(cfd: dict | None) -> None:
    exp = read_exp_kv(EXP / "fig4_Tin_profile_experiment.csv", "sensor", "T_C")
    # Digitized sensors 1..8 → z uniformly from inlet to max Z
    exp_pts = [(fig4_sensor_z(int(float(s))), T) for s, T in exp]
    w, h = 720, 480
    ml, mr, mt, mb = 70, 160, 48, 56
    pw, ph = w - ml - mr, h - mt - mb
    xmin, xmax = 0.0, 25.0
    z_max = 1.98
    ymin, ymax = 0.0, z_max

    def X(T: float) -> float:
        return ml + (T - xmin) / (xmax - xmin) * pw

    def Y(z: float) -> float:
        return mt + (1.0 - (z - ymin) / (ymax - ymin)) * ph

    title = "Cold-aisle rack inlet temperature vs height (sensors uniform 0→Zmax)"
    if cfd:
        title += f"  [iter {cfd['time']:.0f}]"
    parts = svg_header(w, h, title)
    parts += axes(
        ml, mt, pw, ph, xmin, xmax, ymin, ymax,
        "Rack air inlet temperature (°C)",
        "z (m)  inlet→max",
    )
    for T in range(0, int(xmax) + 1, 5):
        xx = X(float(T))
        parts.append(f'<line x1="{xx:.1f}" y1="{mt}" x2="{xx:.1f}" y2="{mt+ph}" stroke="#f0f0f0"/>')
        parts.append(
            f'<text x="{xx:.1f}" y="{mt+ph+16}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10" fill="#555">{T}</text>'
        )
    for z_tick in (0.0, 0.44, 0.88, 1.32, 1.76, 1.98):
        yy = Y(z_tick)
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+pw}" y2="{yy:.1f}" stroke="#f0f0f0"/>')
        parts.append(
            f'<text x="{ml-8}" y="{yy+3:.1f}" text-anchor="end" font-family="{FONT}" '
            f'font-size="10" fill="#555">{z_tick:g}</text>'
        )

    # Experiment polyline
    d = " ".join(
        f"{'M' if i == 0 else 'L'}{X(T):.2f},{Y(z):.2f}" for i, (z, T) in enumerate(exp_pts)
    )
    parts.append(
        f'<path d="{d}" fill="none" stroke="{EXP_COLOR}" stroke-width="2" '
        f'stroke-linejoin="round"/>'
    )
    for z, T in exp_pts:
        parts.append(
            f'<circle cx="{X(T):.2f}" cy="{Y(z):.2f}" r="4" fill="{EXP_COLOR}"/>'
        )

    # CFD at same uniform z stations
    if cfd and "fig4" in cfd:
        pts = [(fig4_sensor_z(i), T) for i, T in enumerate(cfd["fig4"], start=1)]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{X(T):.2f},{Y(z):.2f}" for i, (z, T) in enumerate(pts)
        )
        parts.append(
            f'<path d="{d}" fill="none" stroke="{CFD_COLOR}" stroke-width="2" '
            f'stroke-dasharray="6 3"/>'
        )
        for z, T in pts:
            parts.append(
                f'<circle cx="{X(T):.2f}" cy="{Y(z):.2f}" r="3.5" fill="none" '
                f'stroke="{CFD_COLOR}" stroke-width="1.8"/>'
            )
    elif cfd and "fig4_fallback" in cfd:
        pts = [(fig4_sensor_z(s), T) for s, T in sorted(cfd["fig4_fallback"].items())]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{X(T):.2f},{Y(z):.2f}" for i, (z, T) in enumerate(pts)
        )
        parts.append(
            f'<path d="{d}" fill="none" stroke="{CFD_COLOR}" stroke-width="2" '
            f'stroke-dasharray="6 3"/>'
        )
        for z, T in pts:
            parts.append(
                f'<circle cx="{X(T):.2f}" cy="{Y(z):.2f}" r="3.5" fill="none" '
                f'stroke="{CFD_COLOR}" stroke-width="1.8"/>'
            )

    lx, ly = ml + pw + 14, mt + 10
    parts.append(f'<text x="{lx}" y="{ly}" font-family="{FONT}" font-size="11" font-weight="600">legend</text>')
    parts.append(f'<line x1="{lx}" y1="{ly+18}" x2="{lx+22}" y2="{ly+18}" stroke="{EXP_COLOR}" stroke-width="2"/>')
    parts.append(f'<text x="{lx+28}" y="{ly+22}" font-family="{FONT}" font-size="11">experiment</text>')
    parts.append(
        f'<line x1="{lx}" y1="{ly+38}" x2="{lx+22}" y2="{ly+38}" stroke="{CFD_COLOR}" '
        f'stroke-width="2" stroke-dasharray="6 3"/>'
    )
    parts.append(f'<text x="{lx+28}" y="{ly+42}" font-family="{FONT}" font-size="11">OpenFOAM</text>')
    parts.append(
        f'<text x="{lx}" y="{ly+64}" font-family="{FONT}" font-size="9" fill="#888">'
        f'z=(i−0.5)/8×1.98</text>'
    )
    if cfd and "fig4" not in cfd:
        parts.append(
            f'<text x="{lx}" y="{ly+80}" font-family="{FONT}" font-size="9" fill="#888">'
            f'CFD: sim inlets→s2/4/6/8</text>'
        )
    parts.append("</svg>")
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    (OUT_FIG / "cold_aisle_Tin_profile.svg").write_text("\n".join(parts) + "\n")


def write_fig5(cfd: dict | None) -> None:
    exp = read_exp_kv(EXP / "fig5_rack_T_experiment.csv", "location", "T_C")
    labels = [loc for loc, _ in exp]
    exp_T = [T for _, T in exp]
    cfd_T = None
    if cfd:
        cfd_T = [
            cfd["Tin"][3],  # Sim 4 Inlet
            cfd["Tin"][1],  # Sim 2 Inlet
            cfd["Tin_avg"],
            cfd["Tout_avg"],
        ]
    w, h = 760, 420
    ml, mr, mt, mb = 64, 40, 48, 70
    pw, ph = w - ml - mr, h - mt - mb
    ymin, ymax = 0.0, 30.0
    n = len(labels)
    group_w = pw / n

    def Y(T: float) -> float:
        return mt + (1.0 - (T - ymin) / (ymax - ymin)) * ph

    title = "Rack air temperatures at selected locations"
    if cfd:
        title += f"  [iter {cfd['time']:.0f}]"
    parts = svg_header(w, h, title)
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>')
    parts.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>')
    for T in range(0, int(ymax) + 1, 5):
        yy = Y(float(T))
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+pw}" y2="{yy:.1f}" stroke="#eee"/>')
        parts.append(
            f'<text x="{ml-8}" y="{yy+3:.1f}" text-anchor="end" font-family="{FONT}" '
            f'font-size="10" fill="#555">{T}</text>'
        )
    parts.append(
        f'<text x="18" y="{mt+ph/2:.1f}" transform="rotate(-90 18,{mt+ph/2:.1f})" '
        f'text-anchor="middle" font-family="{FONT}" font-size="11" fill="#444">Temperature (°C)</text>'
    )

    bar_w = group_w * 0.28
    for i, lab in enumerate(labels):
        cx = ml + (i + 0.5) * group_w
        # exp
        x0 = cx - bar_w - 2
        y0 = Y(exp_T[i])
        parts.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{bar_w:.1f}" height="{mt+ph-y0:.1f}" '
            f'fill="{EXP_COLOR}" opacity="0.85"/>'
        )
        if cfd_T is not None:
            x1 = cx + 2
            y1 = Y(cfd_T[i])
            parts.append(
                f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{bar_w:.1f}" height="{mt+ph-y1:.1f}" '
                f'fill="{CFD_COLOR}" opacity="0.85"/>'
            )
        # short label
        short = lab.replace("Rack Air ", "").replace(" (Average)", " avg").replace("Simulator", "Sim")
        if len(short) > 18:
            short = short[:16] + "…"
        parts.append(
            f'<text x="{cx:.1f}" y="{mt+ph+18}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10" fill="#333">{short}</text>'
        )

    parts.append(f'<rect x="{ml}" y="{h-28}" width="12" height="12" fill="{EXP_COLOR}"/>')
    parts.append(f'<text x="{ml+18}" y="{h-18}" font-family="{FONT}" font-size="11">experiment</text>')
    parts.append(f'<rect x="{ml+120}" y="{h-28}" width="12" height="12" fill="{CFD_COLOR}"/>')
    parts.append(f'<text x="{ml+138}" y="{h-18}" font-family="{FONT}" font-size="11">OpenFOAM</text>')
    parts.append("</svg>")
    (OUT_FIG / "rack_T_locations.svg").write_text("\n".join(parts) + "\n")


def write_fig8_bars(
    out_name: str,
    title_base: str,
    exp_path: Path,
    cfd_vals: list[float] | None,
    ymax: float,
    iter_t: float | None,
) -> None:
    exp = read_exp_kv(exp_path, "simulator", "T_C")
    labels = [lab.replace("Sim ", "") for lab, _ in exp]
    exp_T = [T for _, T in exp]
    w, h = 640, 400
    ml, mr, mt, mb = 56, 30, 48, 56
    pw, ph = w - ml - mr, h - mt - mb
    ymin = 0.0
    n = 4
    group_w = pw / n
    bar_w = group_w * 0.28

    def Y(T: float) -> float:
        return mt + (1.0 - (T - ymin) / (ymax - ymin)) * ph

    title = title_base
    if iter_t is not None:
        title += f"  [iter {iter_t:.0f}]"
    parts = svg_header(w, h, title)
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>')
    parts.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#333" stroke-width="1.2"/>')
    for T in range(0, int(ymax) + 1, 5):
        yy = Y(float(T))
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+pw}" y2="{yy:.1f}" stroke="#eee"/>')
        parts.append(
            f'<text x="{ml-8}" y="{yy+3:.1f}" text-anchor="end" font-family="{FONT}" '
            f'font-size="10" fill="#555">{T}</text>'
        )
    parts.append(
        f'<text x="16" y="{mt+ph/2:.1f}" transform="rotate(-90 16,{mt+ph/2:.1f})" '
        f'text-anchor="middle" font-family="{FONT}" font-size="11" fill="#444">Temperature (°C)</text>'
    )
    parts.append(
        f'<text x="{ml+pw/2:.1f}" y="{h-14}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="11" fill="#444">Server simulator</text>'
    )

    for i in range(n):
        cx = ml + (i + 0.5) * group_w
        x0 = cx - bar_w - 2
        y0 = Y(exp_T[i])
        parts.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{bar_w:.1f}" height="{mt+ph-y0:.1f}" '
            f'fill="{EXP_COLOR}" opacity="0.85"/>'
        )
        if cfd_vals is not None:
            x1 = cx + 2
            y1 = Y(cfd_vals[i])
            parts.append(
                f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{bar_w:.1f}" height="{mt+ph-y1:.1f}" '
                f'fill="{CFD_COLOR}" opacity="0.85"/>'
            )
        parts.append(
            f'<text x="{cx:.1f}" y="{mt+ph+18}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="12" fill="#333">{labels[i]}</text>'
        )

    parts.append(f'<rect x="{ml}" y="32" width="12" height="12" fill="{EXP_COLOR}"/>')
    parts.append(f'<text x="{ml+18}" y="42" font-family="{FONT}" font-size="11">experiment</text>')
    parts.append(f'<rect x="{ml+120}" y="32" width="12" height="12" fill="{CFD_COLOR}"/>')
    parts.append(f'<text x="{ml+138}" y="42" font-family="{FONT}" font-size="11">OpenFOAM k-ε</text>')
    parts.append("</svg>")
    (OUT_FIG / out_name).write_text("\n".join(parts) + "\n")


def write_cfd_csv(cfd: dict | None) -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    path = OUT_DATA / "cfd_Tin_Tout_latest.csv"
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["quantity", "Sim1", "Sim2", "Sim3", "Sim4", "avg", "iteration"])
        if not cfd:
            return
        w.writerow(
            ["Tin_C", *[f"{v:.4f}" for v in cfd["Tin"]], f"{cfd['Tin_avg']:.4f}", f"{cfd['time']:.0f}"]
        )
        w.writerow(
            ["Tout_C", *[f"{v:.4f}" for v in cfd["Tout"]], f"{cfd['Tout_avg']:.4f}", f"{cfd['time']:.0f}"]
        )


def write_Tin_Tout_history_svg() -> None:
    """Live history of avg Tin/Tout vs iteration (with experiment targets as dashed lines)."""
    hist = read_probe_history()
    if len(hist) < 2:
        return
    exp_in = read_exp_kv(EXP / "fig8a_Tin_experiment.csv", "simulator", "T_C")
    exp_out = read_exp_kv(EXP / "fig8b_Tout_experiment.csv", "simulator", "T_C")
    Tin_exp_avg = sum(T for _, T in exp_in) / 4.0
    Tout_exp_avg = sum(T for _, T in exp_out) / 4.0

    times = [r["time"] for r in hist]
    Tin = [sum(K_to_C(r[f"s{i}_in"]) for i in range(1, 5)) / 4.0 for r in hist]
    Tout = [sum(K_to_C(r[f"s{i}_out"]) for i in range(1, 5)) / 4.0 for r in hist]

    w, h = 820, 420
    ml, mr, mt, mb = 64, 150, 44, 52
    pw, ph = w - ml - mr, h - mt - mb
    xmin, xmax = min(times), max(times)
    if xmax <= xmin:
        xmax = xmin + 1.0
    ymin = 0.0
    ymax = max(max(Tin), max(Tout), Tin_exp_avg, Tout_exp_avg) + 1.0
    if ymax <= ymin:
        ymax = 30.0

    def X(t: float) -> float:
        return ml + (t - xmin) / (xmax - xmin) * pw

    def Y(v: float) -> float:
        return mt + (1.0 - (v - ymin) / (ymax - ymin)) * ph

    title = f"Avg rack Tin / Tout vs iteration  [last {times[-1]:.0f}]"
    parts = svg_header(w, h, title)
    parts += axes(ml, mt, pw, ph, xmin, xmax, ymin, ymax, "iteration", "T (°C)")
    for i in range(6):
        v = ymin + (ymax - ymin) * i / 5
        yy = Y(v)
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+pw}" y2="{yy:.1f}" stroke="#eee"/>')
        parts.append(
            f'<text x="{ml-8}" y="{yy+3:.1f}" text-anchor="end" font-family="{FONT}" '
            f'font-size="10" fill="#555">{v:.1f}</text>'
        )
    for i in range(9):
        t = xmin + (xmax - xmin) * i / 8
        xx = X(t)
        parts.append(
            f'<text x="{xx:.1f}" y="{mt+ph+16}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10" fill="#555">{t:.0f}</text>'
        )

    # experiment targets
    for T, label, dash in (
        (Tin_exp_avg, "Tin exp avg", "4 3"),
        (Tout_exp_avg, "Tout exp avg", "4 3"),
    ):
        yy = Y(T)
        parts.append(
            f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+pw}" y2="{yy:.1f}" '
            f'stroke="#888" stroke-width="1.2" stroke-dasharray="{dash}"/>'
        )

    def path(vals: list[float], color: str) -> None:
        nonlocal parts
        if len(vals) > 2500:
            step = max(1, len(vals) // 2000)
            idx = list(range(0, len(vals), step))
            if idx[-1] != len(vals) - 1:
                idx.append(len(vals) - 1)
        else:
            idx = range(len(vals))
        d = " ".join(
            f"{'M' if j == 0 else 'L'}{X(times[i]):.2f},{Y(vals[i]):.2f}"
            for j, i in enumerate(idx)
        )
        parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linejoin="round"/>'
        )

    path(Tin, "#1f77b4")
    path(Tout, "#d62728")

    lx = ml + pw + 12
    parts.append(f'<text x="{lx}" y="{mt+12}" font-family="{FONT}" font-size="11" font-weight="600">series</text>')
    for i, (lab, col) in enumerate(
        (("Tin avg", "#1f77b4"), ("Tout avg", "#d62728"), ("exp avg", "#888"))
    ):
        y = mt + 32 + i * 18
        parts.append(f'<line x1="{lx}" y1="{y}" x2="{lx+22}" y2="{y}" stroke="{col}" stroke-width="2"/>')
        parts.append(f'<text x="{lx+28}" y="{y+4}" font-family="{FONT}" font-size="11">{lab}</text>')
    parts.append("</svg>")
    (OUT_FIG / "Tin_Tout_history.svg").write_text("\n".join(parts) + "\n")

    # Also dump history CSV
    with (OUT_DATA / "Tin_Tout_history.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "Tin_avg_C", "Tout_avg_C"])
        for t, ti, to in zip(times, Tin, Tout):
            w.writerow([f"{t:.0f}", f"{ti:.4f}", f"{to:.4f}"])


def main() -> int:
    if not (EXP / "fig8a_Tin_experiment.csv").is_file():
        print(f"ERROR: missing experiment CSVs under {EXP}", file=sys.stderr)
        return 1

    row = latest_probe_row()
    cfd = cfd_from_probes(row)
    OUT_FIG.mkdir(parents=True, exist_ok=True)

    write_fig4(cfd)
    write_fig5(cfd)
    write_fig8_bars(
        "Tin_by_simulator.svg",
        "Steady-state average rack air inlet temperatures by simulator",
        EXP / "fig8a_Tin_experiment.csv",
        cfd["Tin"] if cfd else None,
        25.0,
        cfd["time"] if cfd else None,
    )
    write_fig8_bars(
        "Tout_by_simulator.svg",
        "Steady-state average rack air outlet temperatures by simulator",
        EXP / "fig8b_Tout_experiment.csv",
        cfd["Tout"] if cfd else None,
        30.0,
        cfd["time"] if cfd else None,
    )
    write_cfd_csv(cfd)
    write_Tin_Tout_history_svg()

    print("Wrote Reports/figures/cold_aisle_Tin_profile.svg")
    print("Wrote Reports/figures/rack_T_locations.svg")
    print("Wrote Reports/figures/Tin_by_simulator.svg")
    print("Wrote Reports/figures/Tout_by_simulator.svg")
    print("Wrote Reports/figures/Tin_Tout_history.svg")
    if cfd:
        print(
            f"CFD @ iter {cfd['time']:.0f}: "
            f"Tin={[round(t,2) for t in cfd['Tin']]}  "
            f"Tout={[round(t,2) for t in cfd['Tout']]}"
        )
    else:
        print("NOTE: no probe T yet — experiment-only frames written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
