# Controlled-reset numerical recipe: prospective registration

PDR-0160 and its scoped Astra review authorize this second CPU comparison
family. At this registration no amended-family bank exists. The original
failed reference banks and their preregistration remain unchanged. The exact
frozen external instrument and recipe are retained here for reproducibility.
Real learner/sample/target checks and all final gates remain required.

Instrument SHA256: `f166e8f48165c46da4fba5413839b9a001e22a2da5abd04b31a6904f29eb6d77`.

Recipe JSON SHA256: `799ec391e1eb38c53b4e6c1c12bc0837e1131f1c5c0b3d10659c40e1f6c52d1f`.

```json
{
  "schema": "episode-lanes.controlled-reset-registration.v2",
  "status": "prospective; no recipe-2 bank has been created",
  "recipe_version": 2,
  "recipe_family": "cpu-controlled-reset-inputs",
  "instrument": {
    "path": "runs/episode-lanes/2026-10-02/implementation/causal/population-numerics/controlled-reset-capture.py",
    "sha256": "f166e8f48165c46da4fba5413839b9a001e22a2da5abd04b31a6904f29eb6d77"
  },
  "original_instrument": {
    "path": "runs/episode-lanes/2026-10-02/implementation/causal/population-numerics/capture.py",
    "sha256": "8433076aeae5011c88da18d492ea052525bf4b1bf5a04aa472e08489315d11b4",
    "preserved_byte_for_byte": true
  },
  "helpers": {
    "population-helper.py": "1612d6c2ab5ab01c4dbd4156543e45fe7f8f57827edfca6bcc996b490feb2058",
    "fixture-helper.py": "b22601ae6cac1c78fe86f3e23b717c831905df9c39850daa24b406ae4e6f5c33"
  },
  "base_seed": 42,
  "device": "cpu",
  "initial_episode_0": "unchanged existing helper reset after seed_all(42)",
  "reset_seeds": {
    "1": 43,
    "2": 44,
    "3": 45,
    "4": 46,
    "5": 47,
    "6": 48,
    "7": 49,
    "8": 50
  },
  "reset_intervention": "capture caller CPU state; fork_rng(devices=[]); torch.default_generator.manual_seed(42 + episode); original pop.reset(); exit context; assert caller CPU state exactly restored",
  "source_cuts": [
    "parent",
    "E2",
    "E3",
    "P1",
    "final-candidate"
  ],
  "recipes": [
    "standard-seq1-double0",
    "standard-seq1-double1",
    "per-seq1-double0",
    "per-seq1-double1",
    "recurrent-seq1-double0",
    "recurrent-seq1-double1",
    "recurrent-seq2-double0",
    "recurrent-seq2-double1"
  ],
  "parameters": {
    "episodes": 9,
    "agents": 2,
    "ending_ticks": [
      2,
      5
    ],
    "vector_steps": 45,
    "learner_batch_size": 2,
    "predictor_batch_size": 7,
    "train_frequency": 1,
    "lifespan": 20
  },
  "unchanged_instrumentation": [
    "normal novelty producer executes",
    "actual raw fixed/predictor MSE",
    "independent original pooled RMS checks",
    "actual predictor forward hook",
    "original Q and predictor SGD",
    "source clean/import resolution checks"
  ],
  "new_observations": [
    "controlled reset seeds and caller CPU RNG before/after digests",
    "reset observations/positions/affordance layout/meters/dones/counters",
    "actual per-step per-agent named meters/positions/affordance layout",
    "actual predictor buffer before/admitted/consumed/after hashes at original update",
    "initial/final Q and predictor parameter digests",
    "actual predictor supplied tensor bytes bound to independent insertion episode/tick/agent predecessors; duplicate matches retained and cannot qualify"
  ],
  "constraints": [
    "no original reference bank or preregistration rewrite",
    "no production RNG isolation",
    "all eight recipes use identical frozen instrument/helpers for every cut",
    "all world/config/action/done identities remain exact across source cuts",
    "final eligible normalization and predictor admission exactly63, final once-only outcomes18",
    "all changed numeric coordinates bind exact values and actual causal source SHA",
    "final candidate requires separate GO after clean source supplied"
  ],
  "review": {
    "path": "runs/episode-lanes/2026-10-02/implementation/review/reset-amendment/review.md",
    "verdict": "APPROVE CPU-only controlled-reset recipe; no acceptance of unrun bank"
  }
}
```

```python
"""Recipe 2: CPU-controlled reset inputs with original real learners and RND."""
import hashlib
import argparse
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--source-root', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
source = args.source_root.resolve()
instrument_root = Path('/home/john/hamlet/.worktrees/episode-lane-implementation')
helpers_bank = Path(__file__).resolve().parent
bank = args.output.resolve()
bank.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(source / 'src'))
sys.path.insert(1, str(instrument_root))
import torch
import townlet
from townlet.determinism import seed_all

assert Path(townlet.__file__).resolve().is_relative_to(source / 'src')
revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
assert len(revision) == 40
assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--', 'src', 'configs', 'scripts', 'tests'], text=True).strip()
helpers = runpy.run_path(str(helpers_bank / 'population-helper.py'))
make = helpers['make_lane_population']
schedule = helpers['schedule_for']
controlled = helpers['controlled_action_schedule']
fixture_module = sys.modules['tests.test_townlet.regressions.fixtures.episode_lanes']
fixture_source = Path(fixture_module.__file__).resolve()
fixture_sha256 = hashlib.sha256(fixture_source.read_bytes()).hexdigest()
assert fixture_sha256 == hashlib.sha256((helpers_bank / 'fixture-helper.py').read_bytes()).hexdigest()

RECIPE_VERSION = 2
RESET_SEEDS = {episode: 42 + episode for episode in range(1, 9)}

def hashed(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

cases = []
torch.set_num_threads(1)
with tempfile.TemporaryDirectory(prefix='parent-population-numerics-') as temporary:
    for mode, sequence_length in [('standard', 1), ('per', 1), ('recurrent', 1), ('recurrent', 2)]:
        for double in (False, True):
            seed_all(42)
            name = f'{mode}-seq{sequence_length}-double{int(double)}'
            pop = make(Path(temporary) / name, mode=mode, num_agents=2, lifespan=20, batch_size=2,
                       sequence_length=sequence_length, rnd_batch_size=7, double_dqn=double)
            env = pop.env
            rnd = pop.exploration.rnd
            assert pop.device.type == env.device.type == 'cpu'
            assert all(parameter.device.type == 'cpu' for parameter in pop.q_network.parameters())
            assert all(parameter.device.type == 'cpu' for parameter in rnd.predictor_network.parameters())
            resets = []
            predictor_buffer_calls = []
            previous_predictor_remaining = []
            previous_predictor_remaining_bindings = []
            original_predictor_update = rnd.update_predictor
            original_novelty = pop.exploration.compute_intrinsic_rewards
            calls = []
            reference_errors = []
            predictor_training_inputs = []
            context = {'episode': 0, 'tick': 0}
            def novelty(observations, update_stats):
                with torch.no_grad():
                    errors = ((rnd.fixed_network(observations) - rnd.predictor_network(observations)) ** 2).mean(dim=1)
                before_stats = {'mean': float(rnd.reward_rms.mean), 'var': float(rnd.reward_rms.var), 'count': float(rnd.reward_rms.count)}
                result = original_novelty(observations, update_stats)
                if update_stats:
                    reference_errors.extend(float(value) for value in errors)
                count = 1e-4 + len(reference_errors)
                mean = math.fsum(reference_errors) / count
                variance = (1e-4 * (1.0 + mean * mean) + math.fsum((value - mean) ** 2 for value in reference_errors)) / count
                assert math.isclose(float(rnd.reward_rms.count), count, rel_tol=1e-5, abs_tol=1e-6)
                assert math.isclose(float(rnd.reward_rms.mean), mean, rel_tol=1e-5, abs_tol=1e-6)
                assert math.isclose(float(rnd.reward_rms.var), variance, rel_tol=1e-5, abs_tol=1e-6)
                assert torch.allclose(result, errors / (math.sqrt(variance) + 1e-8), rtol=1e-5, atol=1e-6)
                calls.append({**context, 'update_stats': update_stats,
                              'observation_rows': [hashed(row) for row in observations],
                              'raw_mse': errors.tolist(), 'rms_before': before_stats,
                              'rms_after': {'mean': float(rnd.reward_rms.mean), 'var': float(rnd.reward_rms.var), 'count': float(rnd.reward_rms.count)},
                              'rewards': result.tolist()})
                return result
            def predictor_update(*positional, **keyword):
                # Observe the actual already-appended queue; do not replace admission,
                # sample membership, optimizer ordering or the original SGD call.
                before = [hashed(row) for row in rnd.obs_buffer]
                assert before[:len(previous_predictor_remaining)] == previous_predictor_remaining
                admitted = before[len(previous_predictor_remaining):]
                actual_predecessors = [row.detach().cpu() for row in pop.current_obs]
                independent_predecessors = [
                    {'coordinate': [name, context['episode'], context['tick'], agent],
                     'sha256': hashed(row), 'eligible_on_entry': agent in context['entry_agent_indices']}
                    for agent, row in enumerate(actual_predecessors)]
                admitted_bindings = []
                for row in rnd.obs_buffer[len(previous_predictor_remaining):]:
                    # Bind actual supplied tensor bytes to the independently read
                    # predecessor at this insertion call, retaining any ambiguity.
                    matches = [agent for agent, predecessor_row in enumerate(actual_predecessors)
                               if torch.equal(row.cpu(), predecessor_row)]
                    admitted_bindings.append({'sha256': hashed(row), 'matching_agent_indices': matches,
                        'coordinate': [name, context['episode'], context['tick'], matches[0]] if len(matches) == 1 else None,
                        'eligible_on_entry': (matches[0] in context['entry_agent_indices']) if len(matches) == 1 else None})
                before_bindings = previous_predictor_remaining_bindings + admitted_bindings
                result = original_predictor_update(*positional, **keyword)
                after = [hashed(row) for row in rnd.obs_buffer]
                consumed = len(before) - len(after)
                assert consumed >= 0 and before[consumed:] == after
                predictor_buffer_calls.append({**context, 'before': before,
                    'admitted': admitted, 'consumed': before[:consumed], 'after': after,
                    'independent_predecessors': independent_predecessors,
                    'before_bindings': before_bindings, 'admitted_bindings': admitted_bindings,
                    'consumed_bindings': before_bindings[:consumed], 'after_bindings': before_bindings[consumed:],
                    'admission_binding_unique': all(len(binding['matching_agent_indices']) == 1 for binding in admitted_bindings)})
                previous_predictor_remaining[:] = after
                previous_predictor_remaining_bindings[:] = before_bindings[consumed:]
                return result
            def predictor_hook(module, values):
                if torch.is_grad_enabled():
                    predictor_training_inputs.extend({**context, 'sha256': hashed(row)} for row in values[0])
            hook = rnd.predictor_network.register_forward_pre_hook(predictor_hook)
            rows = []
            initial_q = {key: hashed(value) for key, value in pop.q_network.state_dict().items()}
            initial_predictor = {key: hashed(value) for key, value in rnd.predictor_network.state_dict().items()}
            with patch.object(pop.exploration, 'compute_intrinsic_rewards', side_effect=novelty), \
                    patch.object(rnd, 'update_predictor', side_effect=predictor_update):
                for episode in range(9):
                    caller_cpu_before = torch.get_rng_state().clone() if episode else None
                    if episode:
                        # PDR-0160: seed only CPU for common exogenous reset inputs,
                        # then restore this run's own caller CPU RNG exactly.
                        with torch.random.fork_rng(devices=[]):
                            torch.default_generator.manual_seed(RESET_SEEDS[episode])
                            pop.reset()
                        assert torch.equal(torch.get_rng_state(), caller_cpu_before)
                    resets.append({'episode': episode, 'control_applied': bool(episode),
                        'cpu_reset_seed': RESET_SEEDS[episode] if episode else None,
                        'initial_episode_control': None if episode else 'unchanged existing helper reset after seed_all(42)',
                        'caller_cpu_rng_before_sha256': hashed(caller_cpu_before) if episode else None,
                        'caller_cpu_rng_after_sha256': hashed(torch.get_rng_state()),
                        'caller_cpu_rng_restored': True if episode else None,
                        'positions': env.positions.tolist(),
                        'affordance_layout': {key: value.tolist() for key, value in sorted(env.affordances.items())},
                        'meters': {key: env.meters[:, index].tolist() for key, index in sorted(env.meter_name_to_index.items())},
                        'observation_sha256': [hashed(row) for row in pop.current_obs],
                        'world_tick': env.global_tick, 'step_counts': env.step_counts.tolist(), 'dones': env.dones.tolist()})
                    with controlled(pop.exploration, env, schedule((2, 5))) as selections:
                        for tick in range(1, 6):
                            context.update(episode=episode, tick=tick)
                            active = (~env.dones).clone()
                            context['entry_agent_indices'] = torch.nonzero(active).flatten().tolist()
                            predecessor = pop.current_obs.clone()
                            state = pop.step_population(env)
                            for agent in range(2):
                                rows.append({'key': [name, episode, tick, agent], 'active_on_entry': bool(active[agent]),
                                    'predecessor_sha256': hashed(predecessor[agent]), 'successor_sha256': hashed(state.observations[agent]),
                                    'action': int(state.actions[agent]), 'done': bool(state.dones[agent]),
                                    'reward': float(state.rewards[agent]),
                                    'components': {key: float(value[agent]) for key, value in state.info['reward_components'].items()},
                                    'intrinsic_weight': float(state.info['intrinsic_weight'][agent]),
                                    'q_values': selections.q_values[-1][agent].tolist(),
                                    'world_tick': env.global_tick, 'survival': int(env.step_counts[agent]),
                                    'meters': {key: float(env.meters[agent, index]) for key, index in sorted(env.meter_name_to_index.items())},
                                    'position': env.positions[agent].tolist(),
                                    'affordance_layout': {key: value.tolist() for key, value in sorted(env.affordances.items())}})
            hook.remove()
            final_q = {key: hashed(value) for key, value in pop.q_network.state_dict().items()}
            final_predictor = {key: hashed(value) for key, value in rnd.predictor_network.state_dict().items()}
            case = {'recipe': name, 'recipe_version': RECIPE_VERSION, 'rows': rows, 'novelty_calls': calls,
                    'resets': resets, 'predictor_buffer_calls': predictor_buffer_calls,
                    'q_parameter_hashes': {'initial': initial_q, 'final': final_q},
                    'predictor_parameter_hashes': {'initial': initial_predictor, 'final': final_predictor},
                    'independent_rms_reference_qualified': True, 'predictor_training_inputs': predictor_training_inputs,
                    'config_inventory': {str(path.relative_to(Path(temporary) / name)): hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in sorted((Path(temporary) / name).rglob('*.yaml')) if path.is_file()},
                    'q_parameters_changed': initial_q != final_q, 'predictor_parameters_changed': initial_predictor != final_predictor,
                    'training_updates': pop.training_step_counter, 'survival_history': list(pop.exploration.survival_history),
                    'remaining_predictor_observations': [hashed(row) for row in rnd.obs_buffer]}
            (bank / f'{name}.json').write_text(json.dumps(case, indent=2, allow_nan=False) + '\n')
            cases.append({'recipe': name, 'rows': len(rows), 'normalization_rows': sum(len(call['observation_rows']) for call in calls if call['update_stats']),
                          'predictor_training_rows': len(predictor_training_inputs),
                          'q_parameters_changed': case['q_parameters_changed'], 'predictor_parameters_changed': case['predictor_parameters_changed'],
                          'training_updates': case['training_updates']})
            print(json.dumps(cases[-1]), flush=True)

imports = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
           if (name == 'townlet' or name.startswith('townlet.')) and getattr(module, '__file__', None)}
assert all(Path(path).is_relative_to(source / 'src' / 'townlet') for path in imports.values())
receipt = {'recipe_version': RECIPE_VERSION, 'recipe_family': 'cpu-controlled-reset-inputs',
           'reset_control': {'device_scope': 'CPU Torch default generator only',
                            'initial_episode_0': 'unchanged existing helper reset after seed_all(42)',
                            'seeds': RESET_SEEDS, 'caller_cpu_rng_restoration': 'exact state equality asserted after every controlled reset',
                            'production_rng_policy_changed': False},
           'fixture_helper_sha256': fixture_sha256, 'fixture_helper_source': str(fixture_source),
           'original_instrument_sha256': '8433076aeae5011c88da18d492ea052525bf4b1bf5a04aa472e08489315d11b4',
           'revision': revision, 'source_root': str(source), 'imports': imports, 'seed': 42, 'device': 'cpu', 'cases': cases,
           'instrument_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'helper_sha256': hashlib.sha256((helpers_bank / 'population-helper.py').read_bytes()).hexdigest(),
           'source_inventory_sha256': hashlib.sha256(json.dumps({str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((source / 'src').rglob('*.py'))}, sort_keys=True).encode()).hexdigest(),
           'files': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(bank.iterdir()) if path.is_file() and path.suffix in ('.py', '.json')}}
(bank / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
```
