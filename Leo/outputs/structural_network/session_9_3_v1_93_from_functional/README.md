# Session 9_3 V1 Structural Output

This structural network is aligned exactly to `outputs/functional_network/F_correlation_matrix.npy` and `outputs/functional_network/functional_cohort.csv`.

Important: the functional notebook initially reports 99 neurons in session 9 scan 3, but the saved functional matrix contains 93 neurons after dropping 6 neurons not found in the V1 response matrix. Use this 93-neuron output for comparisons with the pushed `F_correlation_matrix.npy`.

The original project notes used 200 neurons as a conservative fallback threshold. The team has decided this 93-neuron cohort is acceptable, so this folder records that decision and does not enforce the 200-neuron cutoff. No neurons are duplicated: there are 93 unique `pt_root_id` values and 93 unique functional unit IDs within session `9_3`.

Matrix convention: `W[post, pre] = synapse count from pre to post`.
