# MICrONS Tutorial Notebook — Setup Handoff

## Issues Fixed

### 1. Dataset version aligned to 1718
The group standardised on materialisation `1718`. CAVE tables were re-downloaded into `data/1718/raw/` and the old `data/1507/` was removed. Notebooks set:
```python
cleaner = mic.MicronsDataCleaner(datadir="../data/", version=1718)
```
Note: in 1718 the cell-type table is `aibs_metamodel_celltypes_v661_corrections` (was `aibs_metamodel_celltypes_v661` in 1507/1621). The library handles this automatically based on the `version` argument.

### 2. Wrong `datadir` path (both notebooks)
Notebooks are in `Leo/` but data lives one level up at the project root. All `datadir="data/"` arguments must be `datadir="../data/"`. This applies to both `MicronsDataCleaner` and `MicronsFunctionalReader`.

### 3. `functional_data` mode missing session columns
Using `functional_data='best_only'` intentionally drops `session`, `scan_idx`, and `unit_id` columns (library design). Later cells require those columns, so the correct mode is:
```python
units, segments = cleaner.process_nucleus_data(functional_data='all')
```

### 4. Truncated / misnamed h5 file
The functional h5 file was downloaded to `Leo/microns.h5` with a partially-downloaded copy also at `data/functional/microns_functional.h5.h5` (doubled extension, ~2.3 GB, corrupt). The complete file (~20 GB) was moved and renamed to the location the library expects:
```
data/functional/microns_functional.h5
```

### 5. Hardcoded researcher paths for `MicronsFunctionalReader`
Several cells contained a hardcoded absolute path from the original author's machine:
```python
# Wrong — author's local path
funcreader = mic.MicronsFunctionalReader(datadir="../../../../Research/Milan/MICrONS-datacleaner/data/")
# Correct
funcreader = mic.MicronsFunctionalReader(datadir="../data/")
```
Affected cells: two instances in `tutorial_microns.ipynb`, one in `basic-tutorial.ipynb`.

### 6. API change: `get_video_data` now returns a tuple
The library's `get_video_data` now returns `(clip, stim_type)` rather than a dict. Any cell using `video['clip']` must instead call `get_full_data_by_hash`, which does return a dict:
```python
# Wrong
video = funcreader.get_video_data(hash)
# Correct
video = funcreader.get_full_data_by_hash(hash)
```
Affected: `tutorial_microns.ipynb` cells 27, 47, and inside the `find_optimal_gabor` and `evaluate_error` function definitions.

### 7. Removed `video['spatial_freq']` reference
`get_full_data_by_hash` does not return a `spatial_freq` key. The affected cell drew a reference circle on an FFT plot — removed that line as it was illustrative only.

### 8. Missing `units_func` definition (`basic-tutorial.ipynb`)
The variable `units_func` was used but never defined. Added the missing cell:
```python
units_func = units[units['session'].notna()].copy()
```

### 9. `unit_id` column renamed
With `functional_data='all'`, the library renames `unit_id` to `functional_unit_id`. Any code referencing `row['unit_id']` in the context of `units_func` must use `functional_unit_id` instead.

### 10. h5 `unit_ids` lookup required for response indexing
`functional_unit_id` is not a direct row index into the `responses` array. Each session has a `META/unit_ids` dataset mapping row index → unit ID. A lookup dict must be built before indexing responses:
```python
uid_to_idx = {}
for session_key in funcreader.f['sessions'].keys():
    unit_ids = funcreader.f[f'sessions/{session_key}/meta/unit_ids'][:]
    uid_to_idx[session_key] = {uid: i for i, uid in enumerate(unit_ids)}
```

### 11. Not all sessions in h5
`units_func` contains neurons from sessions not present in the h5 file (e.g. `8_4`). Session lookups must be guarded:
```python
if session_key not in uid_to_idx:
    return np.full(len(monet_hashes), np.nan)
```
Sessions available in the h5: `4_7, 5_6, 5_7, 6_2, 6_4, 6_6, 6_7, 7_3, 7_4, 7_5, 8_5, 9_3, 9_4, 9_6`.
