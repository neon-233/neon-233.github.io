#!/usr/bin/env python3
"""Read a VASP OUTCAR without modifying it. This is not a convergence certifier.

Usage: python inspect_vasp_run.py path/to/OUTCAR
Only the Python standard library is required. Output is JSON for a human to review.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"

def value(text):
    number = float(text.replace('D', 'E').replace('d', 'e'))
    if not math.isfinite(number):
        raise ValueError('Non-finite number in OUTCAR')
    return number

def last_match(pattern, text):
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    return matches[-1] if matches else None

def inspect(text):
    total = last_match(r'free\s+energy\s+TOTEN\s*=\s*(' + NUMBER + ')', text)
    energy = last_match(r'energy\s+without\s+entropy\s*=\s*(' + NUMBER + r')\s+energy\s*\(sigma->0\)\s*=\s*(' + NUMBER + ')', text)
    ions = last_match(r'\bNIONS\s*=\s*(\d+)', text)
    cutoff = last_match(r'\bENCUT\s*=\s*(' + NUMBER + ')', text)
    kpoints = last_match(r'\bNKPTS\s*=\s*(\d+)', text)
    force_headers = list(re.finditer(r'POSITION\s+TOTAL-FORCE\s*\(eV/Angst\)', text))
    force_vectors = []
    if force_headers:
        for line in text[force_headers[-1].end():].splitlines():
            fields = line.split()
            if len(fields) >= 6:
                try:
                    nums = [value(x) for x in fields[:6]]
                except ValueError:
                    if force_vectors:
                        break
                    continue
                force_vectors.append(nums[3:6])
            elif force_vectors:
                break
    norms = [math.sqrt(sum(c*c for c in v)) for v in force_vectors]
    stops = list(re.finditer(r'aborting loop because EDIFF is reached', text, flags=re.I))
    ionic_stop = bool(re.search(r'reached required accuracy\s*-\s*stopping structural energy minimisation', text, flags=re.I))
    footer = 'General timing and accounting informations for this job' in text
    warnings = []
    if not footer:
        warnings.append('Timing footer absent: job may still be running, interrupted, or written by a different version. Inspect the scheduler and stdout.')
    if not total:
        warnings.append('No TOTEN record found. This is not a usable final-energy summary.')
    if force_vectors and ions and len(force_vectors) != int(ions.group(1)):
        warnings.append('Last force-block row count does not match NIONS; output may be truncated.')
    if not stops:
        warnings.append('No explicit EDIFF-stop message found. Check every relevant electronic cycle in OUTCAR/OSZICAR; message formats vary.')
    warnings.append('An EDIFF message somewhere in the file does not prove that the final or every electronic cycle converged.')
    warnings.append('Maximum force below is over ALL parsed atoms, including fixed atoms; apply selective-dynamics constraints when judging relaxation.')
    warnings.append('Footer/stop messages do not establish ENCUT, k-mesh, supercell, smearing, magnetic-state or physical-model convergence.')
    warnings.append('TOTEN is the reported free-energy quantity. Do not mix it with sigma->0 energies across an energy-difference calculation.')
    return {
        'nions': int(ions.group(1)) if ions else None,
        'encut_eV': value(cutoff.group(1)) if cutoff else None,
        'irreducible_kpoints_reported': int(kpoints.group(1)) if kpoints else None,
        'last_free_energy_TOTEN_eV': value(total.group(1)) if total else None,
        'last_energy_without_entropy_eV': value(energy.group(1)) if energy else None,
        'last_energy_sigma_to_zero_eV': value(energy.group(2)) if energy else None,
        'last_force_block_atom_count': len(force_vectors),
        'max_force_norm_all_atoms_eV_per_A': max(norms) if norms else None,
        'timing_footer_found': footer,
        'explicit_EDIFF_stop_message_count': len(stops),
        'ionic_accuracy_stop_message_found': ionic_stop,
        'automatically_certified_converged': False,
        'review_notes': warnings,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('outcar', type=Path)
    args = parser.parse_args()
    try:
        raw = args.outcar.read_bytes()
    except OSError as exc:
        parser.exit(2, 'Cannot read OUTCAR: ' + str(exc) + '\n')
    report = inspect(raw.decode('utf-8', errors='replace'))
    report['file'] = str(args.outcar)
    report['sha256'] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
