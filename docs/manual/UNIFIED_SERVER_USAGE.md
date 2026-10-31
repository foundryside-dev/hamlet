# Training with the live viewer

`scripts/run_demo.py` trains an agent on one level of a config pack and, in the same process,
serves the latest checkpoint over a WebSocket so the Vue viewer can watch it play. The viewer
runs separately, so you can restart or edit it without stopping training.

Checked against `scripts/run_demo.py`, `src/townlet/demo/` and `frontend/` on 2026-10-31.

## Quick start

In one terminal, from the repository root:

```bash
uv run scripts/run_demo.py --config configs/default_curriculum \
    --level L1_full_observability --episodes 10000 --inference-port 8766
```

In a second terminal:

```bash
cd frontend
npm ci        # first time only
npm run dev
```

Open <http://localhost:5173>. The viewer connects to `ws://localhost:8766/ws`.

## Options

| Option | Required | Meaning |
| --- | --- | --- |
| `--config DIR` | yes | Config pack directory, for example `configs/default_curriculum` |
| `--level NAME` | yes | Level under `levels/`, for example `L1_full_observability` |
| `--inference-port PORT` | yes | WebSocket port for the viewer |
| `--episodes N` | no | Episodes to train; defaults to the level's `training.yaml` `max_episodes` |
| `--checkpoint-dir DIR` | no | Resume from this checkpoint directory instead of starting a new run |
| `--force-new-vfs` | no | When the checkpoint's variable layout no longer matches the pack, start a fresh run instead of refusing |
| `--debug` | no | Debug-level logging |

The viewer's port is fixed at 8766 in `frontend/src/stores/simulation.js`. If you train on another
port, change it there as well.

## What a run writes

Each run gets its own directory, named by the level's `output_subdir` and a timestamp:

```text
runs/L1_full_observability/2026-10-31_213045/
  checkpoints/
    checkpoint_ep00000.pt
    checkpoint_ep00000.pt.sha256
    ...
  config_snapshot/      # copy of the pack as compiled
  tensorboard/
  metrics.db            # SQLite episode metrics
  training.log
```

The runner saves a checkpoint every 100 episodes and once more when training ends. The
`checkpointing.interval` field in `training.yaml` is validated but not yet read by the runner.

To resume, pass the run's `checkpoints/` directory:

```bash
uv run scripts/run_demo.py --config configs/default_curriculum \
    --level L1_full_observability --inference-port 8766 \
    --checkpoint-dir runs/L1_full_observability/2026-10-31_213045/checkpoints
```

A resume is refused if any part of the pack that the checkpoint was trained on has changed. See
[Reproducibility](../../README.md#reproducibility).

## Serving a checkpoint without training

```bash
uv run python -m townlet.demo.live_inference \
    runs/L1_full_observability/2026-10-31_213045/checkpoints 8766 0.2 10000 \
    configs/default_curriculum L1_full_observability
```

The positional arguments are the checkpoint directory, port, delay between steps in seconds,
number of episodes to play, pack and level.

## TensorBoard

```bash
uv run tensorboard --logdir runs/L1_full_observability/2026-10-31_213045/tensorboard
```

Then open <http://localhost:6006>. See [TENSORBOARD_INTEGRATION.md](TENSORBOARD_INTEGRATION.md).

## Stopping

Press `Ctrl+C` once. Training stops at the next safe point, saves a final checkpoint and shuts
the inference server down.

## Security

The inference server listens on all interfaces with no authentication. Run it on a trusted
network. See [SECURITY.md](../../SECURITY.md).

## Troubleshooting

**Port already in use.** Another server is still running. Stop it, or choose another port and
update the viewer to match.

**The viewer shows nothing.** Check that the training terminal logged `Uvicorn running on
http://0.0.0.0:8766` and that at least one checkpoint has been saved (the first is written at
episode 0).

**Resume refused.** The message names the hash that moved. Either revert the pack change or start
a new run without `--checkpoint-dir`.
