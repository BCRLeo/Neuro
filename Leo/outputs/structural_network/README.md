# Structural Network Outputs

Use the cohort-specific subfolders:

- `session_9_3_v1_93_from_functional/`: current team-pivot cohort aligned exactly to the pushed `outputs/functional_network/F_correlation_matrix.npy` matrix. Use this if the group is now analyzing session 9, scan 3.
- `session_matched-all/`: strict single-session structure-function cohort. This is the current candidate for Project 7 comparisons because all neurons come from h5 session `8_5`.
- `all-matched_axon-clean/`: larger proofread structural-only graph matching the 906-neuron exploratory result. Do not use it for one functional correlation matrix because it spans multiple imaging sessions and contains no inhibitory neurons.

Matrix convention for all `.npz` files:

`W[post, pre] = synapse count from presynaptic neuron pre to postsynaptic neuron post`.

Do not collapse `W_exc` and `W_inh` for E/I analyses. `W_inh` is empty in the axon-clean all-matched cohort because no inhibitory neurons have axon-clean proofreading in this metadata snapshot.

Note: the team notebook initially reports 99 neurons in session 9 scan 3, but the saved functional matrix contains 93 neurons after dropping 6 neurons missing from the V1 response matrix. The `session_9_3_v1_93_from_functional/` folder follows the saved 93-neuron matrix, because that is the matrix actually available for comparisons.

The original project notes used 200 neurons as a conservative fallback threshold. The team has now decided the 93-neuron session `9_3` cohort is acceptable, so the aligned 9_3 output does not enforce that threshold. It also verifies that no neurons were duplicated to increase `N`.
