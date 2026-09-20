#!/usr/bin/env python3
"""Prepare independent input directories only. Does not submit jobs or run VASP."""
import argparse
import csv
import math
from pathlib import Path
import re
import shutil

p = argparse.ArgumentParser()
p.add_argument("mode", choices=["encut", "kmesh"])
p.add_argument("source", type=Path)
p.add_argument("destination", type=Path)
p.add_argument("values", nargs="+", type=float)
a = p.parse_args()
source = a.source.resolve()
destination = a.destination.resolve()
for name in ["INCAR", "POSCAR", "KPOINTS", "POTCAR"]:
    if not (source / name).is_file():
        raise SystemExit(f"Missing source input: {name}")
if destination.exists():
    raise SystemExit("Destination exists; choose a NEW directory to avoid overwriting")
incar = (source / "INCAR").read_text(encoding="utf-8")
potcar = (source / "POTCAR").read_text(encoding="utf-8", errors="replace")
limits = re.findall(r"ENMAX\s*=\s*([0-9.]+)", potcar)
if not limits:
    raise SystemExit("ENMAX not found; inspect POTCAR before proceeding")
max_enmax = max(map(float, limits))
# Restrict this educational generator to an unambiguous static source INCAR.
settings = {}
for number, raw in enumerate(incar.splitlines(), start=1):
    clean = re.split(r"[!#]", raw, maxsplit=1)[0].strip()
    if not clean:
        continue
    if ";" in clean or clean.count("=") != 1:
        raise SystemExit(f"Use one unambiguous tag per line (INCAR line {number})")
    key, value = (part.strip() for part in clean.split("=", 1))
    key = key.upper()
    if key in settings:
        raise SystemExit(f"Duplicate INCAR tag: {key}")
    settings[key] = value
try:
    nsw = int(settings.get("NSW", "0"))
    ibrion = int(settings.get("IBRION", "-1"))
except ValueError:
    raise SystemExit("NSW and IBRION must be plain integers")
if nsw > 0 or ibrion != -1:
    raise SystemExit("Source must be STATIC: NSW <= 0 and IBRION = -1; do not use a relaxation INCAR")
if a.mode == "kmesh":
    try:
        cutoff = float(settings["ENCUT"].replace("D", "E").replace("d", "e"))
    except (KeyError, ValueError):
        raise SystemExit("kmesh source must set an explicit numeric ENCUT")
    if not math.isfinite(cutoff) or cutoff < max_enmax:
        raise SystemExit(f"Source ENCUT must be >= max ENMAX ({max_enmax} eV)")
values = a.values
if any(not math.isfinite(x) or x <= 0 for x in values):
    raise SystemExit("Values must be positive finite numbers")
if len(set(values)) != len(values):
    raise SystemExit("Duplicate values")
if a.mode == "encut" and min(values) < max_enmax:
    raise SystemExit(f"All ENCUT values must be >= max ENMAX ({max_enmax} eV)")
if a.mode == "kmesh" and any(x != int(x) for x in values):
    raise SystemExit("k mesh values must be positive integers")
# This generator expects the distributed one-tag-per-line INCAR, not an arbitrary INCAR.
base = []
for line in incar.splitlines():
    key = line.split("=", 1)[0].strip().upper()
    if key not in {"ISTART", "ICHARG", "LWAVE", "LCHARG"} and not (a.mode == "encut" and key == "ENCUT"):
        base.append(line)
base += ["ISTART = 0", "ICHARG = 2", "LWAVE = .FALSE.", "LCHARG = .FALSE."]
destination.mkdir(parents=True)
rows = []
for value in values:
    label = f"{value:g}"
    run = destination / (("e" if a.mode == "encut" else "k") + label)
    run.mkdir()
    for name in ["POSCAR", "POTCAR"]:
        shutil.copy2(source / name, run / name)
    text = "\n".join(base) + "\n"
    if a.mode == "encut":
        text += f"ENCUT = {value:g}\n"
        shutil.copy2(source / "KPOINTS", run / "KPOINTS")
    else:
        n = int(value)
        (run / "KPOINTS").write_text(f"Gamma mesh convergence\n0\nGamma\n{n} {n} {n}\n0 0 0\n", encoding="utf-8")
    (run / "INCAR").write_text(text, encoding="utf-8")
    rows.append([run.name, a.mode, label, "prepared_not_run"])
with (destination / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["directory", "variable", "value", "status"])
    writer.writerows(rows)
print(f"Prepared {len(rows)} independent folders; submit manually after review")
