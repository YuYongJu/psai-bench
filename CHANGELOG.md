# Changelog

## 1.0.0 (2026-04-12)

Initial open-source release of PSAI-Bench.

### Features

- **3-track scenario generation**: Metadata, Visual, and Multi-Sensor tracks grounded in UCF Crime and Caltech Pedestrian datasets
- **Safety-weighted scoring engine**: TDR, FASR, Safety Score, ECE, Brier Score, and Aggregate Score with SUSPICIOUS penalty
- **4 statistical baselines**: Random, Majority Class, Always Suspicious, Severity Heuristic
- **Frontier model evaluators**: Claude Sonnet, GPT-4o, Gemini Flash via API
- **Statistical comparison**: McNemar's test, bootstrap confidence intervals, run consistency checks
- **Perception-reasoning gap analysis**: Compare metadata-only vs. visual track performance
- **CLI tool**: `psai-bench` command with generate, score, baselines, evaluate, compare, and validate commands
- **103 tests** covering schema validation, generator determinism, scorer correctness, baseline sanity, CLI commands, and statistics

### First Results

- GPT-4o on UCF Crime Metadata Track: TDR=0.999, Accuracy=0.645, Aggregate=0.580
- SUSPICIOUS overuse (42.4%) penalizes aggregate score despite near-perfect threat detection
- Severity heuristic baseline (0.762 accuracy) outperforms GPT-4o on raw accuracy
