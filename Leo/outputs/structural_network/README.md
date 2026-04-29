# Structural Network Outputs

Use the cohort-specific subfolders:

- `session_matched-all/`: strict single-session structure-function cohort. This is the current candidate for Project 7 comparisons because all neurons come from h5 session `8_5`.
- `all-matched_axon-clean/`: larger proofread structural-only graph matching the 906-neuron exploratory result. Do not use it for one functional correlation matrix because it spans multiple imaging sessions and contains no inhibitory neurons.

Matrix convention for all `.npz` files:

`W[post, pre] = synapse count from presynaptic neuron pre to postsynaptic neuron post`.

Do not collapse `W_exc` and `W_inh` for E/I analyses. `W_inh` is empty in the axon-clean all-matched cohort because no inhibitory neurons have axon-clean proofreading in this metadata snapshot.
