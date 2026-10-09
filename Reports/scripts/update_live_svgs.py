#!/usr/bin/env python3
"""Refresh residuals + validation SVGs every N solver iterations (default 100).

Usage (from case dir or via ensure-svg-watch):
  python3 Reports/scripts/update_live_svgs.py
  python3 Reports/scripts/update_live_svgs.py --force
  python3 Reports/scripts/update_live_svgs.py --interval 100
"""

from __future__ import annotations

import argparse
import fcntl
import subprocess
import sys
import time
from pathlib import Path

CASE = Path(__file__).resolve().parents[2]
SCRIPTS = CASE / "Reports" / "scripts"
DATA = CASE / "Reports" / "data"
STAMP = DATA / ".svg_watch_iter"
LOCK = DATA / ".svg_watch.lock"
LOG = CASE / "log.buoyantBoussinesqSimpleFoam"


def last_log_time() -> float | None:
    if not LOG.is_file():
        return None
    last = None
    with LOG.open(errors="replace") as fh:
        for line in fh:
            if line.startswith("Time = "):
                try:
                    last = float(line.split("=", 1)[1].strip())
                except ValueError:
                    continue
    return last


def read_stamp() -> int:
    try:
        return int(STAMP.read_text().strip())
    except (OSError, ValueError):
        return -1


def write_stamp(bucket: int) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(f"{bucket}\n")


def run_script(name: str) -> int:
    script = SCRIPTS / name
    if not script.is_file():
        print(f"NOTE: missing {name}")
        return 1
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=str(CASE),
        check=False,
    ).returncode


def update(interval: int, force: bool) -> int:
    t = last_log_time()
    if t is None:
        if force:
            print("NOTE: no solver log; forcing SVG refresh from probes if any")
            bucket = 0
        else:
            print("SKIP: no log.buoyantBoussinesqSimpleFoam yet")
            return 0
    else:
        bucket = int(t) // interval * interval

    prev = read_stamp()
    if prev >= 0 and bucket < prev:
        print(f"NOTE: log restarted (bucket {bucket} < stamp {prev}); resetting")
        write_stamp(-1)
        prev = -1
    if not force and bucket <= prev:
        return 0

    # Idle finished runs: do not thrash
    if not force and LOG.is_file():
        age = time.time() - LOG.stat().st_mtime
        if age > 900 and prev >= 0 and bucket == prev:
            return 0

    DATA.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("SKIP: another updater is running")
            return 0

        print(f"==> Saiyad2022_rackLevel SVGs @ iter {t if t is not None else '?'} (bucket {bucket})")
        rc1 = run_script("make_residual_svg.py")
        if rc1 != 0:
            print(f"NOTE: make_residual_svg rc={rc1}")
        rc2 = run_script("make_validation_svgs.py")
        if rc2 != 0:
            print(f"NOTE: make_validation_svgs rc={rc2}")
        write_stamp(bucket)
        print(f"OK: Reports/figures refreshed (bucket {bucket})")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=100)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    n = update(args.interval, args.force)
    return 0 if n or not args.force else 1


if __name__ == "__main__":
    raise SystemExit(main())
