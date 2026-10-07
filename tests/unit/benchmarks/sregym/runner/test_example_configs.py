"""The checked-in example experiment configs stay loadable, portable and policy-compliant."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from benchmarks.sregym.runner.experiment import ExperimentConfig, load_experiment_config
from benchmarks.sregym.runner.pipeline import load_pipeline_config, merge_stage_config

EXPERIMENTS = Path(__file__).resolve().parents[5] / "benchmarks" / "sregym" / "experiments"
EXAMPLES = ("default.toml", "example_pipeline.toml", "sdo_example.toml", "codex_baseline_example.toml")
MACHINE_SPECIFIC = re.compile(r"/mnt/|/home/|/Users/|\.internal\b|\.cs\.[a-z]+\.edu")


def _resolved(path: Path) -> list[ExperimentConfig]:
    if "[pipeline]" in path.read_text(encoding="utf-8"):
        pipeline = load_pipeline_config(path)
        return [merge_stage_config(pipeline.defaults, stage.runner_overrides) for stage in pipeline.stages]
    return [load_experiment_config(path)]


def test_the_examples_directory_holds_exactly_the_documented_examples() -> None:
    assert sorted(path.name for path in EXPERIMENTS.glob("*.toml")) == sorted(EXAMPLES)


@pytest.mark.parametrize("name", EXAMPLES)
def test_each_example_parses_and_uses_the_codex_luna_judge(name: str) -> None:
    configs = _resolved(EXPERIMENTS / name)

    assert configs
    assert all(config.env.judge_model_id == "codex-gpt-6-luna" for config in configs)


@pytest.mark.parametrize("name", EXAMPLES)
def test_each_example_is_free_of_machine_specific_paths_and_hosts(name: str) -> None:
    text = (EXPERIMENTS / name).read_text(encoding="utf-8")

    assert MACHINE_SPECIFIC.search(text) is None


def test_the_sdo_and_codex_examples_are_a_comparable_luna_pair() -> None:
    sdo = _resolved(EXPERIMENTS / "sdo_example.toml")
    codex = _resolved(EXPERIMENTS / "codex_baseline_example.toml")

    assert {config.agent for config in sdo} == {"sdo_codex"}
    assert {config.agent for config in codex} == {"codex"}
    assert {config.model for config in sdo + codex} == {"gpt-6-luna"}
    assert {config.reasoning_effort for config in sdo + codex} == {"medium"}
    assert [
        stage.chain_application_workspace for stage in load_pipeline_config(EXPERIMENTS / "sdo_example.toml").stages
    ] == [
        False,
        True,
    ]
