"""Differential harness for the strangler rewrite (WS-7, PDR-0006, PDR-0030).

Runs the frozen oracle worktree and the working tree against the same declared
universe and seed, and asserts their env-step traces agree everywhere
docs/oracle/known-divergences.md does not say otherwise.
"""

# The single machine-readable authority for the current oracle ref. When the
# oracle moves forward (PDR-0030 reversal path), this constant moves with the
# new tag; docs/oracle/ORACLE.md records the history.
ORACLE_TAG = "oracle-2026-08-13"

__all__ = ["ORACLE_TAG"]
