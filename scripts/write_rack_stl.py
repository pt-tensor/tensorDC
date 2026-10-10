#!/usr/bin/env python3
"""Backward-compatible wrapper — prefer write_dummy_stl.py. """

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("write_dummy_stl.py")), run_name="__main__")
