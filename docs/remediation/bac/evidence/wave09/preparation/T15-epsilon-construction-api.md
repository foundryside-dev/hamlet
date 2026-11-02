# T15 epsilon construction API — static supplement

Checked in existing `/workspace/hamlet` at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Reuses the existing five-source / 2,125-line context; no new implementation/helper/test source was opened.

`src/townlet/exploration/epsilon_greedy.py:17,25–41` defines the public class directly:

```python
class EpsilonGreedyExploration(ExplorationStrategy):
    def __init__(
        self,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
```

Source-supported direct construction, with the existing defaults written explicitly:

```python
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
exploration = EpsilonGreedyExploration(epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01)
```

These three positional-or-keyword floats are the only constructor parameters. All have the displayed source defaults, so no argument or configuration object is required by this constructor. It stores them as `self.epsilon`, `self.epsilon_decay`, `self.epsilon_min`; it performs no constructor validation here. For an explicitly configured test, pass its chosen values under exactly those three names. No device, action dimension, seed, policy selector or resolved-config argument belongs in this call.

No epsilon construction factory or config DTO is defined in these five sources. External factory names, config-section spelling and YAML requiredness were not verified and are not supplied. Selection separately reads `agent_states.epsilons` (EG43–64), rather than `self.epsilon`; constructor scalar settings alone do not set per-agent selection epsilon.

| Reused whole source | Lines | SHA256 |
|---|---:|---|
| `training/replay_buffer.py` | 677 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |
| `training/prioritized_replay_buffer.py` | 1092 | `290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9` |
| `exploration/action_selection.py` | 120 | `2a2ddfbd9aaf01afa14b0d1907fa1f3c8823f253dcdc8d16a8ff4054bf3768b8` |
| `exploration/base.py` | 118 | `49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae` |
| `exploration/epsilon_greedy.py` | 118 | `f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059` |

Source paths in the table are under `src/townlet/`. Entry/exit source hashes/counts and HEAD match; tracked status remained clean. Only this ignored prose was written (`.git/info/exclude:7`, `/.superpowers/`). No imports, runtime, tests, index/tracked mutation, branch/worktree/copy or subagent action occurred. Existing 14 worktrees remain preserved; root owns integration. No durable rule was saved, no user-only fallback adopted, and the failed rule grants or restricts nothing. Return stationary.
