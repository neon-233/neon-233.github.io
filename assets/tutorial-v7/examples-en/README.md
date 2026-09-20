# Jisuan V7: VASP Learning Files

These files accompany the computational chemistry tutorials. VASP was not run as part of the website development.
For the formal tutorial, please start from tutorial-v7-en.html and read the corresponding chapters of each file.

## Must confirm before use

1. Use VASP programs and PAW data legally licensed by the unit; the compressed package does not contain programs, POTCAR or real calculation results.
2. Prepare the corresponding POTCAR in the order of POSCAR elements, recording the data set version, TITEL, ENMAX and local SHA-256.
3. Silicon entry input is only set for the specified primitive cell and PBE. All cutoff energy, k-grids and thresholds need to be checked.
4. .template indicates the template that needs to be modified; when there are capital placeholders, angle bracket instructions or the structure file is missing, it cannot be run as is.
5. Create a directory independently for each task, retaining previous input and output; copy CHGCAR, CONTCAR or WAVECAR according to the chapter.
6. Electronic convergence, ion stopping, numerical accuracy and physical credibility need to be checked separately. Do not equate the completion of a template run with the conclusion of scientific research.
7. Advanced tasks also require correct choices of structures, boundary conditions, magnetic states, and methods. Native VASP and VTST parameters cannot be mixed.
8. The queue, module name, core number and program path in any job script are specified by the actual cluster. Please confirm with the administrator first.

Files use UTF-8 encoding and LF line endings. Follow the official documentation for VASP input formats; explanatory prose does not need to be copied into INCAR.

## File index
- si-scf/POSCAR - Teaching input; need to bring your own authorization Si POTCAR, and check ENMAX and convergence.
- si-scf/KPOINTS - Teaching input; need to bring your own authorized Si POTCAR and check ENMAX and convergence.
- si-scf/INCAR — Teaching input; need to bring your own authorization Si POTCAR, and check ENMAX and convergence.
- si-scf/README.txt - Teaching input; need to bring your own authorization Si POTCAR, and check ENMAX and convergence.
- si-relax/INCAR — with same silicon POSCAR/POTCAR and converged mesh; 520 eV Volume optimization accuracy must be verified.
- si-relax/README.txt — Optimization is not a completed calculation; please verify final forces and stresses.
- si-static/INCAR — Copies POSCAR from si-relax/CONTCAR where convergence has been verified, the potential file remains consistent.
- si-static/KPOINTS — Copies POSCAR from si-relax/CONTCAR where convergence has been verified, the potential files remain consistent.
- si-static/README.txt — The downloaded package does not contain an optimized structure. You need to complete your own optimization first.
- prepare_convergence.py - only generates the directory and input, does not submit or run VASP; will refuse to overwrite the target directory.
- submit.slurm.template — Queue and module placeholders must be replaced and the launcher adjusted as per Compute Center instructions.
- calculation-record.md.template — Fill in after each actual calculation, do not use imaginary results.
- si-dos/INCAR — requires converged POSCAR, POTCAR and CHGCAR of the same silicon primitive cell; the value is the starting point for teaching to be tested.
- si-dos/KPOINTS — requires converged POSCAR, POTCAR and CHGCAR of the same silicon primitive cell; the values are the starting point for teaching to be tested.
- si-bands/INCAR — requires converged POSCAR, POTCAR and CHGCAR of the same silicon primitive cell; the value is the starting point of the teaching to be tested.
- si-bands/KPOINTS — requires converged POSCAR, POTCAR and CHGCAR of the same silicon primitive cell; the value is the starting point for teaching to be tested.
- si-dos/README.txt - Avoid mistaking ICHARG=1 for a fixed charge density.
- si-bands/README.txt — The path only corresponds to the primitive cell of this tutorial and cannot be directly transplanted to other unit cells.
- fe-fm/POSCAR — Prepare your own authorized Fe PAW-PBE potential and redo the Fe convergence test. 2.87 Å is the fixed teaching geometry.
- fe-fm/KPOINTS — Prepare your own authorized Fe PAW-PBE potential and redo the Fe convergence test. 2.87 Å is the fixed teaching geometry.
- fe-fm/INCAR — Prepare your own authorized Fe PAW-PBE potential and redo the Fe convergence test. 2.87 Å is the fixed teaching geometry.
- fe-afm/INCAR — copies the same structure, mesh and potential of fe-fm; initializes from scratch, does not read existing magnetization density.
- fe-afm/README.txt — The comparison results require actual solution, and the reverse initial state may not be maintained until the end.
- dft-u/INCAR.template — Explicitly not ready: requires Ni2O2 magnetic structure, compatibility mesh, Ni O potential file, and well-documented Ueff and cutoff energy.
- dft-u/README.txt — Avoid assumptions about magnetic unit cells or "universal U".
- si-soc/INCAR — Must use vasp_ncl; comes with replication of non-magnetic silicon static structures, potentials, CHGCAR and uniform meshes.
- si-soc/README.txt — The three-component magnetic moment and the program type must be correct at the same time.
- si-charge/INCAR - Comes with the same verified structure, potential and convergence mesh; fine FFT mesh also needs to be verified after LAECHG export.
- si-charge/README.txt — Do not treat Bader partition charges directly as integer oxidation states.
- surface/INCAR.template - Requires slab structure, permission POTCAR, converged k-grid, ENCUT and DIPOL; example does not contain magnetic or charge states.
- defect/INCAR.template - Real supercell, k-point, pseudopotential, electron number and spin scheme need to be supplemented; no automatic formation energy or universal charge correction is included.
- phonon-internal/INCAR.template — input unit cell Γ point mode for optimized structures only; requires force accuracy and displacement convergence, not full phonon dispersion.
- phonopy/INCAR-force.template — used for each external displacement supercell, disabling ion optimization; need to unify parameters, complete structure and pseudopotential.
- phonopy/workflow.txt.template — Written according to the official Phonopy 4.5 command system; the actual displacement amount and path need to be replaced, and no real calculations are provided or performed.
- elastic/INCAR.template — only applicable to fully optimized three-dimensional bulk phases; convergence stress accuracy is required and cannot be directly used for two-dimensional modulus containing vacuum.
- neb-native/INCAR.template — Fixed unit cell, five intermediate structures; seven sets of endpoint/intermediate POSCAR required. The native optimizer uses finite POTIM.
- neb-vtst/optimizer-overlay.INCAR.template — Non-complete INCAR; only replaces the corresponding lines of the verified VTST program. Normal VASP prohibits the use of POTIM=0 fragments.
- aimd-nvt/INCAR.template - Short trial calculation of two atom types; the element friction array, time step and production sampling length need to be modified, and no real trajectory is provided.
- vdw/pbe-d3bj-overlay.INCAR.template - Supplemental fragment only, needs to be merged into the complete and verified PBE input; cannot be blindly stacked with other dispersion schemes.
- hse06/INCAR.template — Static calculation of nonmagnetic semiconductors from scratch; requires regular k-grid and converged ENCUT, fixed PBE charge density shortcut cannot be used.
- optics/INCAR.template — Self-consistent frequency response of a 3D non-magnetic insulator; NBANDS, ENCUT and k-grid all need to be converged, exciton-free.
- dielectric/INCAR.template — Electron-clamped ion dielectric response with Born charge; does not contain full ion contributions and is not suitable for LEPSILON calculations of HSE.
- advanced-README.md — Read this first; clarify applicable limitations for native NEB/VTST, Phonopy versions, and all templates.
- report/calculation-report.md - Blank research record, including model, method, convergence, operating environment and evidence boundary; can be filled in according to specific tasks.
- report/practice-checklist.md — Fillable reporting framework; all results are left blank and do not include simulated data or automated scoring.
- tools/inspect_vasp_run.py - Read-only extraction of last energy and force, stop message and file hash; does not automatically verify convergence. The Python standard library can be run.
