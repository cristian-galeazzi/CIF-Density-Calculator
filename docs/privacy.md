# Privacy: nothing private gets published

No experimental or personal data is included in this repository, and none must
ever be committed or published. Three layers enforce this:

1. **Ignored paths** - `cif_files/`, `*.cif`, `density_results.csv` and `*.csv`
   are excluded via [`.gitignore`](../.gitignore); the validation suite and the
   notebook self-check use only synthetic structures.
2. **Stripped notebook outputs** - executed cells embed their results (tables,
   file names) inside the `.ipynb` file. Strip them before every commit:

   ```bash
   jupyter nbconvert --clear-output --inplace CIF_Density_Calculator.ipynb
   ```

3. **Automatic strip on commit (recommended)** - install
   [nbstripout](https://github.com/kynan/nbstripout) once per clone so git
   strips outputs transparently at commit time, and a forgotten manual strip can
   never leak data:

   ```bash
   pip install nbstripout
   nbstripout --install        # run inside the git repository
   ```
