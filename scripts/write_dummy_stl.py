#!/usr/bin/env python3
"""Write dummy STL boxes for ParaView overlay (porous zones are not walls).

Outputs under geometry/:
  domain.stl          — room outer box
  coldAisle.stl       — cold aisle fluid column
  hotAisle.stl        — hot aisle fluid column
  racks.stl           — all IT porous volumes (neighbours + 4 sims)
  neighbours.stl      — rackLeft + rackRight only
  simulators.stl      — sim1–sim4 only
  overhead.stl        — open overhead above racks (cold↔hot link)
  tileInlet.stl       — cold-aisle floor supply patch (thin slab)
  returnOutlet.stl    — hot-aisle ceiling return (thin slab)
  fanExits.stl        — exit-fan cellZones (x=1.55–1.60)
  baffles.stl         — mid-sim floor baffles (thin slabs)

Load foam.foam + any of these as Outline / Wireframe / Surface.
"""

from __future__ import annotations

from pathlib import Path

GEOM = Path(__file__).resolve().parents[1] / "geometry"

# Domain (matches blockMeshDict)
X0, X_COLD, X_HOT, X1 = 0.0, 0.6, 1.6, 2.2
Y0, Y_MID0, Y_MID1, Y1 = 0.0, 0.645, 1.175, 1.82
Z0, Z_IT, Z1 = 0.0, 1.76, 1.98
SIM_Z = (0.0, 0.44, 0.88, 1.32, 1.76)
FAN_X0, FAN_X1 = 1.55, 1.60
SLAB = 0.01  # thin patch thickness for inlet/outlet/baffles


def facet(n, a, b, c) -> str:
    return (
        f"  facet normal {n[0]} {n[1]} {n[2]}\n"
        f"    outer loop\n"
        f"      vertex {a[0]} {a[1]} {a[2]}\n"
        f"      vertex {b[0]} {b[1]} {b[2]}\n"
        f"      vertex {c[0]} {c[1]} {c[2]}\n"
        f"    endloop\n"
        f"  endfacet\n"
    )


def box_facets(x0, x1, y0, y1, z0, z1) -> str:
    p = {
        "000": (x0, y0, z0),
        "100": (x1, y0, z0),
        "110": (x1, y1, z0),
        "010": (x0, y1, z0),
        "001": (x0, y0, z1),
        "101": (x1, y0, z1),
        "111": (x1, y1, z1),
        "011": (x0, y1, z1),
    }
    faces = [
        ((-1, 0, 0), "000", "010", "011", "001"),
        ((1, 0, 0), "100", "101", "111", "110"),
        ((0, -1, 0), "000", "001", "101", "100"),
        ((0, 1, 0), "010", "110", "111", "011"),
        ((0, 0, -1), "000", "100", "110", "010"),
        ((0, 0, 1), "001", "011", "111", "101"),
    ]
    out = []
    for n, a, b, c, d in faces:
        out.append(facet(n, p[a], p[b], p[c]))
        out.append(facet(n, p[a], p[c], p[d]))
    return "".join(out)


def write_stl(name: str, boxes: list[tuple[float, float, float, float, float, float]]) -> Path:
    path = GEOM / f"{name}.stl"
    parts = [f"solid {name}\n"]
    for x0, x1, y0, y1, z0, z1 in boxes:
        parts.append(box_facets(x0, x1, y0, y1, z0, z1))
    parts.append(f"endsolid {name}\n")
    path.write_text("".join(parts))
    return path


def main() -> None:
    GEOM.mkdir(parents=True, exist_ok=True)

    written = []

    written.append(
        write_stl("domain", [(X0, X1, Y0, Y1, Z0, Z1)])
    )
    written.append(
        write_stl("coldAisle", [(X0, X_COLD, Y0, Y1, Z0, Z1)])
    )
    written.append(
        write_stl("hotAisle", [(X_HOT, X1, Y0, Y1, Z0, Z1)])
    )

    neighbours = [
        (X_COLD, X_HOT, Y0, Y_MID0, Z0, Z_IT),
        (X_COLD, X_HOT, Y_MID1, Y1, Z0, Z_IT),
    ]
    sims = [
        (X_COLD, X_HOT, Y_MID0, Y_MID1, SIM_Z[i], SIM_Z[i + 1])
        for i in range(4)
    ]
    written.append(write_stl("neighbours", neighbours))
    written.append(write_stl("simulators", sims))
    written.append(write_stl("racks", neighbours + sims))

    # Overhead fluid above all three rack columns
    written.append(
        write_stl("overhead", [(X_COLD, X_HOT, Y0, Y1, Z_IT, Z1)])
    )

    written.append(
        write_stl("tileInlet", [(X0, X_COLD, Y0, Y1, Z0, Z0 + SLAB)])
    )
    written.append(
        write_stl("returnOutlet", [(X_HOT, X1, Y0, Y1, Z1 - SLAB, Z1)])
    )

    fan_exits = [
        (FAN_X0, FAN_X1, Y0, Y_MID0, Z0, Z_IT),
        *[
            (FAN_X0, FAN_X1, Y_MID0, Y_MID1, SIM_Z[i], SIM_Z[i + 1])
            for i in range(4)
        ],
        (FAN_X0, FAN_X1, Y_MID1, Y1, Z0, Z_IT),
    ]
    written.append(write_stl("fanExits", fan_exits))

    baffles = [
        (X_COLD, X_HOT, Y_MID0, Y_MID1, z - SLAB / 2, z + SLAB / 2)
        for z in (0.44, 0.88, 1.32)
    ]
    written.append(write_stl("baffles", baffles))

    # Keep legacy script path in sync
    legacy = Path(__file__).resolve().parent / "write_rack_stl.py"
    if legacy.is_file():
        # racks.stl already written above
        pass

    print(f"Wrote {len(written)} STL files under {GEOM}/")
    for p in written:
        print(f"  {p.name}")
    print(
        "\nParaView: open foam.foam, then File→Open geometry/*.stl "
        "(Outline / Wireframe / Surface opacity ~0.3)."
    )


if __name__ == "__main__":
    main()
