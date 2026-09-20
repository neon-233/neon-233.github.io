#Computational Chemistry Comprehensive Exercise Record

Status: Not yet running / Partially completed / Completed and verified (choose by yourself)
Topic:
Author and date:
Running environment, VASP version and executable program:
Chapters:
Models, methods and preset acceptance criteria:
Actual running directory and input file identification:
Authorization potential file version and element sequence (only metadata is recorded, POTCAR is not disclosed):

## Common requirements
- [ ] Distinguish between task design, actual calculations, and inferences about results.
- [ ] Keep input, output, job records and failure reasons.
- [ ] Check the actual read settings, not just trust the filename.
- [ ] Each graph indicates the unit, reference energy, sampling method and data source.
- [ ] Leave unconverged or incomplete flags, do not make up values.

## 1. Silicon numerical convergence
Fixed geometry and physics settings:
Variables and control quantities of this round:
Energy definition, atomic numbers and normalization:
Pre-selected acceptance criteria and reasons:

| Table of Contents | ENCUT | k-grid | Electronic Convergence Evidence | Energy/Atoms | Maximum Force/Stress | Time Elapsed |
| --- | --- | --- | --- | --- | --- | --- |
| To be filled | To be filled | To be filled | To be verified | To be calculated | To be calculated | To be recorded |

- [ ] Fixed geometry for ENCUT and k-grid independent testing.
- [ ] Cross-check on the last selected settings.
- [ ] Discuss electrons, basis sets, grid errors and method limitations respectively.

## 2. SCF → DOS / PBE band structure
File flow diagram:
SCF CHGCAR generates directory:
DOS self-consistent way with uniform grid:
band structure reads files, paths, and reciprocal vectors:
Drawing reference energy:
Edge and integral check (to be filled in for actual calculation):
Source of difference and next verification:

## 3. Choose one: magnetic state / neutral defect
Selected route:
Problem and model scope:
Control design:
Magnetic state route: first guess → final local/total magnetic moment → energy and convergence evidence.
Defect route: atomic number and formation energy formula → chemical potential → supercell size check.
The scope of application of the conclusion and the interpretations that are not excluded:

## 4. Surface adsorption and NEB scheme
Crystal plane, vacuum direction, coverage and fixed layer:
Reference state, composition, spin and method consistency:
Adsorption energy definition and symbol:
Endpoint structure, atomic order and force checks:
Directory tree and intermediate image inspection:
Native VASP / VTST and versions:
Barrier convergence and transition state verification plan:
Current status (design/partially calculated/verified):

## 5. AIMD Sampling Plan
Target Observations:
Ensemble, temperature, unit cell and initial velocity sources:
Time step × number of steps = simulation duration:
Thermalization, production and output zones:
Short NVE drift versus accuracy comparison plan:
Chunked/repeated simulation and correlation processing:
If you analyze diffusion: period crossover, drift, fitting interval, transition statistics.
Conditions that extend the simulation or negate the conclusion:

## Final conclusion
It has been actually observed:
Still not verified:
Main uncertainties:
Reproducible file and data locations:
