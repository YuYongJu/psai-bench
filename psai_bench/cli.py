"""PSAI-Bench command-line interface.

Usage:
    psai-bench generate --track metadata --source ucf --n 3000 --seed 42 --output data/generated/
    psai-bench generate --track visual --source ucf --n 3000 --seed 42 --output data/generated/
    psai-bench generate --track multi_sensor --n 1000 --seed 42 --output data/generated/
    psai-bench score --scenarios data/generated/ucf_metadata.json --outputs results/gpt4o_run1.json
    psai-bench baselines --scenarios data/generated/ucf_metadata.json --output results/baselines/
    psai-bench report --results results/ --output report.md
"""

import json
from pathlib import Path

import click
import numpy as np


@click.group()
def main():
    """PSAI-Bench: Physical Security AI Triage Benchmark."""
    pass


@main.command()
@click.option(
    "--track",
    type=click.Choice([
        "metadata", "visual", "multi_sensor",
        "visual_only", "visual_contradictory", "temporal",
    ]),
    required=True,
)
@click.option("--source", type=click.Choice(["ucf", "caltech", "all"]), default="all")
@click.option("--n", type=int, default=None, help="Number of scenarios (default: spec-defined)")
@click.option("--seed", type=int, default=42)
@click.option("--output", type=click.Path(), default="data/generated")
@click.option("--version", "gen_version", type=click.Choice(["v1", "v2"]), default="v1",
              help="Scenario generation version. v2 uses context-dependent GT (PSAI-Bench v2.0).")
def generate(track: str, source: str, n: int | None, seed: int, output: str, gen_version: str):
    """Generate evaluation scenarios."""
    from psai_bench.generators import MetadataGenerator, MultiSensorGenerator, VisualGenerator

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    if track == "metadata":
        gen = MetadataGenerator(seed=seed, version=gen_version)
        scenarios = []
        if source in ("ucf", "all"):
            count = n or 3000
            scenarios.extend(gen.generate_ucf_crime(count))
            click.echo(f"Generated {count} UCF Crime metadata scenarios")
        if source in ("caltech", "all"):
            count = n or 5000
            scenarios.extend(gen.generate_caltech(count))
            click.echo(f"Generated {count} Caltech metadata scenarios")

    elif track == "visual":
        gen = VisualGenerator(seed=seed, version=gen_version)
        scenarios = []
        if source in ("ucf", "all"):
            count = n or 3000
            scenarios.extend(gen.generate_ucf_crime(count))
            click.echo(f"Generated {count} UCF Crime visual scenarios")
        if source in ("caltech", "all"):
            count = n or 3000
            scenarios.extend(gen.generate_caltech(count))
            click.echo(f"Generated {count} Caltech visual scenarios")

    elif track == "multi_sensor":
        gen = MultiSensorGenerator(seed=seed, version=gen_version)
        count = n or 1000
        scenarios = gen.generate(count)
        click.echo(f"Generated {count} multi-sensor scenarios")

    elif track == "visual_only":
        from psai_bench.generators import VisualOnlyGenerator
        count = n or 500
        scenarios = VisualOnlyGenerator(seed=seed).generate(count)
        click.echo(f"Generated {count} visual-only scenarios")
    elif track == "visual_contradictory":
        from psai_bench.generators import ContradictoryGenerator
        count = n or 500
        scenarios = ContradictoryGenerator(seed=seed).generate(count)
        click.echo(f"Generated {count} visual-contradictory scenarios")
    elif track == "temporal":
        from psai_bench.generators import TemporalSequenceGenerator
        count = n or 50
        scenarios = TemporalSequenceGenerator(seed=seed).generate(count)
        click.echo(f"Generated {count} temporal sequences ({len(scenarios)} total alerts)")

    version_suffix = f"_{gen_version}" if gen_version != "v1" else ""
    out_file = out_dir / f"{track}_{source}_seed{seed}{version_suffix}.json"
    with open(out_file, "w") as f:
        json.dump(scenarios, f, indent=2)
    click.echo(f"Saved to {out_file}")

    # Print distribution summary
    from collections import Counter
    gt_dist = Counter(s["_meta"]["ground_truth"] for s in scenarios)
    diff_dist = Counter(s["_meta"]["difficulty"] for s in scenarios)
    click.echo(f"\nGround truth distribution: {dict(gt_dist)}")
    click.echo(f"Difficulty distribution: {dict(diff_dist)}")


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--outputs", type=click.Path(exists=True), required=True)
@click.option("--format", "fmt", type=click.Choice(["json", "table"]), default="table")
def score(scenarios: str, outputs: str, fmt: str):
    """Score system outputs against ground truth."""
    from psai_bench.scorer import score_run

    with open(scenarios) as f:
        scenario_data = json.load(f)
    with open(outputs) as f:
        output_data = json.load(f)

    report = score_run(scenario_data, output_data)

    if fmt == "json":
        click.echo(json.dumps(report.to_dict(), indent=2))
    else:
        from psai_bench.scorer import format_dashboard
        click.echo(format_dashboard(report))


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), default="results/baselines")
def baselines(scenarios: str, output: str):
    """Run all baseline systems and save results."""
    from psai_bench.baselines import (
        always_suspicious_baseline,
        majority_class_baseline,
        random_baseline,
        severity_heuristic_baseline,
    )
    from psai_bench.scorer import score_run

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(scenarios) as f:
        scenario_data = json.load(f)

    baseline_fns = {
        "random": random_baseline,
        "majority_class": majority_class_baseline,
        "always_suspicious": always_suspicious_baseline,
        "severity_heuristic": severity_heuristic_baseline,
    }

    results = {}
    for name, fn in baseline_fns.items():
        outputs = fn(scenario_data)
        report = score_run(scenario_data, outputs)
        results[name] = report.to_dict()

        out_file = out_dir / f"{name}_outputs.json"
        with open(out_file, "w") as f:
            json.dump(outputs, f, indent=2)

        from psai_bench.scorer import format_dashboard
        click.echo(f"\n{'='*60}")
        click.echo(f"  {name.upper()} BASELINE")
        click.echo(f"{'='*60}")
        click.echo(format_dashboard(report))

    # Save summary
    with open(out_dir / "baseline_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    click.echo(f"\nAll baseline results saved to {out_dir}/")


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
def validate_scenarios_cmd(scenarios: str):
    """Validate scenario quality and internal consistency."""
    from psai_bench.validation import validate_scenarios

    with open(scenarios) as f:
        scenario_data = json.load(f)

    report = validate_scenarios(scenario_data)
    click.echo(report.summary())

    # Also show distribution stats
    from collections import Counter
    n = len(scenario_data)
    diff = Counter(s["_meta"]["difficulty"] for s in scenario_data)
    gt = Counter(s["_meta"]["ground_truth"] for s in scenario_data)
    click.echo(f"\nN={n}")
    click.echo(f"Difficulty: {', '.join(f'{k}={v} ({v/n:.1%})' for k, v in sorted(diff.items()))}")
    click.echo(f"Ground truth: {', '.join(f'{k}={v} ({v/n:.1%})' for k, v in sorted(gt.items()))}")


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--outputs", type=click.Path(exists=True), required=True)
def validate_submission_cmd(scenarios: str, outputs: str):
    """Validate a system submission for completeness and correctness."""
    from psai_bench.validation import validate_submission

    with open(scenarios) as f:
        scenario_data = json.load(f)
    with open(outputs) as f:
        output_data = json.load(f)

    report = validate_submission(scenario_data, output_data)
    click.echo(report.summary())


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--outputs-a", type=click.Path(exists=True), required=True, help="System A outputs")
@click.option("--outputs-b", type=click.Path(exists=True), required=True, help="System B outputs")
def compare(scenarios: str, outputs_a: str, outputs_b: str):
    """Compare two systems with McNemar's test and confidence intervals."""
    from psai_bench.statistics import compute_all_cis, mcnemar_test

    with open(scenarios) as f:
        scenario_data = json.load(f)
    with open(outputs_a) as f:
        data_a = json.load(f)
    with open(outputs_b) as f:
        data_b = json.load(f)

    # McNemar's test
    gt = np.array([s["_meta"]["ground_truth"] for s in scenario_data])
    map_a = {o["alert_id"]: o["verdict"] for o in data_a}
    map_b = {o["alert_id"]: o["verdict"] for o in data_b}
    pred_a = np.array([map_a.get(s["alert_id"], "MISSING") for s in scenario_data])
    pred_b = np.array([map_b.get(s["alert_id"], "MISSING") for s in scenario_data])

    result = mcnemar_test(gt, pred_a, pred_b)
    click.echo("=== McNemar's Test ===")
    click.echo(f"Chi2: {result['chi2']:.4f}")
    click.echo(f"p-value: {result['p_value']:.6f}")
    click.echo(f"Significant (p < 0.01): {result['significant']}")
    click.echo(f"Better system: {result['better_system']}")
    click.echo(f"A only correct: {result['a_only_correct']}, B only correct: {result['b_only_correct']}")

    # Confidence intervals for each
    click.echo("\n=== System A - 95% Confidence Intervals ===")
    cis_a = compute_all_cis(scenario_data, data_a)
    for metric, (point, lo, hi) in cis_a.items():
        click.echo(f"  {metric}: {point:.4f} [{lo:.4f}, {hi:.4f}]")

    click.echo("\n=== System B - 95% Confidence Intervals ===")
    cis_b = compute_all_cis(scenario_data, data_b)
    for metric, (point, lo, hi) in cis_b.items():
        click.echo(f"  {metric}: {point:.4f} [{lo:.4f}, {hi:.4f}]")


@main.command()
@click.option("--output-dir", type=click.Path(), default="data/raw/ucf_crime")
@click.option("--sample/--full", default=True,
              help="--sample: 5 videos (~114MB). --full: all 290 test videos (~28GB).")
def download_ucf(output_dir: str, sample: bool):
    """Download UCF Crime test videos from HuggingFace."""
    from psai_bench.downloader import download_full, download_sample

    if sample:
        paths = download_sample(output_dir)
    else:
        paths = download_full(output_dir)
    click.echo(f"\nDone. {len(paths)} videos available in {output_dir}.")


@main.command()
@click.option("--video-dir", type=click.Path(), default=None,
              help="Local dir with UCF Crime videos. If omitted, URIs reference HuggingFace.")
@click.option("--seed", type=int, default=42)
@click.option("--variants", type=int, default=10,
              help="Contextual variants per video. 290 videos x 10 = 2,900 scenarios.")
@click.option("--output", type=click.Path(), default="data/generated")
def generate_visual(video_dir: str | None, seed: int, variants: int, output: str):
    """Generate Visual Track scenarios mapped to real UCF Crime test videos."""
    from huggingface_hub import hf_hub_download

    from psai_bench.video_mapper import (
        VisualTrackMapper,
        parse_temporal_annotations,
        parse_test_split,
    )

    # Download annotation files (tiny, cached)
    ann_path = hf_hub_download(
        "jinmang2/ucf_crime",
        "UCF_Crimes-Train-Test-Split/Temporal_Anomaly_Annotation_for_Testing_Videos.txt",
        repo_type="dataset",
    )
    test_path = hf_hub_download(
        "jinmang2/ucf_crime",
        "UCF_Crimes-Train-Test-Split/Anomaly_Detection_splits/Anomaly_Test.txt",
        repo_type="dataset",
    )

    annotations = parse_temporal_annotations(ann_path)
    test_videos = parse_test_split(test_path)

    click.echo(f"Parsed {len(annotations)} annotations, {len(test_videos)} test videos")

    mapper = VisualTrackMapper(seed=seed)
    scenarios = mapper.generate_from_annotations(
        test_videos, annotations, video_dir, variants_per_video=variants
    )

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"visual_ucf_real_seed{seed}.json"

    with open(out_file, "w") as f:
        json.dump(scenarios, f, indent=2)

    click.echo(f"Generated {len(scenarios)} Visual Track scenarios")
    click.echo(f"Saved to {out_file}")

    from collections import Counter
    gt_dist = Counter(s["_meta"]["ground_truth"] for s in scenarios)
    diff_dist = Counter(s["_meta"]["difficulty"] for s in scenarios)
    has_segments = sum(1 for s in scenarios if s["_meta"]["anomaly_segments"])
    click.echo(f"\nGround truth: {dict(gt_dist)}")
    click.echo(f"Difficulty: {dict(diff_dist)}")
    click.echo(f"Videos with anomaly annotations: {has_segments}/{len(scenarios)}")


@main.command()
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--model", type=click.Choice(["claude-sonnet", "gpt-4o", "gemini-flash", "all"]),
              required=True)
@click.option("--n", type=int, default=None, help="Limit scenarios (for cost control)")
@click.option("--delay", type=float, default=0.1, help="Seconds between API calls")
@click.option("--output", type=click.Path(), default="results/evaluations")
@click.option("--run-id", type=int, default=1, help="Run number (1-5 for multi-run)")
def evaluate(scenarios: str, model: str, n: int | None, delay: float, output: str, run_id: int):
    """Run a frontier model on PSAI-Bench scenarios.

    Requires API keys set as environment variables:
      ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY

    Cost estimates for full Metadata Track (8000 scenarios):
      Claude Sonnet: ~$15-25
      GPT-4o: ~$10-20
      Gemini Flash: ~$0.50-1
    """
    from psai_bench.evaluators import EVALUATORS
    from psai_bench.scorer import score_run

    with open(scenarios) as f:
        scenario_data = json.load(f)

    if n:
        scenario_data = scenario_data[:n]
        click.echo(f"Limited to first {n} scenarios (cost control)")

    models_to_run = list(EVALUATORS.keys()) if model == "all" else [model]
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for model_name in models_to_run:
        click.echo(f"\n{'='*60}")
        click.echo(f"  Evaluating: {model_name} (run {run_id})")
        click.echo(f"  Scenarios: {len(scenario_data)}")
        click.echo(f"{'='*60}\n")

        try:
            evaluator_cls = EVALUATORS[model_name]
            evaluator = evaluator_cls()
        except ValueError as e:
            click.echo(f"  SKIPPED: {e}")
            continue

        outputs = evaluator.evaluate_batch(scenario_data, delay_seconds=delay)

        # Save outputs
        out_file = out_dir / f"{model_name}_run{run_id}.json"
        with open(out_file, "w") as f:
            json.dump(outputs, f, indent=2)
        click.echo(f"\n  Outputs saved to {out_file}")

        # Score immediately
        report = score_run(scenario_data, outputs)
        click.echo("\n  --- Quick Score ---")
        click.echo(f"  Accuracy: {report.accuracy:.4f}")
        click.echo(f"  TDR: {report.tdr:.4f}")
        click.echo(f"  FASR: {report.fasr:.4f}")
        click.echo(f"  Safety Score (3:1): {report.safety_score_3_1:.4f}")
        click.echo(f"  ECE: {report.ece:.4f}")
        click.echo(f"  Aggregate: {report.aggregate_score:.4f}")
        click.echo(f"  SUSPICIOUS%: {report.suspicious_fraction:.1%}")

        # Parse errors/API errors
        parse_errors = sum(1 for o in outputs if o.get("_parse_error"))
        api_errors = sum(1 for o in outputs if o.get("_api_error"))
        if parse_errors or api_errors:
            click.echo(f"  Parse errors: {parse_errors}, API errors: {api_errors}")


@main.command()
@click.option("--results-dir", type=click.Path(exists=True), default="results/evaluations")
@click.option("--scenarios", type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), default="results/perception_gap_analysis.json")
def analyze_gap(results_dir: str, scenarios: str, output: str):
    """Analyze the perception-reasoning gap across models.

    Compares Metadata Track vs Visual Track scores for each model
    to quantify how much video actually contributes to triage accuracy.
    This is the core novel contribution of the PSAI-Bench paper.
    """
    from psai_bench.scorer import score_run

    results_path = Path(results_dir)
    with open(scenarios) as f:
        scenario_data = json.load(f)

    # Find all result files grouped by model
    result_files = sorted(results_path.glob("*.json"))
    models = {}
    for f in result_files:
        # Parse filename: model_run1.json
        parts = f.stem.rsplit("_run", 1)
        if len(parts) == 2:
            model_name = parts[0]
            if model_name not in models:
                models[model_name] = []
            models[model_name].append(f)

    if not models:
        click.echo("No evaluation results found.")
        return

    analysis = {}
    for model_name, files in sorted(models.items()):
        click.echo(f"\n=== {model_name} ({len(files)} runs) ===")
        for f in files:
            with open(f) as fh:
                outputs = json.load(fh)
            report = score_run(scenario_data, outputs)
            track = scenario_data[0].get("track", "unknown") if scenario_data else "unknown"

            key = f"{model_name}_{track}"
            analysis[key] = {
                "model": model_name,
                "track": track,
                "accuracy": report.accuracy,
                "tdr": report.tdr,
                "fasr": report.fasr,
                "safety_score_3_1": report.safety_score_3_1,
                "ece": report.ece,
                "aggregate": report.aggregate_score,
                "suspicious_fraction": report.suspicious_fraction,
                "accuracy_easy": report.accuracy_easy,
                "accuracy_medium": report.accuracy_medium,
                "accuracy_hard": report.accuracy_hard,
            }
            click.echo(
                f"  {f.name}: Acc={report.accuracy:.3f} "
                f"TDR={report.tdr:.3f} SS={report.safety_score_3_1:.3f} "
                f"Agg={report.aggregate_score:.3f}"
            )

    # Compute perception-reasoning gaps if both tracks exist
    click.echo(f"\n{'='*60}")
    click.echo("  PERCEPTION-REASONING GAP ANALYSIS")
    click.echo(f"{'='*60}")

    gap_found = False
    for model_name in set(k.rsplit("_", 1)[0] for k in analysis):
        meta_key = f"{model_name}_metadata"
        visual_key = f"{model_name}_visual"
        if meta_key in analysis and visual_key in analysis:
            gap_found = True
            meta = analysis[meta_key]
            visual = analysis[visual_key]
            gap = visual["accuracy"] - meta["accuracy"]
            ss_gap = visual["safety_score_3_1"] - meta["safety_score_3_1"]
            click.echo(f"\n  {model_name}:")
            click.echo(f"    Metadata accuracy: {meta['accuracy']:.3f}")
            click.echo(f"    Visual accuracy:   {visual['accuracy']:.3f}")
            click.echo(f"    Gap (visual - meta): {gap:+.3f}")
            click.echo(f"    Safety Score gap:    {ss_gap:+.3f}")
            if abs(gap) < 0.02:
                click.echo("    >> Video adds negligible value for this model")
            elif gap > 0:
                click.echo(f"    >> Video improves triage by {gap:.1%}")
            else:
                click.echo(f"    >> Video HURTS triage by {abs(gap):.1%} (model confused by visual)")

    if not gap_found:
        click.echo("\n  No model has results on both tracks yet.")
        click.echo("  Run evaluations on both metadata and visual scenarios first.")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(analysis, f, indent=2)
    click.echo(f"\nAnalysis saved to {out_path}")


if __name__ == "__main__":
    main()
