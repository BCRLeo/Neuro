"""Build the Project 7 structural network for the matched MICrONS cohort.

Outputs are written under Leo/outputs/structural_network/.

Methodological choices encoded here:
- The analysis cohort is restricted to neurons with both structural annotations
  and a functional recording in the same calcium-imaging session.
- Presynaptic cell class is used to keep excitatory and inhibitory structural
  edges separate.
- The structural adjacency uses synapse counts, not synapse area:
      W[post, pre] = number of synapses from pre neuron to post neuron.
- Autapses are removed before any graph construction.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp

import microns_datacleaner.filters as fl
import microns_datacleaner.processing as proc


VERSION = 1718
GO_THRESHOLD = 200
DATASET = "minnie65_public"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LEO_RAW = SCRIPT_DIR / "data" / str(VERSION) / "raw"
SHARED_RAW = REPO_ROOT / "data" / str(VERSION) / "raw"
H5_PATH = REPO_ROOT / "data" / "functional" / "microns_functional.h5"
OUT_BASE = SCRIPT_DIR / "outputs" / "structural_network"

TABLES = {
    "nucleus": "nucleus_detection_v0",
    "proofreading": "proofreading_status_and_strategy",
    "brain_areas": "nucleus_functional_area_assignment",
    "celltype_full": "aibs_metamodel_celltypes_v661",
    "celltype_corrections": "aibs_metamodel_celltypes_v661_corrections",
    "func_props": "digital_twin_properties_bcm_coreg_v4",
}


@dataclass
class BuildSummary:
    version: int
    cohort_scope: str
    proofread_policy: str
    h5_path: str
    n_units_after_structural_merge: int
    n_functionally_matched_unique: int
    n_ax_clean_functionally_matched_unique: int
    selected_session: str
    selected_session_unique_neurons: int
    go_threshold: int
    go_for_structure_function: bool
    n_cohort: int
    n_excitatory: int
    n_inhibitory: int
    n_cohort_ax_clean: int
    n_cohort_axon_unproofread: int
    n_synapse_rows_raw: int
    n_autapses_removed: int
    n_directed_edges_all: int
    n_directed_edges_excitatory_pre: int
    n_directed_edges_inhibitory_pre: int
    directed_density_no_autapses: float
    total_synapse_count_no_autapses: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download-missing-tables",
        action="store_true",
        help="Download missing nucleus metadata tables into Leo/data/1718/raw.",
    )
    parser.add_argument(
        "--download-synapses",
        action="store_true",
        help="Query CAVE for cohort synapses and cache them under Leo/outputs.",
    )
    parser.add_argument(
        "--cohort-scope",
        choices=["session", "all-matched"],
        default="session",
        help=(
            "'session' builds the strict structure-function cohort from one h5 "
            "session; 'all-matched' builds a larger structural-only graph from "
            "all axon-clean functionally matched neurons."
        ),
    )
    parser.add_argument(
        "--proofread-policy",
        choices=["axon-clean", "matched-all"],
        default="axon-clean",
        help=(
            "'axon-clean' keeps only neurons with proofread axons; "
            "'matched-all' keeps all matched excitatory/inhibitory neurons and "
            "records proofreading status as a limitation."
        ),
    )
    parser.add_argument(
        "--synapse-batch-size",
        type=int,
        default=200,
        help="Number of postsynaptic IDs per synapse query batch.",
    )
    parser.add_argument(
        "--allow-small-cohort",
        action="store_true",
        help="Build outputs even if the selected functional session is below the go threshold.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download_table(table: str, out_path: Path) -> None:
    from caveclient import CAVEclient

    ensure_dir(out_path.parent)
    client = CAVEclient(DATASET)
    client.materialize.version = VERSION
    df = client.materialize.query_table(table, split_positions=True)
    pd.DataFrame(df).to_csv(out_path, index=False)


def table_path(table: str, *, download_missing: bool) -> Path:
    """Return a readable table path, preferring Leo-local files over shared data."""
    candidates = [LEO_RAW / f"{table}.csv", SHARED_RAW / f"{table}.csv"]
    for path in candidates:
        if path.exists():
            return path
    if download_missing:
        target = LEO_RAW / f"{table}.csv"
        print(f"Downloading missing table {table} -> {target}")
        download_table(table, target)
        return target
    raise FileNotFoundError(
        f"Could not find {table}.csv in {LEO_RAW} or {SHARED_RAW}. "
        "Re-run with --download-missing-tables."
    )


def read_table(table: str, *, download_missing: bool) -> pd.DataFrame:
    path = table_path(table, download_missing=download_missing)
    return pd.read_csv(path)


def read_celltype_table(*, download_missing: bool) -> pd.DataFrame:
    """Use the full cell-type table, not the small corrections-only table."""
    full_path = LEO_RAW / f"{TABLES['celltype_full']}.csv"
    shared_full_path = SHARED_RAW / f"{TABLES['celltype_full']}.csv"
    if full_path.exists() or shared_full_path.exists():
        return read_table(TABLES["celltype_full"], download_missing=download_missing)
    if download_missing:
        target = LEO_RAW / f"{TABLES['celltype_full']}.csv"
        print(f"Downloading full cell-type table -> {target}")
        download_table(TABLES["celltype_full"], target)
        return pd.read_csv(target)

    corrections = read_table(TABLES["celltype_corrections"], download_missing=False)
    raise RuntimeError(
        "Only the corrections-only cell-type table is available "
        f"({len(corrections):,} rows). That table collapses the cohort to a tiny "
        "subset and is not suitable for Project 7. Re-run with "
        "--download-missing-tables to fetch aibs_metamodel_celltypes_v661."
    )


def build_units(download_missing: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    nucleus = read_table(TABLES["nucleus"], download_missing=download_missing)
    celltype = read_celltype_table(download_missing=download_missing)
    proofread = read_table(TABLES["proofreading"], download_missing=download_missing)
    areas = read_table(TABLES["brain_areas"], download_missing=download_missing)
    funcprops = read_table(TABLES["func_props"], download_missing=download_missing)

    nucleus = nucleus.rename(columns={"id": "nucleus_id"})
    units = proc.merge_nucleus_with_cell_types(nucleus, celltype)
    units = proc.merge_brain_area(units, areas)
    units = proc.merge_proofreading_status(units, proofread, VERSION)
    units = proc.transform_positions(units)
    segments = proc.divide_volume_into_segments(units)
    segments = proc.merge_segments_by_layer(segments)
    proc.add_layer_info(units, segments)

    # Remove invalid roots and multisoma objects, matching microns-datacleaner.
    units = units[units["pt_root_id"] > 0]
    units = units.drop_duplicates(subset="pt_root_id", keep=False)

    units = proc.merge_functional_properties(units, funcprops, mode="all")
    units.loc[units["tuning_type"].isna(), "tuning_type"] = "not_matched"
    return units.reset_index(drop=True), segments


def add_h5_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    valid = out["session"].notna() & out["scan_idx"].notna()
    out = out[valid].copy()
    out["h5_key"] = (
        out["session"].astype(int).astype(str)
        + "_"
        + out["scan_idx"].astype(int).astype(str)
    )
    return out


def available_h5_units() -> dict[str, set[int]]:
    if not H5_PATH.exists():
        raise FileNotFoundError(f"Functional h5 not found: {H5_PATH}")
    with h5py.File(H5_PATH, "r") as f:
        return {
            key: set(f[f"sessions/{key}/meta/unit_ids"][:].astype(int))
            for key in f["sessions"].keys()
        }


def choose_cohort(
    units: pd.DataFrame, cohort_scope: str, proofread_policy: str
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    h5_units = available_h5_units()
    h5_sessions = set(h5_units)

    matched = fl.filter_neurons(units, tuning="matched").copy()
    matched = add_h5_key(matched)
    matched = matched[matched["h5_key"].isin(h5_sessions)].copy()
    matched["functional_unit_id"] = matched["functional_unit_id"].astype(int)
    matched = matched[
        matched.apply(
            lambda r: int(r["functional_unit_id"]) in h5_units[r["h5_key"]],
            axis=1,
        )
    ].copy()

    matched_neurons = matched[
        matched["classification_system"].isin(["excitatory_neuron", "inhibitory_neuron"])
    ].copy()
    if proofread_policy == "axon-clean":
        analysis_pool = fl.filter_neurons(matched_neurons, proofread="ax_clean").copy()
    elif proofread_policy == "matched-all":
        analysis_pool = matched_neurons.copy()
    else:
        raise ValueError(f"Unknown proofread_policy: {proofread_policy}")

    if analysis_pool.empty:
        raise RuntimeError(
            f"No functionally matched neurons pass proofread_policy={proofread_policy!r}. "
            "Check the metadata cache before proceeding."
        )

    dedup_by_session = analysis_pool.sort_values("cc_abs", ascending=False).drop_duplicates(
        subset=["h5_key", "pt_root_id"], keep="first"
    )
    session_counts = dedup_by_session.groupby("h5_key").size().sort_values(ascending=False)
    best_session = str(session_counts.index[0])

    if cohort_scope == "session":
        cohort = (
            analysis_pool[analysis_pool["h5_key"] == best_session]
            .sort_values("cc_abs", ascending=False)
            .drop_duplicates(subset="pt_root_id", keep="first")
            .reset_index(drop=True)
        )
    elif cohort_scope == "all-matched":
        # This graph is useful for structural-only topology, but not for one
        # functional correlation matrix because rows span different sessions.
        cohort = (
            analysis_pool.sort_values("cc_abs", ascending=False)
            .drop_duplicates(subset="pt_root_id", keep="first")
            .reset_index(drop=True)
        )
    else:
        raise ValueError(f"Unknown cohort_scope: {cohort_scope}")

    if cohort.duplicated(subset=["h5_key", "functional_unit_id"]).any():
        dupes = cohort.loc[
            cohort.duplicated(subset=["h5_key", "functional_unit_id"], keep=False),
            ["pt_root_id", "h5_key", "functional_unit_id"],
        ]
        raise RuntimeError(
            "Duplicated functional_unit_id values within the same h5 session:\n"
            f"{dupes}"
        )

    return cohort, session_counts, matched


def chunks(values: np.ndarray, size: int) -> Iterable[np.ndarray]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def download_synapses(ids: np.ndarray, batch_size: int, out_path: Path) -> pd.DataFrame:
    from caveclient import CAVEclient

    ensure_dir(out_path.parent)
    client = CAVEclient(DATASET)
    client.materialize.version = VERSION
    synapse_table = client.info.get_datastack_info()["synapse_table"]

    frames = []
    for part, post_ids in enumerate(chunks(ids, batch_size)):
        print(f"Synapse query batch {part + 1}: {len(post_ids)} post IDs")
        df = client.materialize.query_table(
            synapse_table,
            filter_in_dict={
                "pre_pt_root_id": ids,
                "post_pt_root_id": post_ids,
            },
            select_columns=["id", "pre_pt_root_id", "post_pt_root_id", "size"],
            split_positions=True,
        )
        frames.append(pd.DataFrame(df))

    synapses = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    synapses.to_csv(out_path, index=False)
    return synapses


def load_synapses(ids: np.ndarray, args: argparse.Namespace, out_dir: Path) -> pd.DataFrame:
    raw_path = out_dir / "cohort_synapses_raw.csv"
    if args.download_synapses:
        return download_synapses(ids, args.synapse_batch_size, raw_path)
    if raw_path.exists():
        return pd.read_csv(raw_path)

    bad_shared_cache = SHARED_RAW / "cohort_synapses.csv"
    if bad_shared_cache.exists():
        n_rows = sum(1 for _ in bad_shared_cache.open("r", encoding="utf-8")) - 1
        raise RuntimeError(
            f"No Leo-local synapse cache found at {raw_path}. The shared cache "
            f"{bad_shared_cache} has only {n_rows} rows and should not be trusted. "
            "Re-run with --download-synapses."
        )
    raise FileNotFoundError(f"No synapse cache found at {raw_path}. Use --download-synapses.")


def edge_table_from_synapses(
    synapses: pd.DataFrame, cohort: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    ids = set(cohort["pt_root_id"].astype(np.int64))
    required = {"pre_pt_root_id", "post_pt_root_id", "size"}
    missing = required.difference(synapses.columns)
    if missing:
        raise ValueError(f"Synapse table missing columns: {sorted(missing)}")

    syn = synapses.copy()
    syn["pre_pt_root_id"] = syn["pre_pt_root_id"].astype(np.int64)
    syn["post_pt_root_id"] = syn["post_pt_root_id"].astype(np.int64)
    syn = syn[syn["pre_pt_root_id"].isin(ids) & syn["post_pt_root_id"].isin(ids)]

    autapse_mask = syn["pre_pt_root_id"] == syn["post_pt_root_id"]
    n_autapses = int(autapse_mask.sum())
    syn = syn[~autapse_mask].copy()

    edge = (
        syn.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False)
        .agg(synapse_count=("size", "size"), synapse_size_sum=("size", "sum"))
        .sort_values(["pre_pt_root_id", "post_pt_root_id"])
        .reset_index(drop=True)
    )
    return edge, n_autapses


def adjacency_from_edges(
    edge: pd.DataFrame, cohort: pd.DataFrame, pre_class: str | None = None
) -> sp.csr_matrix:
    if pre_class is not None:
        class_by_id = cohort.set_index("pt_root_id")["classification_system"].to_dict()
        keep_pre = {
            int(root_id)
            for root_id, cls in class_by_id.items()
            if cls == pre_class
        }
        edge = edge[edge["pre_pt_root_id"].isin(keep_pre)]

    id_to_idx = {int(root_id): i for i, root_id in enumerate(cohort["pt_root_id"])}
    rows = edge["post_pt_root_id"].map(id_to_idx).astype(int).to_numpy()
    cols = edge["pre_pt_root_id"].map(id_to_idx).astype(int).to_numpy()
    data = edge["synapse_count"].astype(np.float64).to_numpy()
    return sp.csr_matrix((data, (rows, cols)), shape=(len(cohort), len(cohort)))


def write_outputs(
    units: pd.DataFrame,
    matched: pd.DataFrame,
    session_counts: pd.Series,
    cohort: pd.DataFrame,
    synapses: pd.DataFrame,
    edge: pd.DataFrame,
    n_autapses: int,
    out_dir: Path,
    args: argparse.Namespace,
) -> BuildSummary:
    ensure_dir(out_dir)

    W_all = adjacency_from_edges(edge, cohort)
    W_exc = adjacency_from_edges(edge, cohort, "excitatory_neuron")
    W_inh = adjacency_from_edges(edge, cohort, "inhibitory_neuron")

    if W_all.nnz != W_exc.nnz + W_inh.nnz:
        raise RuntimeError("E/I edge split does not sum to all structural edges.")
    if W_all.diagonal().sum() != 0:
        raise RuntimeError("Autapses remain in W_all.")

    cohort_out = cohort.copy()
    cohort_out.insert(0, "matrix_index", np.arange(len(cohort_out)))

    cohort_cols = [
        "matrix_index",
        "nucleus_id",
        "pt_root_id",
        "classification_system",
        "cell_type",
        "layer",
        "brain_area",
        "strategy_axon",
        "strategy_dendrite",
        "pt_position_x",
        "pt_position_y",
        "pt_position_z",
        "session",
        "scan_idx",
        "functional_unit_id",
        "cc_abs",
        "h5_key",
    ]
    cohort_out[cohort_cols].to_csv(out_dir / "cohort_neurons.csv", index=False)
    edge.to_csv(out_dir / "structural_edges.csv", index=False)
    session_counts.rename("n_matched_unique").to_csv(
        out_dir / "session_counts.csv", header=True
    )
    sp.save_npz(out_dir / "W_all_synapse_count_post_by_pre.npz", W_all)
    sp.save_npz(out_dir / "W_exc_synapse_count_post_by_pre.npz", W_exc)
    sp.save_npz(out_dir / "W_inh_synapse_count_post_by_pre.npz", W_inh)

    n = len(cohort)
    density = W_all.nnz / (n * (n - 1)) if n > 1 else 0.0
    summary = BuildSummary(
        version=VERSION,
        cohort_scope=args.cohort_scope,
        proofread_policy=args.proofread_policy,
        h5_path=str(H5_PATH),
        n_units_after_structural_merge=int(units["pt_root_id"].nunique()),
        n_functionally_matched_unique=int(matched["pt_root_id"].nunique()),
        n_ax_clean_functionally_matched_unique=int(
            fl.filter_neurons(matched, proofread="ax_clean")["pt_root_id"].nunique()
        ),
        selected_session=(
            str(cohort["h5_key"].iloc[0])
            if cohort["h5_key"].nunique() == 1
            else "ALL_MATCHED_MULTISSESSION_STRUCTURAL_ONLY"
        ),
        selected_session_unique_neurons=n,
        go_threshold=GO_THRESHOLD,
        go_for_structure_function=bool(n >= GO_THRESHOLD and cohort["h5_key"].nunique() == 1),
        n_cohort=n,
        n_excitatory=int((cohort["classification_system"] == "excitatory_neuron").sum()),
        n_inhibitory=int((cohort["classification_system"] == "inhibitory_neuron").sum()),
        n_cohort_ax_clean=int((cohort["strategy_axon"] != "none").sum()),
        n_cohort_axon_unproofread=int((cohort["strategy_axon"] == "none").sum()),
        n_synapse_rows_raw=int(len(synapses)),
        n_autapses_removed=n_autapses,
        n_directed_edges_all=int(W_all.nnz),
        n_directed_edges_excitatory_pre=int(W_exc.nnz),
        n_directed_edges_inhibitory_pre=int(W_inh.nnz),
        directed_density_no_autapses=float(density),
        total_synapse_count_no_autapses=int(W_all.sum()),
    )
    (out_dir / "summary.json").write_text(
        json.dumps(asdict(summary), indent=2), encoding="utf-8"
    )

    review = [
        "# Structural Network Build Review",
        "",
        "Root `structural_network.ipynb` was useful as exploration, but it should not be treated as final methods because:",
        "- it reports a 906-neuron all-session matched structural graph, which is not automatically a valid functional-correlation cohort;",
        "- it collapses E/I edges for several analyses;",
        "- it uses synaptic size where the project definition asks for synapse count;",
        "- it compares small-world metrics to an ER-like baseline rather than a degree-preserving configuration model.",
        "",
        "This build instead writes directed matrices with rows as postsynaptic neurons and columns as presynaptic neurons:",
        "- `W_all_synapse_count_post_by_pre.npz`",
        "- `W_exc_synapse_count_post_by_pre.npz`",
        "- `W_inh_synapse_count_post_by_pre.npz`",
        "",
        f"Selected functional session: `{summary.selected_session}`",
        f"Cohort size: `{summary.n_cohort}` neurons",
        f"Proofread policy: `{summary.proofread_policy}`",
        f"Axon-clean neurons in cohort: `{summary.n_cohort_ax_clean}`",
        f"Unproofread-axon neurons in cohort: `{summary.n_cohort_axon_unproofread}`",
        f"Go threshold met: `{summary.go_for_structure_function}`",
        f"Directed structural edges after autapse removal: `{summary.n_directed_edges_all}`",
        "",
        "Do not claim structure-function results from the all-matched multisession graph.",
        "Do not claim structure-function results if `go_for_structure_function` is false.",
    ]
    (out_dir / "BUILD_REVIEW.md").write_text("\n".join(review) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    args = parse_args()
    out_dir = OUT_BASE / f"{args.cohort_scope}_{args.proofread_policy}"
    ensure_dir(out_dir)

    units, _segments = build_units(args.download_missing_tables)
    cohort, session_counts, matched = choose_cohort(
        units, args.cohort_scope, args.proofread_policy
    )

    print(f"{args.proofread_policy} matched neurons per h5 session:")
    print(session_counts.to_string())
    if args.cohort_scope == "session":
        print(f"\nSelected cohort: {cohort['h5_key'].iloc[0]} with N={len(cohort)}")
    else:
        print(
            "\nSelected cohort: all axon-clean matched neurons across h5 sessions "
            f"with N={len(cohort)}"
        )

    strict_session = args.cohort_scope == "session"
    if strict_session and len(cohort) < GO_THRESHOLD and not args.allow_small_cohort:
        raise RuntimeError(
            f"Selected session has only {len(cohort)} neurons below the "
            f"go threshold ({GO_THRESHOLD}). Use --allow-small-cohort only for "
            "debugging or pivot to the structural-only fallback."
        )

    ids = cohort["pt_root_id"].astype(np.int64).to_numpy()
    synapses = load_synapses(ids, args, out_dir)
    edge, n_autapses = edge_table_from_synapses(synapses, cohort)
    summary = write_outputs(
        units, matched, session_counts, cohort, synapses, edge, n_autapses, out_dir, args
    )

    print("\nBuild summary")
    for key, value in asdict(summary).items():
        print(f"{key}: {value}")
    print(f"\nOutputs written to {out_dir}")


if __name__ == "__main__":
    main()
