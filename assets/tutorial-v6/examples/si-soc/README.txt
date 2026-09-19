Use vasp_ncl, not vasp_std or vasp_gam. Copy matching POSCAR/POTCAR/CHGCAR from nonmagnetic Si PBE SCF and use a converged uniform KPOINTS mesh. This input performs a new self-consistent SOC calculation with ICHARG=1. MAGMOM contains 3 components per atom (6 numbers for 2 Si); do not add ISPIN=2. Check actual NBANDS and SOC convergence.

If reusing submit.slurm.template, replace vasp_std with vasp_ncl in BOTH command -v and srun lines. Save the configured script in si-soc, cd into si-soc, then submit there. Changing only INCAR does not change the executable.
