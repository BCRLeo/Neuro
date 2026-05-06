"""Build structural matrices aligned to the team's session 9 scan 3 functional output.

This is intentionally separate from `build_structural_network.py` because the
team pivoted to the small session 9_3 V1 cohort already saved under
`outputs/functional_network/`.

The output order follows `outputs/functional_network/functional_cohort.csv`
exactly, so row/column `i` in these structural matrices matches row/column `i`
in `outputs/functional_network/F_correlation_matrix.npy`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

FUNC_COHORT = REPO_ROOT / "outputs" / "functional_network" / "functional_cohort.csv"
FUNC_MATRIX = REPO_ROOT / "outputs" / "functional_network" / "F_correlation_matrix.npy"
SOURCE_SYNAPSES = (
    SCRIPT_DIR
    / "outputs"
    / "structural_network"
    / "all-matched_axon-clean"
    / "cohort_synapses_raw.csv"
)
OUT_DIR = SCRIPT_DIR / "outputs" / "structural_network" / "session_9_3_v1_93_from_functional"


def adjacency(edge: pd.DataFrame, cohort: pd.DataFrame, pre_class: str | None = None) -> sp.csr_matrix:
    if pre_class is not None:
        class_by_id = cohort.set_index("pt_root_id")["classification_system"].to_dict()
        keep = {int(root_id) for root_id, cls in class_by_id.items() if cls == pre_class}
        edge = edge[edge["pre_pt_root_id"].isin(keep)]

    id_to_idx = dict(zip(cohort["pt_root_id"].astype("int64"), cohort["matrix_index"].astype(int)))
    rows = edge["post_pt_root_id"].map(id_to_idx).astype(int).to_numpy()
    cols = edge["pre_pt_root_id"].map(id_to_idx).astype(int).to_numpy()
    data = edge["synapse_count"].astype(float).to_numpy()
    n = len(cohort)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))


def main() -> None:
    if not FUNC_COHORT.exists():
        raise FileNotFoundError(FUNC_COHORT)
    if not FUNC_MATRIX.exists():
        raise FileNotFoundError(FUNC_MATRIX)
    if not SOURCE_SYNAPSES.exists():
        raise FileNotFoundError(SOURCE_SYNAPSES)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cohort = pd.read_csv(FUNC_COHORT)
    cohort["pt_root_id"] = cohort["pt_root_id"].astype("int64")
    cohort["unit_id"] = cohort["unit_id"].astype("int64")
    cohort = cohort.sort_values("matrix_index").reset_index(drop=True)
    cohort["matrix_index"] = np.arange(len(cohort), dtype=int)
    cohort = cohort.rename(columns={"unit_id": "functional_unit_id"})
    cohort["h5_key"] = (
        cohort["session"].astype(int).astype(str)
        + "_"
        + cohort["scan_idx"].astype(int).astype(str)
    )
    if cohort["pt_root_id"].duplicated().any():
        dupes = cohort.loc[cohort["pt_root_id"].duplicated(keep=False), "pt_root_id"]
        raise RuntimeError(f"Duplicated pt_root_id values in functional cohort: {dupes.tolist()}")
    if cohort[["h5_key", "functional_unit_id"]].duplicated().any():
        dupes = cohort.loc[
            cohort[["h5_key", "functional_unit_id"]].duplicated(keep=False),
            ["h5_key", "functional_unit_id", "pt_root_id"],
        ]
        raise RuntimeError(f"Duplicated functional unit rows in cohort:\n{dupes}")

    F = np.load(FUNC_MATRIX)
    if F.shape != (len(cohort), len(cohort)):
        raise ValueError(f"Functional matrix shape {F.shape} does not match cohort size {len(cohort)}")

    ids = set(cohort["pt_root_id"].astype("int64"))
    syn = pd.read_csv(SOURCE_SYNAPSES)
    syn["pre_pt_root_id"] = syn["pre_pt_root_id"].astype("int64")
    syn["post_pt_root_id"] = syn["post_pt_root_id"].astype("int64")
    syn = syn[syn["pre_pt_root_id"].isin(ids) & syn["post_pt_root_id"].isin(ids)].copy()

    autapses = syn["pre_pt_root_id"] == syn["post_pt_root_id"]
    n_autapses = int(autapses.sum())
    syn_no_auto = syn[~autapses].copy()

    edge = (
        syn_no_auto.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False)
        .agg(synapse_count=("size", "size"), synapse_size_sum=("size", "sum"))
        .sort_values(["pre_pt_root_id", "post_pt_root_id"])
        .reset_index(drop=True)
    )

    W_all = adjacency(edge, cohort)
    W_exc = adjacency(edge, cohort, "excitatory_neuron")
    W_inh = adjacency(edge, cohort, "inhibitory_neuron")
    if W_all.nnz != W_exc.nnz + W_inh.nnz:
        raise RuntimeError("E/I split does not sum to all edges")
    if int(W_all.diagonal().sum()) != 0:
        raise RuntimeError("Autapses remain in W_all")

    cohort.to_csv(OUT_DIR / "cohort_neurons.csv", index=False)
    syn.to_csv(OUT_DIR / "cohort_synapses_raw.csv", index=False)
    edge.to_csv(OUT_DIR / "structural_edges.csv", index=False)
    sp.save_npz(OUT_DIR / "W_all_synapse_count_post_by_pre.npz", W_all)
    sp.save_npz(OUT_DIR / "W_exc_synapse_count_post_by_pre.npz", W_exc)
    sp.save_npz(OUT_DIR / "W_inh_synapse_count_post_by_pre.npz", W_inh)

    summary = {
        "source_functional_cohort": str(FUNC_COHORT),
        "source_functional_matrix": str(FUNC_MATRIX),
        "source_synapse_cache": str(SOURCE_SYNAPSES),
        "selected_session": "9_3",
        "n_cohort": int(len(cohort)),
        "n_unique_pt_root_id": int(cohort["pt_root_id"].nunique()),
        "n_unique_functional_unit_id_within_session": int(
            cohort.drop_duplicates(["h5_key", "functional_unit_id"]).shape[0]
        ),
        "duplicates_used_to_increase_n": False,
        "go_threshold_enforced": False,
        "go_threshold_note": (
            "The original fallback threshold was 200 neurons, but the team has "
            "decided the 93-neuron session 9_3 V1 cohort is acceptable for the "
            "current analysis. This builder therefore records the cohort size "
            "but does not refuse to build below 200."
        ),
        "functional_matrix_shape": list(F.shape),
        "n_excitatory": int((cohort["classification_system"] == "excitatory_neuron").sum()),
        "n_inhibitory": int((cohort["classification_system"] == "inhibitory_neuron").sum()),
        "n_raw_synapse_rows_between_cohort": int(len(syn)),
        "n_autapses_removed": n_autapses,
        "n_directed_edges_all": int(W_all.nnz),
        "n_directed_edges_excitatory_pre": int(W_exc.nnz),
        "n_directed_edges_inhibitory_pre": int(W_inh.nnz),
        "directed_density_no_autapses": float(W_all.nnz / (len(cohort) * (len(cohort) - 1))),
        "total_synapse_count_no_autapses": int(W_all.sum()),
        "matrix_convention": "W[post, pre] = synapse count from pre neuron to post neuron",
        "method_note": (
            "This folder is aligned to the pushed 93-neuron functional matrix. "
            "The team's initial notebook reported 99 session 9_3 neurons before "
            "dropping 6 neurons missing from the V1 response matrix. No neurons "
            "are duplicated to reach a target threshold."
        ),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# Session 9_3 V1 Structural Output\n\n"
        "This structural network is aligned exactly to "
        "`outputs/functional_network/F_correlation_matrix.npy` and "
        "`outputs/functional_network/functional_cohort.csv`.\n\n"
        "Important: the functional notebook initially reports 99 neurons in "
        "session 9 scan 3, but the saved functional matrix contains 93 neurons "
        "after dropping 6 neurons not found in the V1 response matrix. Use this "
        "93-neuron output for comparisons with the pushed `F_correlation_matrix.npy`.\n\n"
        "Matrix convention: `W[post, pre] = synapse count from pre to post`.\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print(f"\nWrote {OUT_DIR}")


if __name__ == "__main__":
    main()
