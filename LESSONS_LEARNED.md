# Lessons learned — Saiyad2022 rack-level OpenFOAM validation

Resume of agent/human work on recreating Saiyad, Fulpagare & Bhargav (2022)
*Building Simulation* 15:1595–1610. Use this before changing mesh, porous, fans,
baffles, or “paper fidelity” shortcuts.

Reference notes:
`../../References/Airflow-CFD/Comparison of detached eddy simulation and standard k-epsilon RANS model for rack-level airflow analysis inside a data center.md`

---

## 1. Geometry: what the paper actually means

| Region | Paper definition | Wrong shortcut we tried |
|--------|------------------|-------------------------|
| **Neighbour racks** | Fluid + **porous** real servers, **10 kW** each, fan at exits | Solid blanks / omit mesh → dead zones, low \|U\| |
| **Overhead / “top”** | Cold & hot aisles **connected above rack tops** (“internal BCs” = open fluid interface, not a wall) | Solid canopy (`rackCanopy`) → kills recirculation / Fig.4 Tin shape |
| **Mid rack** | Four stacked 10U simulators, porous + heat + exit fans | Sealing sides/top or blanking neighbours changes Tin/Tout vs experiment |

**“Internal boundary conditions” (top)** ≠ wall. Means continuous fluid over the cabinets (STAR-CCM+ internal interface). In OpenFOAM: keep OH hex blocks over left/mid/right racks; do **not** invent an impermeable lid.

**Domain height:** paper text quotes **2.3 m**; this case uses **1.98 m** (facility Fig.1). Simulator text **1×0.6×0.5 m** vs case **1.0×0.53×0.44 m** (10U). Document intentional choices; don’t silently mix both.

After removing side rack blocks, **only put wall faces that are owned by remaining cells** on patches — orphan faces → `blockMesh` FOAM FATAL (`face … does not have neighbour cell face`).

---

## 2. Heat loads (Table 2)

- **Server simulator heat load 2500 W** → treat as **per simulator** → mid rack **10 kW** (matches Fig.5 ~6 K ΔT at ~1.5 m/s through-flow).
- **Neighboring rack heat load 10000 W** → **per neighbour column**.
- Boussinesq `scalarSemiImplicitSource` on `T`, `volumeMode absolute`:
  - `Su = Q / (ρ Cp)` with ρ=1.2, Cp=1005 → `2500 → 2.072968`, `10000 → 8.291874`.
- Paper lists solid ρ/Cp/k for servers; we inject heat into **air T only** (no conjugate solid). Same Watts, different physics detail.

---

## 3. Porous treatment

- Table 2: Pv=0.50 → `d_x ≈ 27778`; Pi=0.05 → `f_x ≈ 0.0833` (Darcy–Forchheimer).
- STAR **85% porosity** = fluid volume fraction of the region; resistances already include packing — **do not** multiply d,f by (1−γ) again.
- Prefer **streamwise** paper coeffs + **amplified transverse** (`d,f` with OpenFOAM `-1000` convention) so flow is front→back through servers.
- Isotropic d=f in X,Y,Z allows unwanted cross-flow inside cabinets unless baffles block it.
- OpenFOAM still solves turbulence **inside** porous cells (STAR often does not) — remaining fidelity gap; no free freeze without custom code.

---

## 4. Fan model (highest impact on Tin/mass balance)

Paper: manufacturer **fan curve at each server EXIT** (Nelson 2007), all racks.

| Approach | Result |
|----------|--------|
| `meanVelocityForce` on **whole** mid zones only, Ubar=1.5 | Approx mid ΔT; neighbours undriven |
| Ubar=1.5 on **all three** full racks | Over-demands ~4.8 m³/s vs tile ~1.68 m³/s → reverse recirculation, Tin runaway |
| Force on **thin exit slices** (x≈1.55–1.60) mid Ubar=1.5, neighbours **milder** (~0.4) | Closer to “exit fan” + mass-safe |

True fan curves **self-balance** against Δp; hard Ubar does not. Never force the same high Ubar on all rack faces without checking tile mass.

---

## 5. Mesh / baffles / workflow

- Mid sims: impermeable **floor baffles** at z=0.44 / 0.88 / 1.32 (`topoSet` + `createBaffles`). Neighbours = continuous columns (no inter-U floors unless paper says so).
- Refine **normal to baffles**: both-ends grading in each 0.44 m band so faces stay on baffle planes.
- `./buildMesh` must re-`topoSet` / `createBaffles` after dict changes; `./Run` re-decomposes (stale `processor*` after remesh crashes `reconstructPar`).
- After mesh edits: stop solver → rebuild → clean fields → Run. **stop + reconstructPar -latestTime** when user asks to inspect.
- Dummy STLs (`scripts/write_dummy_stl.py` → `geometry/*.stl`) for ParaView — racks are porous cellZones, not walls. Use `foam.foam` + Outline STLs.

---

## 6. Turbulence / solver (intentional deltas)

- Paper RANS baseline: **standard k−ε** (+ DES). This case: **RNG k−ε** (aligned with HVAC Nielsen practice) — call it out in README.
- Solver: `buoyantBoussinesqSimpleFoam`.
- Validation SVGs: `Reports/scripts/make_validation_svgs.py` (Fig.4/5/8 + history). Prefer clean CFD vs exp plots; % error labels are optional and were removed by request.

---

## 7. Decision checklist before changing the case

1. Does the change match paper **fluid** neighbour + **open overhead**, or are we blanking volume again?
2. Heat: 4×2500 mid + 2×10000 neighbours, Su=Q/(ρCp)?
3. Fans: exit-local? Mid strong / neighbours mild? Mass balance vs tile?
4. Porous: streamwise Table 2 + transverse amplification; no double-counting 85%?
5. Remesh + baffles + fan cellZones still exist? STL refresh?
6. Document remaining gaps (domain H, sim size, RNG vs std k−ε, no Nelson curve).

---

## 8. Quick paths

```text
Case:   Validation-study/OpenFOAM/Data-Center-Cooling/Airflow-CFD/Saiyad2022_rackLevel/
Mesh:   system/blockMeshDict, topoSetDict, createBafflesDict
Physics: constant/fvOptions, turbulenceProperties
Viz:    foam.foam, geometry/*.stl, scripts/write_dummy_stl.py
Plots:  Reports/scripts/make_validation_svgs.py
```
