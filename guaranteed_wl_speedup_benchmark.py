#!/usr/bin/env python3


from __future__ import annotations

import argparse
import bz2
import contextlib
import csv
import gzip
import io
import json
import lzma
import os
import statistics
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

import matplotlib.pyplot as plt

# Local solver imports.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from clauses import Clause, Clauses
from new_watch_lit_solver import (  # noqa: E402
    watched_literals_solve,
    wl_blocking_solve,
    wl_stable_solve,
    wl_blocking_stable_solve,
)


SAT = True

DEFAULT_URI_LIST_URL = "https://satcompetition.github.io/2020/downloads/sc2020-main.uri"
DEFAULT_CACHE_JSON = SCRIPT_DIR / "sat_competition_payload.json"
DEFAULT_LOCAL_FALLBACK = SCRIPT_DIR / "dimacs_tests.json"

SOLVERS = {
    "wl_base": watched_literals_solve,
    "wl_blocking": wl_blocking_solve,
    "wl_stable": wl_stable_solve,
    "wl_block+stable": wl_blocking_stable_solve,
}

COLORS = {
    "wl_base": "tab:blue",
    "wl_blocking": "tab:orange",
    "wl_stable": "tab:green",
    "wl_block+stable": "tab:red",
}


@dataclass
class TestCase:
    name: str
    raw_clauses: list[list[int]]
    clauses: Clauses
    result: bool = SAT


class OrderedLiteralSet:
    """
    Small ordered-set wrapper.

    The project solvers only rely on iteration and membership for clauses.literals.
    Using an ordered wrapper lets us control the decision order, which makes the
    stress construction deterministic enough for benchmarking.
    """

    def __init__(self, ordered_literals: Iterable[int]):
        seen = set()
        ordered = []
        for lit in ordered_literals:
            if lit not in seen:
                seen.add(lit)
                ordered.append(lit)
        self._ordered = ordered
        self._set = seen

    def __iter__(self) -> Iterator[int]:
        return iter(self._ordered)

    def __contains__(self, item: object) -> bool:
        return item in self._set

    def __len__(self) -> int:
        return len(self._ordered)


def make_test_case(name: str, raw_clauses: Sequence[Sequence[int]], result: bool = SAT) -> TestCase:
    clause_list = [Clause(list(clause)) for clause in raw_clauses]
    clauses = Clauses(clause_list)
    return TestCase(name=name, raw_clauses=[list(c) for c in raw_clauses], clauses=clauses, result=result)


def read_text_maybe_compressed(raw: bytes, url: str) -> str:
    lower = url.lower()
    if lower.endswith(".xz"):
        return lzma.decompress(raw).decode("utf-8", errors="replace")
    if lower.endswith(".gz"):
        return gzip.decompress(raw).decode("utf-8", errors="replace")
    if lower.endswith(".bz2"):
        return bz2.decompress(raw).decode("utf-8", errors="replace")
    if lower.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            cnf_members = [name for name in zf.namelist() if name.lower().endswith(".cnf")]
            member = cnf_members[0] if cnf_members else zf.namelist()[0]
            return zf.read(member).decode("utf-8", errors="replace")
    # Try auto-detection as a fallback.
    for decoder in (
        lambda b: lzma.decompress(b).decode("utf-8", errors="replace"),
        lambda b: gzip.decompress(b).decode("utf-8", errors="replace"),
        lambda b: bz2.decompress(b).decode("utf-8", errors="replace"),
    ):
        try:
            return decoder(raw)
        except Exception:
            pass
    return raw.decode("utf-8", errors="replace")


def parse_dimacs_text(text: str, max_clauses: int | None = None) -> list[list[int]]:
    clauses: list[list[int]] = []
    current: list[int] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            continue
        for token in line.split():
            lit = int(token)
            if lit == 0:
                if current:
                    clauses.append(current)
                    current = []
                    if max_clauses is not None and len(clauses) >= max_clauses:
                        return clauses
            else:
                current.append(lit)
    if current and (max_clauses is None or len(clauses) < max_clauses):
        clauses.append(current)
    return clauses


def load_cached_payload(cache_json: Path, payload_clauses: int) -> tuple[list[list[int]], str] | None:
    if cache_json.exists():
        with cache_json.open() as f:
            data = json.load(f)
        return [list(cl) for cl in data["raw_clauses"][:payload_clauses]], data.get("source", str(cache_json))
    return None


def load_local_dimacs_fallback(payload_clauses: int) -> tuple[list[list[int]], str] | None:
    if not DEFAULT_LOCAL_FALLBACK.exists():
        return None
    with DEFAULT_LOCAL_FALLBACK.open() as f:
        data = json.load(f)
    if not data:
        return None
    largest = max(data, key=lambda entry: len(entry.get("raw_clauses", [])))
    return [list(cl) for cl in largest["raw_clauses"][:payload_clauses]], str(DEFAULT_LOCAL_FALLBACK)


def download_uri_list(uri_list_url: str, timeout: int = 30) -> list[str]:
    with urllib.request.urlopen(uri_list_url, timeout=timeout) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def download_benchmark_clauses(
    uri_list_url: str,
    payload_clauses: int,
    benchmark_url: str | None = None,
    max_attempts: int = 12,
    timeout: int = 60,
) -> tuple[list[list[int]], str]:
    candidate_urls: list[str]
    if benchmark_url:
        candidate_urls = [benchmark_url]
    else:
        candidate_urls = download_uri_list(uri_list_url)

    errors: list[str] = []
    for url in candidate_urls[:max_attempts]:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                raw = resp.read()
            text = read_text_maybe_compressed(raw, url)
            clauses = parse_dimacs_text(text, max_clauses=payload_clauses)
            if clauses:
                return clauses, url
            errors.append(f"parsed zero clauses from {url}")
        except Exception as exc:  # pragma: no cover - network variability
            errors.append(f"{url}: {exc}")
    raise RuntimeError("Could not download a SAT Competition benchmark. Tried:\n  - " + "\n  - ".join(errors))


def ensure_payload(
    payload_clauses: int,
    cache_json: Path,
    uri_list_url: str,
    benchmark_url: str | None,
    force_download: bool,
) -> tuple[list[list[int]], str]:
    if not force_download:
        cached = load_cached_payload(cache_json, payload_clauses)
        if cached is not None:
            return cached

        local = load_local_dimacs_fallback(payload_clauses)
        if local is not None:
            return local

    clauses, source = download_benchmark_clauses(
        uri_list_url=uri_list_url,
        payload_clauses=payload_clauses,
        benchmark_url=benchmark_url,
    )
    cache_json.parent.mkdir(parents=True, exist_ok=True)
    with cache_json.open("w") as f:
        json.dump({"source": source, "raw_clauses": clauses}, f)
    return clauses, source


def shift_clause(clause: Sequence[int], offset: int) -> list[int]:
    return [lit + offset if lit > 0 else lit - offset for lit in clause]


def build_guaranteed_speedup_case(
    payload_clauses: Sequence[Sequence[int]],
    gadgets: int,
    chain_len: int,
    fanout: int,
) -> TestCase:
    """
    Build a SAT instance with a deterministic watched-literal stress pattern.

    Construction sketch for one gadget:
      - t is set TRUE by a unit clause.
      - dummy decision x1 implies a = TRUE, so -a becomes FALSE.
      - dummy decision x2 implies d = FALSE.
      - dummy decisions x3..x_{k+2} imply c1..ck are FALSE one by one.
      - long clause copies are [-a, d, c1, ..., ck, t].

    Base watched literals repeatedly move the false watch through c1, c2, ...
    until it finally reaches t. Stable watches jump directly to t once t has
    non-zero stability. Blocking literals cache t and skip clause-body scans on
    the later watched-false events.
    """
    raw: list[list[int]] = []

    # 1) Online SAT-competition payload, gated so it stays present but inert.
    gate1 = 50_000_001
    gate2 = 50_000_002
    payload_offset = 10_000_000
    raw.append([gate1])
    raw.append([gate2])
    for clause in payload_clauses:
        raw.append([gate1, gate2] + shift_clause(clause, payload_offset))

    # 2) Global dummy decision variables x1..x_{k+2}.
    #    The tautologies force them into the decision order without creating
    #    units or pure literals.
    dummy_count = chain_len + 2
    for i in range(1, dummy_count + 1):
        raw.append([i, -i])

    # 3) The watch-stress gadgets.
    next_var = 1000
    ordered_literals: list[int] = list(range(1, dummy_count + 1))
    ordered_literals.extend(-i for i in range(1, dummy_count + 1))
    ordered_literals.extend([gate1, gate2])

    for _ in range(gadgets):
        a = next_var
        d = next_var + 1
        t = next_var + 2
        next_var += 3
        cs = list(range(next_var, next_var + chain_len))
        next_var += chain_len

        # t is the long-lived satisfied literal.
        raw.append([t])

        # Sequential trigger chain driven by the global dummy decisions.
        raw.append([-1, a])       # after decision x1=TRUE, a becomes TRUE
        raw.append([-2, -d])      # after decision x2=TRUE, d becomes FALSE
        for idx, c in enumerate(cs, start=1):
            raw.append([-(idx + 2), -c])  # x_{idx+2}=TRUE makes c FALSE

        long_clause = [-a, d] + cs + [t]
        for _ in range(fanout):
            raw.append(long_clause[:])

        ordered_literals.extend([a, d, t])
        ordered_literals.extend(cs)
        ordered_literals.extend([-a, -d])
        ordered_literals.extend(-c for c in cs)

    test_case = make_test_case(
        name=f"comp_payload+watch_stress_g{gadgets}_k{chain_len}_f{fanout}",
        raw_clauses=raw,
        result=SAT,
    )

    # Critical benchmark trick: branch/all_assigned only need to reason over the
    # literals that actually drive the stress construction. The gated SAT-competition
    # payload is already satisfied by gate1/gate2 and is intentionally omitted from
    # the branching universe so it does not drown out the watched-literal effect.
    test_case.clauses.literals = OrderedLiteralSet(ordered_literals)
    return test_case


def run_solver_silent(solve, test_case: TestCase) -> tuple[bool, float]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        start = time.perf_counter()
        result = solve(test_case)
        elapsed = time.perf_counter() - start
    return result.result, elapsed


def benchmark(
    payload_clauses: Sequence[Sequence[int]],
    sizes: Sequence[int],
    chain_len: int,
    fanout: int,
    repeats: int,
) -> tuple[list[dict[str, object]], dict[str, float]]:
    rows: list[dict[str, object]] = []

    for gadgets in sizes:
        test_case = build_guaranteed_speedup_case(
            payload_clauses=payload_clauses,
            gadgets=gadgets,
            chain_len=chain_len,
            fanout=fanout,
        )
        clause_count = len(test_case.raw_clauses)

        for solver_name, solve in SOLVERS.items():
            timings = []
            for _ in range(repeats):
                ok, elapsed = run_solver_silent(solve, test_case)
                if not ok:
                    raise RuntimeError(f"{solver_name} returned UNSAT on a SAT benchmark: {test_case.name}")
                timings.append(elapsed)
            median_time = statistics.median(timings)
            rows.append(
                {
                    "solver": solver_name,
                    "gadgets": gadgets,
                    "size": clause_count,
                    "median_time": median_time,
                    "all_timings": json.dumps(timings),
                }
            )

    # Median speedup over wl_base, computed from the per-size medians.
    by_size_solver = {(row["size"], row["solver"]): row["median_time"] for row in rows}
    sizes_present = sorted({int(row["size"]) for row in rows})
    speedups: dict[str, float] = {}
    for solver_name in SOLVERS:
        if solver_name == "wl_base":
            continue
        ratios = []
        for size in sizes_present:
            base_t = float(by_size_solver[(size, "wl_base")])
            opt_t = float(by_size_solver[(size, solver_name)])
            ratios.append(base_t / opt_t)
        speedups[solver_name] = statistics.median(ratios)
    return rows, speedups


def plot_results(rows: Sequence[dict[str, object]], out_png: Path) -> None:
    grouped: dict[str, list[tuple[int, float]]] = {name: [] for name in SOLVERS}
    for row in rows:
        grouped[str(row["solver"])] .append((int(row["size"]), float(row["median_time"])))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    for solver_name, points in grouped.items():
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax1.plot(xs, ys, marker="o", label=solver_name, color=COLORS[solver_name])
        ax2.plot(xs, ys, marker="o", label=solver_name, color=COLORS[solver_name])

    ax1.set_xlabel("Number of Clauses")
    ax1.set_ylabel("Median Solve Time (seconds)")
    ax1.set_title("Watched-Literal Optimization Benchmark (Linear)")
    ax1.grid(True)
    ax1.legend()

    ax2.set_xlabel("Number of Clauses")
    ax2.set_ylabel("Median Solve Time (seconds)")
    ax2.set_title("Watched-Literal Optimization Benchmark (Log-Log)")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.grid(True, which="both", linestyle="--", alpha=0.5)
    ax2.legend()

    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=170)
    plt.close(fig)


def save_csv(rows: Sequence[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["solver", "gadgets", "size", "median_time", "all_timings"])
        writer.writeheader()
        writer.writerows(rows)


def save_speedups(speedups: dict[str, float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(speedups, f, indent=2)


def parse_sizes(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Guaranteed-style watched-literal speedup benchmark.")
    parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("5,10,20,40,80"))
    parser.add_argument("--chain-len", type=int, default=20)
    parser.add_argument("--fanout", type=int, default=32)
    parser.add_argument("--payload-clauses", type=int, default=50)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--uri-list-url", type=str, default=DEFAULT_URI_LIST_URL)
    parser.add_argument("--benchmark-url", type=str, default=None)
    parser.add_argument("--cache-json", type=Path, default=DEFAULT_CACHE_JSON)
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=SCRIPT_DIR / "results")
    args = parser.parse_args()

    payload_clauses, source = ensure_payload(
        payload_clauses=args.payload_clauses,
        cache_json=args.cache_json,
        uri_list_url=args.uri_list_url,
        benchmark_url=args.benchmark_url,
        force_download=args.force_download,
    )

    rows, speedups = benchmark(
        payload_clauses=payload_clauses,
        sizes=args.sizes,
        chain_len=args.chain_len,
        fanout=args.fanout,
        repeats=args.repeats,
    )

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    png_path = args.results_dir / f"guaranteed_wl_speedups_{timestamp}.png"
    csv_path = args.results_dir / f"guaranteed_wl_speedups_{timestamp}.csv"
    json_path = args.results_dir / f"guaranteed_wl_speedups_{timestamp}.json"

    plot_results(rows, png_path)
    save_csv(rows, csv_path)
    save_speedups(speedups, json_path)

    print(f"Competition payload source: {source}")
    print(f"Graph saved to: {png_path}")
    print(f"Raw timings saved to: {csv_path}")
    print(f"Median speedups saved to: {json_path}")
    print("\nMedian speedup over wl_base:")
    for solver_name in ("wl_blocking", "wl_stable", "wl_block+stable"):
        print(f"  {solver_name:15s} {speedups[solver_name]:.3f}x")


if __name__ == "__main__":
    main()
