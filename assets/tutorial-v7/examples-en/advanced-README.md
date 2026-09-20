# V7 advanced-task templates / advanced task templates

These files are a starting point for instruction and are not the results of calculations of materials that have been run and verified.
All INCAR.template must be copied to its own new task directory, complete the value marked REPLACE, and then renamed to INCAR after checking.
You must provide real POSCAR, converged KPOINTS, and licensed POTCAR yourself; POTCAR is not distributed in this package.
Examples are usually for non-magnetic semiconductors/insulators; actual metal, magnetic, U, SOC, and charged systems cannot be directly applied without review.
The reference states, electron numbers and pinned layers of the surface/defect template are determined by the research question.

## Key differences between native NEB and VTST
neb-native/INCAR.template uses the native optimizer and finite POTIM, and the five intermediate structures correspond to seven POSCARs from 00 to 06.
neb-vtst/optimizer-overlay.INCAR.template is only valid for VASPs that are compiled with VTST compatibility: IBRION=3, POTIM=0, IOPT=7.
Setting POTIM=0 in a normal VASP will cause the ions to be immobile. You cannot just write LCLIMB / IOPT to enable VTST.
The VTST fragment needs to replace the original INCAR corresponding line, and conflicting settings cannot coexist. First set LCLIMB=.FALSE. to pre-converge, then check the path and then continue the calculation separately and turn it on.

## Phonopy and VASP's Built-in Finite Displacements
phonon-internal is the path of VASP's self-displacement and the input unit cell Gamma vibration.
phonopy's INCAR-force is used for the static force of the external displacement structure and prohibits further optimization of the displacement structure.
workflow.txt.template provides phonopy-init / phonopy commands according to Phonopy 4.5 style, which needs to match the installed version.
The example only lists two vasprun.xml paths, which must be replaced with actual full displacements, strictly maintaining the order of phonopy_disp.yaml.

## Other restrictions
The AIMD template LANGEVIN_GAMMA has two values and is only applicable to the two POTCAR types; POTIM unit is fs.
HSE requires a regular k grid with self-consistent orbitals and cannot fix the PBE density with ICHARG=11.
LOPTICS is an independent particle response and is not equal to the exciton spectrum; the LEPSILON template is not suitable for HSE.
Flex template only for 3D bulk; GPa with vacuum model depends on box height.
All demonstration thresholds and grids must converge to the target properties and are not replicated to achieve paper accuracy.

Verification date: 2026-09-19. For a complete discussion and official link, see vasp-advanced-v7-en.html.
