# Saiyad et al. (2022) — Rack-level airflow validation

OpenFOAM recreation of the **3-rack** CEETHERM domain from:

> Saiyad, A., Fulpagare, Y. & Bhargav, A. (2022). Comparison of detached eddy
> simulation and standard k−ε RANS model for rack-level airflow analysis inside
> a data center. *Building Simulation*, 15, 1595–1610.
> https://doi.org/10.1007/s12273-021-0879-3

This case implements steady RANS with **`RNGkEpsilon`** (`buoyantBoussinesqSimpleFoam`),
using the same turbulence/wall-function setup as the HVAC Nielsen validation cases
(`Validation-study/OpenFOAM/HVAC`). Geometry/BCs follow Table 2 and §3 of Saiyad et al.;
note the paper’s published RANS baseline was standard k−ε — RNG is intentional here.
DES can be added later as a transient companion.

**Agent / modeller resume:** see [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) (geometry blanks vs paper,
fans/mass balance, porous mapping, heat Su, remesh pitfalls).

## Geometry (paper §3)

| Quantity | Value |
|----------|------:|
| Domain (L × B × H) | 2.2 m × 1.82 m × **1.98 m** (Fig. 1) |
| Cold aisle (x) | 0 – 0.6 m |
| Rack depth (x) | 0.6 – 1.6 m (1.0 m) |
| Hot aisle (x) | 1.6 – 2.2 m |
| Neighbour racks (y) | left 0–0.645 m; right 1.175–1.82 m |
| Mid simulators (y) | 0.645 – 1.175 m (**width 0.53 m**) |
| Each simulator (z) | **height 0.44 m** (10U): s1 0–0.44, s2 0.44–0.88, s3 0.88–1.32, s4 1.32–1.76 |
| Overhead | 1.76 – 1.98 m — **open fluid** over cold, racks, and hot (paper cold↔hot link) |

**Flow path (paper Fig. 2):**
- Three porous rack columns in the fluid mesh (`rackLeft`, `sim1`…`sim4`, `rackRight`)
- Table 2 Darcy–Forchheimer (streamwise Pv/Pi; amplified transverse)
- Exit-fan cellZones at hot faces; solid floors between mid sims; open overhead
- Cold/hot faces of all racks open for through-flow

Coordinate convention (OpenFOAM): **x** through racks, **y** along rack row, **z** up, **g = −z**.

### Why ParaView shows only a box

Racks are **porous cellZones** inside one fluid mesh (same modelling as the paper) — not solid walls — so the `.foam` boundaries are only `tileInlet`, `returnOutlet`, and the room walls.

**See the racks:**

1. Open `foam.foam` → *Mesh Regions* → enable **Cell Zones** `rackLeft`, `sim1`…`sim4`, `rackRight`. Opacity ~0.3.
2. Or load dummy STLs from `geometry/` (Outline / Wireframe / Surface ~0.3):
   `racks.stl`, `simulators.stl`, `neighbours.stl`, `coldAisle.stl`, `hotAisle.stl`,
   `overhead.stl`, `tileInlet.stl`, `returnOutlet.stl`, `fanExits.stl`, `baffles.stl`, `domain.stl`.
   Regenerate with `python3 scripts/write_dummy_stl.py` (also run by `./buildMesh`).
3. Or run `./scripts/exportRacksVTK` and open the `VTK/` files.

## Boundary conditions (Table 2 / Fig. 7)

| Patch | BC |
|-------|-----|
| `tileInlet` (cold-aisle floor) | U = (0 0 1.54) m/s, T = 290.15 K (17 °C) |
| `returnOutlet` (hot-aisle **ceiling**) | p_rgh = 0, inletOutlet for U/T |
| Other walls | no-slip, adiabatic (`floorHot` = hot-aisle floor) |

Plenum / CRAC omitted as in the paper; supply through cold-aisle tiles, return through hot-aisle ceiling.

## Porous servers + heat (Table 2)

STAR-CCM+ resistances → OpenFOAM Darcy–Forchheimer (`explicitPorositySource`):

- Viscous Pv = 0.50 kg/(m³·s) → `d_x ≈ 2.78e4` 1/m² (streamwise)
- Inertial Pi = 0.05 kg/m⁴ → `f_x ≈ 0.083` 1/m (streamwise)
- Transverse `d,f` amplified (`-1000` OF convention) so flow is front→back
- STAR **85% porosity** = region fluid fraction; resistances already include packing (not re-scaled)

| Zone | Heat load |
|------|----------:|
| `sim1`…`sim4` | **2500 W each** (10 kW mid rack) |
| `rackLeft`, `rackRight` | **10000 W each** (Table 2 neighbouring racks) |

**Fans (paper: curve at server exit):** `meanVelocityForce` on thin exit zones
`sim1Fan`…`sim4Fan`, `rackLeftFan`, `rackRightFan` (`x=1.55–1.60`). Mid
`Ubar=(1.5 0 0)` (Fig.5 ΔT≈6 K); neighbours `Ubar=(0.4 0 0)` so tile mass is not
over-driven (stand-in for a self-balancing fan curve).

## Quick start

```bash
./buildMesh
./Run          # NP=4 by default; NP=1 for serial
```

Via repo docker wrapper (from this directory):

```bash
./buildMesh
./Run
```

## Live validation SVGs (every 100 iterations)

Digitized experiment (manual) from the paper lives in
`References/Airflow-CFD/Data-…/` and is copied to `Reports/data/experiment/`.

On the **Mac host** (not inside docker):

```bash
./ensure-svg-watch --background   # also started by ./Run when SVG_WATCH≠0
```

Refreshes every 100 solver iterations:

| Figure | SVG |
|--------|-----|
| Residuals | `Reports/figures/residuals.svg` |
| Cold-aisle Tin profile | `Reports/figures/cold_aisle_Tin_profile.svg` |
| Rack T locations | `Reports/figures/rack_T_locations.svg` |
| Tin by simulator | `Reports/figures/Tin_by_simulator.svg` |
| Tout by simulator | `Reports/figures/Tout_by_simulator.svg` |
| Tin/Tout history | `Reports/figures/Tin_Tout_history.svg` |

```bash
python3 Reports/scripts/update_live_svgs.py --force   # one-shot refresh
```

## Validation report (ODT)

Report lives under the parent Airflow-CFD folder (Electronic-Cooling / HVAC style):

| File | Role |
|------|------|
| [`../Report/tensorDataCenterCooling-Validation-Report.odt`](../Report/tensorDataCenterCooling-Validation-Report.odt) | Validation report |
| [`../Report/scripts/build_odt_report.py`](../Report/scripts/build_odt_report.py) | Rebuild (crops white padding; uses `../Report/Images/`) |

```bash
python3 Reports/scripts/make_validation_svgs.py
python3 ../Report/scripts/build_odt_report.py
```

Header publisher line: **Tensor Publisher. 2026**.

## Validation targets

See `validation/targets.json` and `validation/metrics.py`.

Primary checks vs experiment / paper:

1. Mean rack inlet & outlet air temperatures within **~1.4 °C** of experiment
2. **β** index: β(s1)≈0.15 (exp), β(s4)≈0.48 (exp); k−ε paper: 0 / 0.35
3. SHI / RTI trends (paper Fig. 18; absolute SHI not tabulated in text)

Probe locations sample cold-aisle rack faces ahead of / behind each simulator band (s1–s4).

## Outputs

- `postProcessing/` — patch averages, probes, fieldMinMax
- `Reports/` — place figures / summarised metrics after post-processing
