#!/usr/bin/env python3
"""
Unified Demo Server Entry Point

Single-command interface for running Hamlet training, inference, and frontend together.

Usage (v2.1 hierarchical configs):
    python run_demo.py --config configs/default_curriculum --level L1_full_observability --episodes 10000

Author: Hamlet Project
Date: November 2, 2025
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from townlet.config.resolved_launch import resolve_launch
from townlet.demo.unified_server import UnifiedServer

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified Hamlet Demo Server - Training, Inference, and Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start training + inference (then run frontend separately) for a given level
  python run_demo.py --config configs/default_curriculum --level L1_full_observability --episodes 10000 --inference-port 8766
  # In another terminal: cd frontend && npm run dev

  # Resume from checkpoint
  python run_demo.py --config configs/default_curriculum --level L1_full_observability \\
      --checkpoint-dir runs/L1_full_observability/2025-11-02_123456/checkpoints --inference-port 8766

  # Start a fresh branch when that checkpoint's VFS ABI no longer matches
  python run_demo.py --config configs/default_curriculum --level L1_full_observability \\
      --checkpoint-dir runs/L1_full_observability/2025-11-02_123456/checkpoints --inference-port 8766 --force-new-vfs

  # Custom inference port
  python run_demo.py --config configs/default_curriculum --level L1_full_observability \\
      --episodes 5000 --inference-port 8800

Note:
  Frontend runs separately for better stability and Vue HMR support.
  Start frontend with: cd frontend && npm run dev
""",
    )

    # Required arguments
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to v2.1 experiment directory (e.g., configs/default_curriculum)",
    )

    parser.add_argument(
        "--level",
        type=str,
        required=True,
        help="Curriculum level name to run",
    )

    parser.add_argument(
        "--episodes",
        type=int,
        help="Total number of training episodes to run (default: read from config YAML)",
    )

    # Optional arguments
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        help="Directory for checkpoints. If not provided, auto-generated in runs/ structure",
    )

    parser.add_argument(
        "--inference-port",
        type=int,
        required=True,
        help="Port for inference WebSocket server",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug-level logging for troubleshooting")

    parser.add_argument(
        "--force-new-vfs",
        action="store_true",
        help="Start a fresh run branch instead of resuming when checkpoint vfs_hash differs from the current VFS ABI",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # The compiler owns declaration transport and located selection diagnostics.
    try:
        resolved = resolve_launch(Path(args.config), level_name=args.level)
    except Exception as error:
        logger.error("Failed to resolve launch: %s", error)
        if args.debug:
            logger.exception("Full traceback:")
        sys.exit(1)

    config_dir = resolved.root
    level_name = resolved.level_name
    training_origin = resolved.declaration_origins[f"levels/{level_name}/training"]
    authored_episodes = resolved.effective.training.training_loop.max_episodes
    # Preserve the explicit runtime request without changing the authored DTO.
    total_episodes = args.episodes
    if total_episodes is None:
        total_episodes = authored_episodes

    # Print startup banner
    logger.info("=" * 60)
    logger.info("Unified Demo Server Starting")
    logger.info("=" * 60)
    logger.info(f"Experiment Root: {config_dir}")
    logger.info(f"Level: {level_name}")
    logger.info("Training Config: %s", training_origin)
    logger.info("Authored Episodes: %s", authored_episodes)
    if args.episodes is not None:
        logger.info(f"Episodes: {total_episodes} (from --episodes flag)")
    else:
        logger.info(f"Episodes: {total_episodes} (from training config)")
    if args.checkpoint_dir:
        logger.info(f"Checkpoint Dir: {args.checkpoint_dir}")
    else:
        logger.info("Checkpoint Dir: Auto-generated in runs/ structure")
    logger.info(f"Inference Port: {args.inference_port}")
    logger.info("Note: Frontend runs separately (cd frontend && npm run dev)")
    logger.info("=" * 60)

    # Create unified server
    try:
        server = UnifiedServer(
            config_dir=str(config_dir),
            total_episodes=total_episodes,
            checkpoint_dir=args.checkpoint_dir,
            inference_port=args.inference_port,
            level_name=level_name,
            force_new_vfs=args.force_new_vfs,
        )
    except Exception as e:
        logger.error(f"Failed to create UnifiedServer: {e}")
        if args.debug:
            logger.exception("Full traceback:")
        sys.exit(1)

    # Register signal handlers for graceful shutdown with escalation
    shutdown_count = [0]  # Mutable container to track shutdown attempts

    def signal_handler(signum, frame):
        """Handle SIGINT (Ctrl+C) and SIGTERM with escalating response."""
        shutdown_count[0] += 1
        signal_name = signal.Signals(signum).name

        if shutdown_count[0] == 1:
            # First signal: graceful shutdown
            logger.info(f"\nShutdown signal received ({signal_name}). Gracefully stopping...")
            logger.info("(Press Ctrl+C again to force immediate exit)")
            server.stop()
        elif shutdown_count[0] == 2:
            # Second signal: warn but continue graceful shutdown
            logger.warning("\nSecond shutdown signal received. Waiting for training thread to finish current episode...")
            logger.warning("(Press Ctrl+C again to force immediate exit)")
        else:
            # Third+ signal: immediate exit
            logger.error("\nForce shutdown! Exiting immediately without cleanup.")
            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the server (blocks until shutdown)
    try:
        server.start()
    except KeyboardInterrupt:
        # Already handled by signal handler
        pass
    except Exception as e:
        logger.error(f"Unexpected error during server operation: {e}")
        if args.debug:
            logger.exception("Full traceback:")
        server.stop()
        sys.exit(1)

    # Clean exit
    logger.info("=" * 60)
    logger.info("All systems stopped. Goodbye!")
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
