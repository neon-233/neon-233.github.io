SI LEARNING EXAMPLE — NOT A COMPUTED RESULT

This folder contains a two-atom diamond-Si primitive POSCAR, a PBE INCAR,
and a Gamma-centered 8x8x8 KPOINTS mesh. It does not contain POTCAR or VASP.

Use only an appropriately licensed VASP installation. Obtain the Si PAW_PBE
potential from your institution's licensed distribution. Copy its unmodified
POTCAR to this folder. Record its release, TITEL, ZVAL, ENMAX and hash.
POSCAR species order must match POTCAR order. Do not publicly redistribute POTCAR.

ENCUT=520 eV and 8x8x8 are learning starting values, not convergence claims.
ENCUT must be >= max ENMAX of the actual POTCAR. Test ENCUT and k-point
convergence independently before drawing conclusions. For cell relaxation,
start with an increased cutoff (often at least 1.3*max ENMAX) and verify stress.
Update ENCUT consistently in all dependent examples if a higher value is needed.

The 5.43 Angstrom lattice parameter is an initial geometry, not a relaxed result.
Use vasp_std on a compute allocation; do not use vasp_gam for this mesh.
The website has not executed VASP or validated any numerical energies/band gaps.
