#!/usr/bin/env python3
"""Wrapper — ODT builder moved to Airflow-CFD/Report/scripts/build_odt_report.py."""

from pathlib import Path
import runpy

runpy.run_path(
    str(
        Path(__file__).resolve().parents[3]
        / "Report"
        / "scripts"
        / "build_odt_report.py"
    ),
    run_name="__main__",
)
