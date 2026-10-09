#!/usr/bin/env python3
"""Compute Tin/Tout, SHI, RTI, beta from Saiyad2022_rackLevel probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
PROBE_DIR = CASE / "postProcessing" / "probes_simulators"
TARGETS = CASE / "validation" / "targets.json"

# Probe order in controlDict
LABELS = [
    "s1_in", "s2_in", "s3_in", "s4_in",
    "s1_out", "s2_out", "s3_out", "s4_out",
    "cold_mid", "cold_z07", "cold_z078", "hot_mid",
]


def latest_probe_file(name: str) -> Path:
    if not PROBE_DIR.is_dir():
        raise FileNotFoundError(f"Missing {PROBE_DIR} — run the case first")
    times = sorted(
        (p for p in PROBE_DIR.iterdir() if p.is_dir()),
        key=lambda p: float(p.name),
    )
    if not times:
        raise FileNotFoundError(f"No time dirs in {PROBE_DIR}")
    f = times[-1] / name
    if not f.is_file():
        raise FileNotFoundError(f)
    return f


def read_last_T() -> dict[str, float]:
    path = latest_probe_file("T")
    last = None
    with path.open() as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            last = line.split()
    if last is None:
        raise RuntimeError(f"No data in {path}")
    # time + N probe values
    vals = [float(x) for x in last[1:]]
    if len(vals) < 8:
        raise RuntimeError(f"Expected ≥8 T probes, got {len(vals)}")
    return {lab: vals[i] for i, lab in enumerate(LABELS[: len(vals)])}


def main() -> int:
    targets = json.loads(TARGETS.read_text())
    T_sup = targets["operating_point"]["T_supply_C"] + 273.15
    T = read_last_T()

    Tin = [T[f"s{i}_in"] for i in range(1, 5)]
    Tout = [T[f"s{i}_out"] for i in range(1, 5)]
    Tin_avg = sum(Tin) / 4.0
    Tout_avg = sum(Tout) / 4.0

    # beta(z) = (Tin(z) - Tsup) / (Tout_avg - Tsup)  [paper Eq. 3 uses local Tout-Tsup]
    dT_rack = Tout_avg - T_sup
    beta = []
    for i, tin in enumerate(Tin, start=1):
        b = (tin - T_sup) / dT_rack if abs(dT_rack) > 1e-6 else float("nan")
        beta.append(b)

    # SHI ≈ (Tin_avg - Tsup) / (Tout_avg - Tsup)
    shi = (Tin_avg - T_sup) / dT_rack if abs(dT_rack) > 1e-6 else float("nan")

    # RTI needs CRAC return; use return-outlet probe proxy if present
    T_ret = T.get("hot_mid", Tout_avg)
    rti = 100.0 * (T_ret - T_sup) / dT_rack if abs(dT_rack) > 1e-6 else float("nan")

    report = {
        "T_sup_K": T_sup,
        "Tin_K": {f"s{i}": Tin[i - 1] for i in range(1, 5)},
        "Tout_K": {f"s{i}": Tout[i - 1] for i in range(1, 5)},
        "Tin_avg_C": Tin_avg - 273.15,
        "Tout_avg_C": Tout_avg - 273.15,
        "beta": {f"s{i}": beta[i - 1] for i in range(1, 5)},
        "SHI": shi,
        "RTI_percent_proxy": rti,
        "targets_beta_experiment": targets["beta_index"]["experiment"],
        "targets_beta_paper_kEpsilon": targets["beta_index"]["paper_kEpsilon"],
        "acceptance_TinTout_C": targets["acceptance"]["mean_Tin_Tout_abs_error_C"],
    }

    out = CASE / "Reports" / "data" / "metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    print(f"\nWrote {out}")
    print(
        "Compare beta s1/s4 to experiment "
        f"{targets['beta_index']['experiment']} "
        f"and paper k-ε {targets['beta_index']['paper_kEpsilon']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
