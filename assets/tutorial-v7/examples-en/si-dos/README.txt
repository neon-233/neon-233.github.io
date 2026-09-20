Copy POSCAR, POTCAR and converged CHGCAR from si-static (same geometry and PBE model). ICHARG=1 updates the density self-consistently on the denser mesh. Verify ENCUT, k mesh, NBANDS and DOS resolution. POTCAR and calculated outputs are not included.

For the py4vasp snippet, start the Jupyter notebook in the parent directory of si-dos. If the notebook is already inside si-dos, use Calculation.from_path(".") instead of Calculation.from_path("si-dos").
