"""Unit contracts for the M4 equal-step token engineering harness."""

from __future__ import annotations

import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

_SCRIPT = Path(__file__).parents[4] / "scripts" / "l2_token_regression.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("l2_token_regression", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def regression():
    return _load_module()


def _write_brain_template(path: Path, *, architecture: str, aggregator: str) -> None:
    architecture_key = "token_set" if architecture == "token_set" else "recurrent"
    heads = "      num_heads: 4\n" if aggregator == "attention" else ""
    path.write_text(
        "version: '1.0'\n"
        "description: test template\n"
        "architecture:\n"
        f"  type: {architecture}\n"
        f"  {architecture_key}:\n"
        "    token_embed_dim: 16\n"
        "    q_head_hidden_dim: 64\n"
        "    aggregator:\n"
        f"      type: {aggregator}\n"
        f"{heads}"
        "optimizer:\n"
        "  type: adam\n"
    )


class TestFrozenContract:
    def test_exact_per_seed_budgets_and_raw_threshold(self, regression):
        assert regression.BASELINE_ENV_STEP_BUDGETS == {
            42: 3_322_056,
            43: 3_112_832,
            44: 3_314_536,
            45: 2_278_640,
            46: 2_286_816,
        }
        assert regression.BASELINE_SEED_MEANS == {
            42: 98.9975,
            43: 98.9975,
            44: 98.985,
            45: 98.83,
            46: 99.91125,
        }
        assert regression.BASELINE_IQM == 98.99333333333334
        assert regression.ACCEPTANCE_THRESHOLD == 79.19466666666668
        assert regression.REPRESENTATIVE_SEED == 45
        assert regression.SEEDS == (45,)

    @pytest.mark.parametrize(
        ("label", "dto_type"),
        [("token_feedforward", "token_set"), ("token_recurrent", "recurrent")],
    )
    @pytest.mark.parametrize("aggregator", ["mean", "attention"])
    def test_template_must_match_declared_cell(self, regression, tmp_path, label, dto_type, aggregator):
        template = tmp_path / "brain.yaml"
        _write_brain_template(template, architecture=dto_type, aggregator=aggregator)

        data = regression.validate_brain_template(template, architecture=label, aggregator=aggregator)

        assert data["architecture"]["type"] == dto_type

    def test_template_mismatch_refuses(self, regression, tmp_path):
        template = tmp_path / "brain.yaml"
        _write_brain_template(template, architecture="token_set", aggregator="mean")

        with pytest.raises(ValueError, match="token_recurrent.*recurrent"):
            regression.validate_brain_template(template, architecture="token_recurrent", aggregator="mean")
        with pytest.raises(ValueError, match="aggregator"):
            regression.validate_brain_template(template, architecture="token_feedforward", aggregator="attention")


def _write_cell_result(
    root: Path,
    *,
    architecture: str,
    aggregator: str,
    seed: int,
    mean: float,
    budget_shortfall: int = 0,
) -> None:
    run_dir = root / f"{architecture}-{aggregator}" / f"seed_{seed}"
    run_dir.mkdir(parents=True)
    (run_dir / "meta.json").write_text(
        json.dumps(
            {
                "architecture": architecture,
                "aggregator": aggregator,
                "seed": seed,
                "requested_live_agent_steps": {42: 3_322_056, 43: 3_112_832, 44: 3_314_536, 45: 2_278_640, 46: 2_286_816}[seed],
                "realized_live_agent_steps": (
                    {42: 3_322_056, 43: 3_112_832, 44: 3_314_536, 45: 2_278_640, 46: 2_286_816}[seed] - budget_shortfall
                ),
                "budget_exact": budget_shortfall == 0,
                "budget_stop_rule": "stop_before_vector_step",
                "git_sha": "git-sha",
                "src_tree": "src-tree",
                "harness_blob": "harness-blob",
                "brain_templates_tree": "templates-tree",
                "brain_template_sha256": f"template-{architecture}-{aggregator}",
                "parameter_count": 1_000 + (100 if architecture == "token_recurrent" else 0) + (10 if aggregator == "attention" else 0),
                "compiled_brain_hash": f"brain-{architecture}-{aggregator}",
                "compiled_pack_brain_hash": "pack-brain",
                "compiled_token_type_schema_hash": "token-schema",
                "compiled_token_layout_hash": "token-layout",
                "compiled_observation_schema_hash": "observation-schema",
            }
        )
    )
    total_survival_steps = round(mean * 800)
    base, remainder = divmod(total_survival_steps, 800)
    survival_steps = [base + (1 if index < remainder else 0) for index in range(800)]
    (run_dir / "greedy_eval.json").write_text(
        json.dumps(
            {
                "train_seed": seed,
                "eval_seed": 12345,
                "eval_episodes": 100,
                "num_agents": 8,
                "episode_cap": 1000,
                "mean_survival": mean,
                "episodes": [
                    {"episode": episode, "survival_steps": survival_steps[episode * 8 : (episode + 1) * 8]} for episode in range(100)
                ],
            }
        )
    )


class TestSummary:
    def test_four_cells_representative_seed_and_raw_score(self, regression, tmp_path):
        for architecture in regression.ARCHITECTURES:
            for aggregator in regression.AGGREGATORS:
                _write_cell_result(
                    tmp_path,
                    architecture=architecture,
                    aggregator=aggregator,
                    seed=regression.REPRESENTATIVE_SEED,
                    mean=regression.BASELINE_SEED_MEANS[regression.REPRESENTATIVE_SEED],
                )

        summary = regression.summarize_results(tmp_path)

        assert summary["acceptance_threshold"] == regression.ACCEPTANCE_THRESHOLD
        assert summary["representative_seed"] == 45
        assert summary["all_cells_passed"] is True
        assert len(summary["cells"]) == 4
        for cell in summary["cells"]:
            assert cell["greedy_mean_survival"] == regression.BASELINE_SEED_MEANS[45]
            assert cell["budget_exact"] is True
            assert cell["budget_compliant"] is True
            assert cell["passed"] is True
            assert [row["seed"] for row in cell["seeds"]] == [45]
            assert cell["model_identity"]["parameter_count"] >= 1_000
        assert summary["cohort_identity"] == {
            "git_sha": "git-sha",
            "src_tree": "src-tree",
            "harness_blob": "harness-blob",
            "brain_templates_tree": "templates-tree",
            "compiled_pack_brain_hash": "pack-brain",
            "compiled_token_type_schema_hash": "token-schema",
            "compiled_token_layout_hash": "token-layout",
            "compiled_observation_schema_hash": "observation-schema",
        }

    def test_sub_vector_shortfall_is_compliant_and_recorded(self, regression, tmp_path):
        for architecture in regression.ARCHITECTURES:
            for aggregator in regression.AGGREGATORS:
                _write_cell_result(
                    tmp_path,
                    architecture=architecture,
                    aggregator=aggregator,
                    seed=regression.REPRESENTATIVE_SEED,
                    mean=regression.BASELINE_SEED_MEANS[regression.REPRESENTATIVE_SEED],
                    budget_shortfall=(1 if architecture == "token_recurrent" and aggregator == "attention" else 0),
                )

        summary = regression.summarize_results(tmp_path)

        failing = next(cell for cell in summary["cells"] if cell["architecture"] == "token_recurrent" and cell["aggregator"] == "attention")
        assert failing["budget_exact"] is False
        assert failing["budget_compliant"] is True
        assert failing["score_passed"] is True
        assert failing["passed"] is True
        assert summary["all_cells_passed"] is True

    def test_oversized_shortfall_fails_cell(self, regression, tmp_path):
        for architecture in regression.ARCHITECTURES:
            for aggregator in regression.AGGREGATORS:
                _write_cell_result(
                    tmp_path,
                    architecture=architecture,
                    aggregator=aggregator,
                    seed=regression.REPRESENTATIVE_SEED,
                    mean=regression.BASELINE_SEED_MEANS[regression.REPRESENTATIVE_SEED],
                    budget_shortfall=(8 if architecture == "token_recurrent" and aggregator == "attention" else 0),
                )

        summary = regression.summarize_results(tmp_path)

        failing = next(cell for cell in summary["cells"] if cell["architecture"] == "token_recurrent" and cell["aggregator"] == "attention")
        assert failing["budget_compliant"] is False
        assert failing["passed"] is False
        assert summary["all_cells_passed"] is False

    def test_raw_score_below_threshold_fails_cell(self, regression, tmp_path):
        for architecture in regression.ARCHITECTURES:
            for aggregator in regression.AGGREGATORS:
                _write_cell_result(
                    tmp_path,
                    architecture=architecture,
                    aggregator=aggregator,
                    seed=regression.REPRESENTATIVE_SEED,
                    mean=(
                        10.0
                        if architecture == "token_recurrent" and aggregator == "attention"
                        else regression.BASELINE_SEED_MEANS[regression.REPRESENTATIVE_SEED]
                    ),
                )

        summary = regression.summarize_results(tmp_path)

        failing = next(cell for cell in summary["cells"] if cell["architecture"] == "token_recurrent" and cell["aggregator"] == "attention")
        assert failing["score_passed"] is False
        assert failing["passed"] is False
        assert summary["all_cells_passed"] is False

    def test_missing_cell_artifact_refuses(self, regression, tmp_path):
        with pytest.raises(FileNotFoundError, match="token_feedforward-mean.*seed_45"):
            regression.summarize_results(tmp_path)

    def test_cross_cell_cohort_identity_drift_refuses(self, regression, tmp_path):
        for architecture in regression.ARCHITECTURES:
            for aggregator in regression.AGGREGATORS:
                _write_cell_result(
                    tmp_path,
                    architecture=architecture,
                    aggregator=aggregator,
                    seed=regression.REPRESENTATIVE_SEED,
                    mean=regression.BASELINE_SEED_MEANS[regression.REPRESENTATIVE_SEED],
                )
        meta_path = tmp_path / "token_feedforward-mean" / "seed_45" / "meta.json"
        metadata = json.loads(meta_path.read_text())
        metadata["src_tree"] = "different-src-tree"
        meta_path.write_text(json.dumps(metadata))

        with pytest.raises(ValueError, match="src_tree differs across the M4 cohort"):
            regression.summarize_results(tmp_path)


class TestDirtySourceGuard:
    def test_dirty_acceptance_input_refuses_and_scans_all_protocol_paths(self, regression, monkeypatch):
        calls: list[tuple[str, ...]] = []

        def fake_git(*args):
            calls.append(args)
            return " M scripts/l2_token_regression.py"

        monkeypatch.setattr(regression, "_git", fake_git)
        with pytest.raises(SystemExit, match="acceptance inputs are dirty"):
            regression.require_clean_acceptance_inputs()

        assert calls == [
            (
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                "src/townlet",
                "scripts/l2_token_regression.py",
                "configs/benchmarks/l2_token_regression",
            )
        ]

    def test_clean_identity_binds_engine_harness_and_templates(self, regression, monkeypatch):
        responses = iter(["", "head-sha", "src-tree", "harness-blob", "templates-tree"])
        monkeypatch.setattr(regression, "_git", lambda *args: next(responses))

        assert regression.require_clean_acceptance_inputs() == {
            "git_sha": "head-sha",
            "src_tree": "src-tree",
            "harness_blob": "harness-blob",
            "brain_templates_tree": "templates-tree",
        }


class TestRuntimeIdentity:
    def test_runtime_metadata_captures_model_and_compiled_token_identity(self, regression):
        network = SimpleNamespace(parameters=lambda: iter([SimpleNamespace(numel=lambda: 7), SimpleNamespace(numel=lambda: 11)]))
        runner = SimpleNamespace(
            population=SimpleNamespace(q_network=network),
            compiled=SimpleNamespace(brain_hash="brain", pack_brain_hash="pack-brain"),
            level_name=regression.LEVEL,
        )
        runner.compiled.get_level = lambda _level: SimpleNamespace(
            token_type_schema_hash="token-schema",
            layout_hash="token-layout",
            observation_schema_hash="observation-schema",
        )

        assert regression.runtime_model_metadata(runner) == {
            "parameter_count": 18,
            "compiled_brain_hash": "brain",
            "compiled_pack_brain_hash": "pack-brain",
            "compiled_token_type_schema_hash": "token-schema",
            "compiled_token_layout_hash": "token-layout",
            "compiled_observation_schema_hash": "observation-schema",
        }


class TestInvocationTiming:
    def test_normalized_command_and_resumed_timing_preserve_original_start(self, regression, tmp_path):
        args = Namespace(
            architecture="token_recurrent",
            aggregator="attention",
            brain_template=str(tmp_path / "brain.yaml"),
            seed=45,
            env_step_budget=regression.BASELINE_ENV_STEP_BUDGETS[45],
            run_root=str(tmp_path / "runs"),
            resume=True,
        )
        metadata: dict[str, object] = {}

        expected_command = [
            "uv",
            "run",
            "python",
            str(regression.REPO_ROOT / "scripts" / "l2_token_regression.py"),
            "train",
            "--architecture",
            "token_recurrent",
            "--aggregator",
            "attention",
            "--brain-template",
            str((tmp_path / "brain.yaml").resolve()),
            "--seed",
            "45",
            "--env-step-budget",
            str(regression.BASELINE_ENV_STEP_BUDGETS[45]),
            "--run-root",
            str((tmp_path / "runs").resolve()),
            "--resume",
        ]
        first = regression.begin_training_attempt(metadata, args, argv=["first"], started_at="2026-08-31T01:00:00+00:00")
        regression.finish_training_attempt(
            metadata,
            first,
            finished_at="2026-08-31T02:00:00+00:00",
            duration_seconds=3600.0,
            completed=False,
        )
        second = regression.begin_training_attempt(metadata, args, argv=["second"], started_at="2026-08-31T03:00:00+00:00")
        regression.finish_training_attempt(
            metadata,
            second,
            finished_at="2026-08-31T05:00:00+00:00",
            duration_seconds=7200.0,
            completed=True,
        )

        assert metadata["training_started_at"] == "2026-08-31T01:00:00+00:00"
        assert metadata["training_finished_at"] == "2026-08-31T05:00:00+00:00"
        assert metadata["duration_seconds"] == 10_800.0
        assert metadata["normalized_train_command"] == expected_command
        assert metadata["train_argv"] == ["second"]
        assert metadata["training_attempts"] == [
            {
                "started_at": "2026-08-31T01:00:00+00:00",
                "finished_at": "2026-08-31T02:00:00+00:00",
                "duration_seconds": 3600.0,
                "resume": True,
                "argv": ["first"],
                "normalized_command": expected_command,
            },
            {
                "started_at": "2026-08-31T03:00:00+00:00",
                "finished_at": "2026-08-31T05:00:00+00:00",
                "duration_seconds": 7200.0,
                "resume": True,
                "argv": ["second"],
                "normalized_command": expected_command,
            },
        ]

    @pytest.mark.parametrize("realized", [0, 2_278_632, 2_278_641])
    def test_eval_refuses_partial_large_shortfall_or_overshoot(self, regression, realized):
        metadata = {
            "requested_live_agent_steps": regression.BASELINE_ENV_STEP_BUDGETS[45],
            "realized_live_agent_steps": realized,
        }

        with pytest.raises(SystemExit, match="resume training first"):
            regression.require_budget_complete_for_eval(metadata, Path("run"))

    def test_eval_accepts_conservative_sub_vector_shortfall(self, regression):
        requested = regression.BASELINE_ENV_STEP_BUDGETS[45]
        regression.require_budget_complete_for_eval(
            {"requested_live_agent_steps": requested, "realized_live_agent_steps": requested - 7},
            Path("run"),
        )


class TestResume:
    def _metadata(self, regression, template: Path) -> dict[str, object]:
        return {
            "format": "l2-token-regression-1",
            "architecture": "token_feedforward",
            "aggregator": "mean",
            "seed": 45,
            "level": regression.LEVEL,
            "requested_live_agent_steps": regression.BASELINE_ENV_STEP_BUDGETS[45],
            "budget_stop_rule": regression.BUDGET_STOP_RULE,
            "git_sha": "head-sha",
            "src_tree": "src-tree",
            "harness_blob": "harness-blob",
            "brain_templates_tree": "templates-tree",
            "brain_template": str(template.resolve()),
            "brain_template_sha256": regression.hashlib.sha256(template.read_bytes()).hexdigest(),
        }

    def test_resume_accepts_only_matching_unfinished_run(self, regression, tmp_path):
        template = tmp_path / "template.yaml"
        template.write_text("template")
        run_dir = tmp_path / "run"
        (run_dir / "pack").mkdir(parents=True)
        (run_dir / "checkpoints").mkdir()
        (run_dir / "checkpoints" / "checkpoint_ep00001.pt").write_bytes(b"checkpoint")
        metadata = self._metadata(regression, template)
        (run_dir / "meta.json").write_text(json.dumps(metadata))

        resumed = regression.validate_resume_run(
            run_dir,
            identity={
                "git_sha": "head-sha",
                "src_tree": "src-tree",
                "harness_blob": "harness-blob",
                "brain_templates_tree": "templates-tree",
            },
            brain_template=template,
            architecture="token_feedforward",
            aggregator="mean",
            seed=45,
            budget=regression.BASELINE_ENV_STEP_BUDGETS[45],
        )

        assert resumed == metadata

    @pytest.mark.parametrize(
        ("mutation", "message"),
        [
            ({"harness_blob": "other-harness"}, "harness_blob"),
            ({"architecture": "token_recurrent"}, "architecture"),
            ({"requested_live_agent_steps": 1}, "requested_live_agent_steps"),
            ({"brain_template_sha256": "wrong"}, "brain_template_sha256"),
        ],
    )
    def test_resume_refuses_identity_cell_budget_or_template_mismatch(self, regression, tmp_path, mutation, message):
        template = tmp_path / "template.yaml"
        template.write_text("template")
        run_dir = tmp_path / "run"
        (run_dir / "pack").mkdir(parents=True)
        (run_dir / "checkpoints").mkdir()
        (run_dir / "checkpoints" / "checkpoint_ep00001.pt").write_bytes(b"checkpoint")
        metadata = self._metadata(regression, template)
        metadata.update(mutation)
        (run_dir / "meta.json").write_text(json.dumps(metadata))

        with pytest.raises(ValueError, match=message):
            regression.validate_resume_run(
                run_dir,
                identity={
                    "git_sha": "head-sha",
                    "src_tree": "src-tree",
                    "harness_blob": "harness-blob",
                    "brain_templates_tree": "templates-tree",
                },
                brain_template=template,
                architecture="token_feedforward",
                aggregator="mean",
                seed=45,
                budget=regression.BASELINE_ENV_STEP_BUDGETS[45],
            )

    def test_resume_refuses_evaluated_or_checkpointless_run(self, regression, tmp_path):
        template = tmp_path / "template.yaml"
        template.write_text("template")
        run_dir = tmp_path / "run"
        (run_dir / "pack").mkdir(parents=True)
        (run_dir / "checkpoints").mkdir()
        metadata = self._metadata(regression, template)
        (run_dir / "meta.json").write_text(json.dumps(metadata))
        kwargs = {
            "identity": {
                "git_sha": "head-sha",
                "src_tree": "src-tree",
                "harness_blob": "harness-blob",
                "brain_templates_tree": "templates-tree",
            },
            "brain_template": template,
            "architecture": "token_feedforward",
            "aggregator": "mean",
            "seed": 45,
            "budget": regression.BASELINE_ENV_STEP_BUDGETS[45],
        }

        with pytest.raises(FileNotFoundError, match="checkpoint"):
            regression.validate_resume_run(run_dir, **kwargs)

        (run_dir / "checkpoints" / "checkpoint_ep00001.pt").write_bytes(b"checkpoint")
        (run_dir / "greedy_eval.json").write_text("{}")
        with pytest.raises(ValueError, match="greedy_eval"):
            regression.validate_resume_run(run_dir, **kwargs)
