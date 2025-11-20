"""Affordance mechanics tests (v2.1-native).

These tests avoid legacy config layouts by building minimal packs via the
shared config builder and mutating only the v2.1 YAMLs we care about.
Coverage focuses on:
- Opening hours (nested opening_hours schedule)
- Affordability processing (costs vs meters)
- Instant effects application on meters
- Multi-tick/dual semantics vs instant mode equivalence
"""

from __future__ import annotations

import pytest
import torch

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml


def _set_global_vision(config_dir):
    mutate_curriculum_yaml(config_dir, lambda c: c["curriculum"].update({"active_vision": "global", "vision_range": 0.0}))


def _mutate_affordances(config_dir, mutator):
    import yaml

    level_dir = config_dir / "levels" / "L0_test"
    aff_path = level_dir / "affordances.yaml"
    data = yaml.safe_load(aff_path.read_text())
    aff_list = data["affordances"]["affordances"] if isinstance(data["affordances"], dict) else data["affordances"]
    for aff in aff_list:
        mutator(aff)
    if isinstance(data["affordances"], dict):
        data["affordances"]["affordances"] = aff_list
    else:
        data["affordances"] = aff_list
    aff_path.write_text(yaml.safe_dump(data, sort_keys=False))


def _zero_bar_depletions(config_dir):
    import yaml

    level_dir = config_dir / "levels" / "L0_test"
    bars_path = level_dir / "bars.yaml"
    data = yaml.safe_load(bars_path.read_text())
    bars_section = data.get("bars", {})
    meters = bars_section.get("meters") if isinstance(bars_section, dict) else data.get("meters") or bars_section
    meters = meters or []
    for bar in meters:
        dep = bar.get("depletion", {})
        for key in ("passive", "move", "interact"):
            if key in dep:
                dep[key] = 0.0
        bar["depletion"] = dep
    if isinstance(bars_section, dict) and "meters" in bars_section:
        bars_section["meters"] = meters
        data["bars"] = bars_section
    else:
        data["meters"] = meters
    bars_path.write_text(yaml.safe_dump(data, sort_keys=False))


class TestOpeningHours:
    def test_work_and_entertainment_hours(self, config_pack_factory, cpu_env_factory):
        config_dir = config_pack_factory(name="hours")

        _set_global_vision(config_dir)

        # Enable wraparound hours on ENTERTAINMENT and ensure WORK stays 9-17
        def set_hours(aff):
            opening = aff.get("opening_hours", {})
            if aff["name"] == "ENTERTAINMENT":
                opening = {"enabled": True, "schedule": [{"start": 18, "end": 28}]}
            elif aff["name"] == "WORK":
                opening = {"enabled": True, "schedule": [{"start": 9, "end": 17}]}
            aff["opening_hours"] = opening

        _mutate_affordances(config_dir, set_hours)

        env = cpu_env_factory(config_dir=config_dir, level_name="L0_test", num_agents=1)
        engine = env.affordance_engine

        assert not engine.is_affordance_open("WORK", 6)
        assert engine.is_affordance_open("WORK", 9)
        assert engine.is_affordance_open("WORK", 12)
        assert not engine.is_affordance_open("WORK", 18)

        assert not engine.is_affordance_open("ENTERTAINMENT", 16)
        assert engine.is_affordance_open("ENTERTAINMENT", 23)
        assert engine.is_affordance_open("ENTERTAINMENT", 2)
        assert not engine.is_affordance_open("ENTERTAINMENT", 5)


class TestDualVsInstant:
    def test_bed_dual_matches_instant_total(self, config_pack_factory, cpu_env_factory):
        config_dir = config_pack_factory(name="bed_dual_vs_instant")
        _set_global_vision(config_dir)
        _zero_bar_depletions(config_dir)

        # Make SLEEP a dual interaction with per_tick + completion effects, and create an instant clone
        import yaml

        level_dir = config_dir / "levels" / "L0_test"
        aff_path = level_dir / "affordances.yaml"
        data = yaml.safe_load(aff_path.read_text())
        aff_list = data["affordances"]["affordances"] if isinstance(data["affordances"], dict) else data["affordances"]
        for aff in aff_list:
            if aff["name"] == "SLEEP":
                aff["interaction_type"] = "dual"
                aff["duration_ticks"] = 5
                aff["costs_per_tick"] = {"money": 0.01}
                aff["interactions"] = {
                    "on_start": [],
                    "per_tick": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.05"}],
                    "on_completion": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.25"}],
                    "on_early_exit": [],
                    "on_failure": [],
                }
        if isinstance(data["affordances"], dict):
            data["affordances"]["affordances"] = aff_list
        else:
            data["affordances"] = aff_list
        aff_path.write_text(yaml.safe_dump(data, sort_keys=False))

        # Instant variant: copy pack and convert Bed to instant with same total effect
        config_dir_instant = config_pack_factory(name="bed_instant_variant")
        _set_global_vision(config_dir_instant)
        _zero_bar_depletions(config_dir_instant)
        level_dir_inst = config_dir_instant / "levels" / "L0_test"
        aff_path_inst = level_dir_inst / "affordances.yaml"
        data_inst = yaml.safe_load(aff_path_inst.read_text())
        aff_list_inst = data_inst["affordances"]["affordances"] if isinstance(data_inst["affordances"], dict) else data_inst["affordances"]
        for aff in aff_list_inst:
            if aff["name"] == "SLEEP":
                aff["interaction_type"] = "instant"
                aff.pop("duration_ticks", None)
                aff.pop("costs_per_tick", None)
                aff["interactions"] = {
                    "on_start": [
                        {
                            "modify": "target.bar.energy",
                            "value": "target.bar.energy + (0.05 * 5 + 0.25)",
                        }
                    ],
                    "per_tick": [],
                    "on_completion": [],
                    "on_early_exit": [],
                    "on_failure": [],
                }
        if isinstance(data_inst["affordances"], dict):
            data_inst["affordances"]["affordances"] = aff_list_inst
        else:
            data_inst["affordances"] = aff_list_inst
        aff_path_inst.write_text(yaml.safe_dump(data_inst, sort_keys=False))

        env_dual = cpu_env_factory(config_dir=config_dir, level_name="L0_test", num_agents=1)
        env_inst = cpu_env_factory(config_dir=config_dir_instant, level_name="L0_test", num_agents=1)

        env_dual.reset()
        env_inst.reset()
        env_dual.positions[0] = env_dual.affordances["SLEEP"]
        env_inst.positions[0] = env_inst.affordances["SLEEP"]
        env_dual.meters[0, 0] = 0.3
        env_inst.meters[0, 0] = 0.3
        env_dual.meters[0, 3] = 0.5
        env_inst.meters[0, 3] = 0.5

        for _ in range(5):
            env_dual.step(torch.tensor([4], device=env_dual.device))
        dual_gain = env_dual.meters[0, 0].item() - 0.3

        env_inst.step(torch.tensor([4], device=env_inst.device))
        inst_gain = env_inst.meters[0, 0].item() - 0.3

        assert pytest.approx(inst_gain, rel=0.05) == dual_gain
