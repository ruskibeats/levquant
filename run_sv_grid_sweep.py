"""
Deterministic SV grid sweep and heatmap visualiser.

Runs the engine across a fixed insight grid to map leverage terrain and
decision cliff zones.

Run:
    python run_sv_grid_sweep.py
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

from cli.run import run_engine


SV1A_GRID = [0.15, 0.22, 0.28, 0.32, 0.35, 0.38, 0.42, 0.46, 0.50, 0.56, 0.65]
SV1B_GRID = [0.50, 0.58, 0.64, 0.70, 0.76, 0.82, 0.86, 0.90, 0.96]
SV1C_GRID = [0.45, 0.60, 0.75, 0.85, 0.95]

DECISION_TO_INT = {
    "REJECT": 0,
    "HOLD": 1,
    "COUNTER": 2,
    "ACCEPT": 3,
}
INT_TO_DECISION = {v: k for k, v in DECISION_TO_INT.items()}


def run_grid_sweep(
    sv1a_grid: List[float],
    sv1b_grid: List[float],
    sv1c_grid: List[float],
) -> List[Dict]:
    """Run deterministic engine across full 3D grid."""
    rows: List[Dict] = []
    for sv1c in sv1c_grid:
        for sv1a in sv1a_grid:
            for sv1b in sv1b_grid:
                state = {"SV1a": sv1a, "SV1b": sv1b, "SV1c": sv1c}
                out = run_engine(state=state)
                rows.append(
                    {
                        "SV1a": sv1a,
                        "SV1b": sv1b,
                        "SV1c": sv1c,
                        "upls": out["scores"]["upls"],
                        "tripwire": out["scores"]["tripwire"],
                        "decision": out["evaluation"]["decision"],
                        "confidence": out["evaluation"]["confidence"],
                        "tripwire_triggered": out["evaluation"]["tripwire_triggered"],
                    }
                )
    return rows


def _slice_rows(rows: List[Dict], sv1c: float) -> List[Dict]:
    return [r for r in rows if r["SV1c"] == sv1c]


def _matrix(rows_slice: List[Dict], sv1a_grid: List[float], sv1b_grid: List[float], key: str):
    lookup = {(r["SV1a"], r["SV1b"]): r[key] for r in rows_slice}
    return [[lookup[(a, b)] for b in sv1b_grid] for a in sv1a_grid]


def write_csvs(rows: List[Dict], output_grid_dir: Path, sv1c_grid: List[float]) -> None:
    output_grid_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "SV1a",
        "SV1b",
        "SV1c",
        "upls",
        "tripwire",
        "decision",
        "confidence",
        "tripwire_triggered",
    ]

    all_path = output_grid_dir / "grid_all.csv"
    with all_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    for sv1c in sv1c_grid:
        slice_path = output_grid_dir / f"grid_sv1c_{sv1c:.2f}.csv"
        with slice_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(_slice_rows(rows, sv1c))


def generate_heatmaps(
    rows: List[Dict],
    sv1a_grid: List[float],
    sv1b_grid: List[float],
    sv1c_grid: List[float],
    plots_dir: Path,
) -> None:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch
    except ModuleNotFoundError:
        print("matplotlib not installed; skipping heatmap generation")
        return

    plots_dir.mkdir(parents=True, exist_ok=True)

    decision_cmap = ListedColormap(["#d73027", "#fee08b", "#91bfdb", "#1a9850"])
    decision_legend = [
        Patch(facecolor="#d73027", label="REJECT"),
        Patch(facecolor="#fee08b", label="HOLD"),
        Patch(facecolor="#91bfdb", label="COUNTER"),
        Patch(facecolor="#1a9850", label="ACCEPT"),
    ]

    for sv1c in sv1c_grid:
        rows_slice = _slice_rows(rows, sv1c)
        upls_mat = _matrix(rows_slice, sv1a_grid, sv1b_grid, "upls")
        dec_mat = _matrix(rows_slice, sv1a_grid, sv1b_grid, "decision")
        dec_int_mat = [[DECISION_TO_INT[v] for v in row] for row in dec_mat]

        # UPLS heatmap
        fig, ax = plt.subplots(figsize=(10, 7))
        im = ax.imshow(upls_mat, cmap="viridis", origin="lower", aspect="auto")
        ax.set_xticks(range(len(sv1b_grid)))
        ax.set_xticklabels([f"{v:.2f}" for v in sv1b_grid], rotation=45, ha="right")
        ax.set_yticks(range(len(sv1a_grid)))
        ax.set_yticklabels([f"{v:.2f}" for v in sv1a_grid])
        ax.set_xlabel("SV1b")
        ax.set_ylabel("SV1a")
        ax.set_title(f"UPLS Heatmap (SV1c={sv1c:.2f})")
        fig.colorbar(im, ax=ax, label="UPLS")
        fig.tight_layout()
        fig.savefig(plots_dir / f"heatmap_upls_sv1c_{sv1c:.2f}.png", dpi=150)
        plt.close(fig)

        # Decision heatmap
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.imshow(dec_int_mat, cmap=decision_cmap, origin="lower", aspect="auto", vmin=0, vmax=3)
        ax.set_xticks(range(len(sv1b_grid)))
        ax.set_xticklabels([f"{v:.2f}" for v in sv1b_grid], rotation=45, ha="right")
        ax.set_yticks(range(len(sv1a_grid)))
        ax.set_yticklabels([f"{v:.2f}" for v in sv1a_grid])
        ax.set_xlabel("SV1b")
        ax.set_ylabel("SV1a")
        ax.set_title(f"Decision Heatmap (SV1c={sv1c:.2f})")
        ax.legend(handles=decision_legend, loc="upper left", bbox_to_anchor=(1.02, 1.0))
        fig.tight_layout()
        fig.savefig(plots_dir / f"heatmap_decision_sv1c_{sv1c:.2f}.png", dpi=150)
        plt.close(fig)


def find_cliffs(
    rows: List[Dict],
    sv1a_grid: List[float],
    sv1b_grid: List[float],
    sv1c_grid: List[float],
) -> List[Tuple[float, float, float, str, str]]:
    """Find 4-neighbour adjacency decision changes for each SV1c slice."""
    cliffs: List[Tuple[float, float, float, str, str]] = []
    for sv1c in sv1c_grid:
        rows_slice = _slice_rows(rows, sv1c)
        dec_mat = _matrix(rows_slice, sv1a_grid, sv1b_grid, "decision")
        for i in range(len(sv1a_grid)):
            for j in range(len(sv1b_grid)):
                cur = dec_mat[i][j]
                if i + 1 < len(sv1a_grid) and dec_mat[i + 1][j] != cur:
                    cliffs.append((sv1a_grid[i], sv1b_grid[j], sv1c, cur, dec_mat[i + 1][j]))
                if j + 1 < len(sv1b_grid) and dec_mat[i][j + 1] != cur:
                    cliffs.append((sv1a_grid[i], sv1b_grid[j], sv1c, cur, dec_mat[i][j + 1]))
    return cliffs


def print_summary(rows: List[Dict], sv1c_grid: List[float]) -> None:
    print(f"Total grid points: {len(rows)}")
    print()
    for sv1c in sv1c_grid:
        slice_rows = _slice_rows(rows, sv1c)
        counts = {"REJECT": 0, "HOLD": 0, "COUNTER": 0, "ACCEPT": 0}
        for r in slice_rows:
            counts[r["decision"]] += 1
        upls_vals = [r["upls"] for r in slice_rows]
        print(f"SV1c={sv1c:.2f}")
        print(f"  decision counts: {counts}")
        print(
            f"  UPLS min/max/mean: {min(upls_vals):.3f} / {max(upls_vals):.3f} / {sum(upls_vals)/len(upls_vals):.3f}"
        )
        print()


def main() -> None:
    output_grid_dir = Path("outputs/grid")
    plots_dir = Path("outputs/grid/plots")

    rows = run_grid_sweep(SV1A_GRID, SV1B_GRID, SV1C_GRID)
    write_csvs(rows, output_grid_dir, SV1C_GRID)
    generate_heatmaps(rows, SV1A_GRID, SV1B_GRID, SV1C_GRID, plots_dir)
    print_summary(rows, SV1C_GRID)

    cliffs = find_cliffs(rows, SV1A_GRID, SV1B_GRID, SV1C_GRID)
    print(f"Cliff transitions found (4-neighbour): {len(cliffs)}")
    for c in cliffs[:20]:
        sv1a, sv1b, sv1c, d1, d2 = c
        print(f"  SV1c={sv1c:.2f}, SV1a={sv1a:.2f}, SV1b={sv1b:.2f}: {d1} -> {d2}")


if __name__ == "__main__":
    main()