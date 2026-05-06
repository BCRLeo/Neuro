# Structural Network Handoff

This folder contains the structural-network build for Leo's part of Project 7,
"From Structure to Function", using MICrONS `minnie65_public` materialization
`1718`.

The key output is a directed weighted structural connectome where:

```text
W[post, pre] = synapse count from presynaptic neuron pre to postsynaptic neuron post
```

Rows are postsynaptic neurons. Columns are presynaptic neurons.

## Weighting Choice

The structural matrices use synapse count, not synapse size.

Example:

- If neuron A makes 3 synapses onto neuron B, the edge weight is `3`.
- The total cleft/contact size is still kept in `structural_edges.csv` as
  `synapse_size_sum`, but it is not the primary structural weight.

Reason:

- The project definition states `W_ij = synapse count from neuron j to neuron i`.
- Synapse size is biologically interesting, but it changes the interpretation
  from "how many synaptic contacts connect this pair" to "how much total contact
  area connects this pair".
- If the group wants a sensitivity analysis, rerun the same comparisons with
  `synapse_size_sum`, but keep the main analysis count-weighted.

## Which Output Should Be Used?

There are now three cohort-specific subfolders. The first one reflects the
team's later pivot to session 9, scan 3.

### `session_9_3_v1_93_from_functional/`

Use this if the group is now analyzing the pushed functional output in
`outputs/functional_network/`.

This folder is aligned exactly to:

- `outputs/functional_network/F_correlation_matrix.npy`
- `outputs/functional_network/functional_cohort.csv`

Important clarification:

- The functional notebook initially reports `99` neurons in session 9, scan 3.
- The saved functional matrix is actually `93 x 93`.
- Six neurons were dropped because they were missing from the V1 response matrix.
- Therefore this structural folder follows the saved `93`-neuron matrix, not the
  intermediate `99`-neuron printout.

Summary:

- Cohort size: `93` neurons
- Session: `9_3`
- Brain area/layer/type: `V1`, `L4`, `4P`
- Excitatory neurons: `93`
- Inhibitory neurons: `0`
- Directed structural edges after autapse removal: `229`
- Total synapse count after autapse removal: `260`

Threshold and duplication note:

- The original project notes used `200` neurons as a conservative fallback
  threshold.
- The team has now decided the `93`-neuron session `9_3` cohort is acceptable.
- This output therefore does not enforce the `200`-neuron cutoff.
- No neurons are duplicated to increase `N`: the output has `93` unique
  `pt_root_id` values and `93` unique functional unit IDs within session `9_3`.

Important limitations:

- There are no inhibitory neurons, so E/I separation is trivial and `W_inh` is
  empty.
- The current functional matrix is Pearson-only, so it should be described as
  exploratory unless partial correlation or another controlled functional metric
  is added.

### `session_matched-all/`

This was the earlier main Project 7 structure-function candidate before the
team pivot.

This folder contains neurons from one functional imaging session, `8_5`.
That matters because functional correlations are only valid between neurons
recorded in the same session.

Summary:

- Cohort size: `1476` neurons
- Excitatory neurons: `1465`
- Inhibitory neurons: `11`
- Directed structural edges after autapse removal: `5728`
- Excitatory-presynaptic edges: `5684`
- Inhibitory-presynaptic edges: `44`
- Total synapse count after autapse removal: `6495`
- Go/no-go threshold met: yes, `1476 > 200`

Important limitation:

- Only `127` neurons have axon-clean proofreading.
- `1349` neurons have unproofread axons.
- This cohort is therefore best for structure-function matching, but the
  structural certainty is weaker than in the axon-clean-only graph.

### `all-matched_axon-clean/`

Use this as a clean structural-only reference graph.

This folder reproduces the 906-neuron structural result from the exploratory
root notebook, but it should not be used as the main structure-function cohort.

Summary:

- Cohort size: `906` neurons
- Directed structural edges after autapse removal: `11822`
- Total synapse count after autapse removal: `13281`
- Excitatory neurons: `906`
- Inhibitory neurons: `0`

Important limitations:

- The neurons span multiple functional imaging sessions, so one shared
  functional correlation matrix is not valid.
- There are no inhibitory presynaptic neurons, so `W_inh` is empty.
- This cannot satisfy the E/I separation requirement for the full Project 7
  structure-function analysis.

## What Each File Means

Each cohort subfolder contains the same file types.

### `summary.json`

Machine-readable summary of the build.

It records:

- dataset version
- cohort scope
- proofreading policy
- selected functional session
- number of neurons
- number of excitatory and inhibitory neurons
- number of structural edges
- number of autapses removed
- whether the go/no-go threshold was passed

Start here when checking which cohort was built.

### `cohort_neurons.csv`

One row per neuron in the final cohort.

Important columns:

- `matrix_index`: row/column index in the adjacency matrices
- `pt_root_id`: MICrONS root ID
- `classification_system`: excitatory or inhibitory label
- `cell_type`: more detailed cell type
- `layer`, `brain_area`: anatomical metadata
- `strategy_axon`, `strategy_dendrite`: proofreading status
- `pt_position_x`, `pt_position_y`, `pt_position_z`: soma position for distance control
- `session`, `scan_idx`, `functional_unit_id`: functional recording alignment

This file is the bridge between structure, function, cell type, and distance.

### `structural_edges.csv`

One row per directed neuron-to-neuron connection after grouping synapses.

Important columns:

- `pre_pt_root_id`: presynaptic neuron
- `post_pt_root_id`: postsynaptic neuron
- `synapse_count`: number of synapses from pre to post
- `synapse_size_sum`: total synaptic contact area, kept as extra metadata

For the project definition, use `synapse_count` as the structural edge weight.

### `cohort_synapses_raw.csv`

Raw CAVE synapse rows downloaded before collapsing into neuron-pair edges.

This file is mostly for auditability and reproducibility. It proves what was
downloaded and lets the edge table be rebuilt if needed. It should not usually
be analyzed directly.

### `session_counts.csv`

Counts of matched neurons per functional session before final cohort selection.

This explains why session `8_5` was chosen for the structure-function cohort:
it had the largest usable matched-neuron count.

### `W_all_synapse_count_post_by_pre.npz`

Sparse adjacency matrix for all directed structural edges.

```text
W_all[post, pre] = synapse count from pre to post
```

### `W_exc_synapse_count_post_by_pre.npz`

Same shape as `W_all`, but only includes edges where the presynaptic neuron is
excitatory.

### `W_inh_synapse_count_post_by_pre.npz`

Same shape as `W_all`, but only includes edges where the presynaptic neuron is
inhibitory.

Do not collapse `W_exc` and `W_inh` for E/I-specific analyses.

### `BUILD_REVIEW.md`

Human-readable review of the build and methodological warnings.

## Why These Steps Were Needed

The goal is to compare a structural network with a functional network. That
requires the same neurons to exist in both datasets.

The pipeline therefore does the following:

1. Builds a neuron table from MICrONS metadata.
2. Filters to neurons with functional recordings.
3. Selects a single functional session for the main structure-function cohort.
4. Builds directed synaptic edges from `synapses_pni_2`.
5. Removes autapses.
6. Aggregates individual synapses into neuron-pair edge weights using synapse count.
7. Splits structural edges by presynaptic E/I class.
8. Saves matrices and metadata using the same neuron ordering.

The single-session step is essential. Pairwise calcium correlations are only
meaningful between neurons recorded together. Combining neurons from different
sessions would create invalid functional edges.

The E/I split is also essential. Excitatory and inhibitory structural edges have
different biological meaning and should not be collapsed in the final analysis.

## Review Of Teammate Root Notebook

The root-level `structural_network.ipynb` was useful exploratory work, but it is
not final-methods safe for the Project 7 analysis.

Main issues:

- It uses the 906-neuron all-session axon-clean cohort, which is structural-only.
- It does not give a valid single-session functional-correlation cohort.
- It collapses E/I edges in parts of the analysis.
- It uses synaptic size as the structural weight, while the project definition
  specifies synapse count.
- Its small-world comparison is not a degree-preserving configuration-model null.

The `all-matched_axon-clean/` outputs reproduce the useful structural part of
that notebook, but the final structure-function analysis should use
`session_matched-all/`.

## Next Step

Use `session_matched-all/cohort_neurons.csv` to build the functional response
matrix for h5 session `8_5`.

The functional matrix must be aligned in the exact same order as
`matrix_index`.

Then compute:

- Pearson correlations for descriptive comparison only
- partial correlations or another controlled functional-connectivity metric for
  the main analysis
- distance-controlled tests using `pt_position_x/y/z`

Do not claim structure-function correspondence until distance has been
controlled and permutation tests have been run.
