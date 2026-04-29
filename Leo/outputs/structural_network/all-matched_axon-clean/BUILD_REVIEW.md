# Structural Network Build Review

Root `structural_network.ipynb` was useful as exploration, but it should not be treated as final methods because:
- it reports a 906-neuron all-session matched structural graph, which is not automatically a valid functional-correlation cohort;
- it collapses E/I edges for several analyses;
- it uses synaptic size where the project definition asks for synapse count;
- it compares small-world metrics to an ER-like baseline rather than a degree-preserving configuration model.

This build instead writes directed matrices with rows as postsynaptic neurons and columns as presynaptic neurons:
- `W_all_synapse_count_post_by_pre.npz`
- `W_exc_synapse_count_post_by_pre.npz`
- `W_inh_synapse_count_post_by_pre.npz`

Selected functional session: `ALL_MATCHED_MULTISSESSION_STRUCTURAL_ONLY`
Cohort size: `906` neurons
Proofread policy: `axon-clean`
Axon-clean neurons in cohort: `906`
Unproofread-axon neurons in cohort: `0`
Go threshold met: `False`
Directed structural edges after autapse removal: `11822`

Do not claim structure-function results from the all-matched multisession graph.
Do not claim structure-function results if `go_for_structure_function` is false.
