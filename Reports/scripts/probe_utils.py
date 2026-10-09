#!/usr/bin/env python3
"""Read probes_simulators T history from postProcessing (live-friendly)."""

from __future__ import annotations

from pathlib import Path

CASE = Path(__file__).resolve().parents[2]
PROBE_DIR = CASE / "postProcessing" / "probes_simulators"

# Order must match system/controlDict probes_simulators
LABELS = [
    "s1_in",
    "s2_in",
    "s3_in",
    "s4_in",
    "s1_out",
    "s2_out",
    "s3_out",
    "s4_out",
    "cold_mid",
    "cold_z07",
    "cold_z078",
    "hot_mid",
]

# Optional Fig.4 profile probes (added when present in controlDict)
FIG4_LABELS = [f"fig4_s{i}" for i in range(1, 9)]


def find_probe_T() -> Path | None:
    if not PROBE_DIR.is_dir():
        return None
    # Prefer highest time directory that has T
    times = sorted(
        (p for p in PROBE_DIR.iterdir() if p.is_dir()),
        key=lambda p: float(p.name),
    )
    for tdir in reversed(times):
        f = tdir / "T"
        if f.is_file():
            return f
    # Fallback: any T under probes
    for f in PROBE_DIR.rglob("T"):
        if f.is_file():
            return f
    return None


def read_probe_history(path: Path | None = None) -> list[dict[str, float]]:
    path = path or find_probe_T()
    if path is None:
        return []
    rows: list[dict[str, float]] = []
    with path.open(errors="replace") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                t = float(parts[0])
                vals = [float(x) for x in parts[1:]]
            except ValueError:
                continue
            row: dict[str, float] = {"time": t}
            for i, lab in enumerate(LABELS):
                if i < len(vals):
                    row[lab] = vals[i]
            # Extra probes after the base 12 → Fig.4 sensors
            base = len(LABELS)
            for j, lab in enumerate(FIG4_LABELS):
                idx = base + j
                if idx < len(vals):
                    row[lab] = vals[idx]
            rows.append(row)
    # Deduplicate by time (keep last)
    by_t = {r["time"]: r for r in rows}
    return [by_t[t] for t in sorted(by_t)]


def latest_probe_row() -> dict[str, float] | None:
    hist = read_probe_history()
    return hist[-1] if hist else None


def K_to_C(T: float) -> float:
    return T - 273.15
