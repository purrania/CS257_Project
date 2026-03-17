#!/usr/bin/env python3
"""Quick inspection of dimacs_tests.json: clause length stats and example clauses."""

import json
from collections import Counter
import matplotlib.pyplot as plt

with open("dimacs_tests.json") as f:
    data = json.load(f)

all_clause_lens = [len(c) for entry in data for c in entry["raw_clauses"]]
print("=== Overall Stats ===")
print(f"  Total clauses: {len(all_clause_lens)}")
print(f"  Avg clause length: {sum(all_clause_lens) / len(all_clause_lens):.2f}")
print(f"  Max clause length: {max(all_clause_lens)}")
print()

for entry in data:
    clauses = entry["raw_clauses"]
    clause_lens = [len(c) for c in clauses]
    avg_len = sum(clause_lens) / len(clause_lens)
    max_len = max(clause_lens)

    print(f"--- {entry['name']} ---")
    print(f"  Clauses: {len(clauses)}  Avg length: {avg_len:.2f}  Max length: {max_len}")
    print(f"  Example clauses:")
    for c in clauses[:5]:
        print(f"    {c}")
    print()

# Histogram of clause lengths
counts = Counter(all_clause_lens)
lengths = sorted(counts.keys())
freqs = [counts[l] for l in lengths]

plt.figure(figsize=(10, 5))
plt.bar(lengths, freqs)
plt.xlabel("Clause Length")
plt.ylabel("Count")
plt.title("Distribution of Clause Lengths in DIMACS Test Cases")
plt.xticks(lengths)
plt.grid(axis="y", alpha=0.5)
plt.tight_layout()
plt.savefig("results/clause_length_histogram.png", dpi=150)
print("Histogram saved to results/clause_length_histogram.png")
