"""Finite PER estimators matched to their actual ordered sampling laws.

Receipts address positions in the supplied population. Storage owns stable
transition handles separately. The legacy adapter deliberately consumes the
external global NumPy stream; the qualified API requires an explicit Generator.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from townlet.training.replay_contract import SamplingReceipt

SUCCESSIVE = "successive_without_replacement"
INDEPENDENT = "independent_with_replacement"
WEIGHT_RULES = {SUCCESSIVE: "successive_conditional_residual_v1", INDEPENDENT: "independent_inverse_probability_v1"}


def _unit_interval(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"PER {field} must be a finite number in [0, 1]")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"PER {field} must be a finite number in [0, 1]") from error
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise ValueError(f"PER {field} must be a finite number in [0, 1]")
    return result


def _positive(values: np.ndarray, indices: np.ndarray, field: str) -> None:
    bad = np.flatnonzero(~np.isfinite(values) | (values <= 0))
    if bad.size:
        index = int(indices[int(bad[0])])
        raise ValueError(f"PER {field} at population index {index} is not positive finite representable {values.dtype.name}")


def _probabilities(scores: np.ndarray, indices: np.ndarray) -> np.ndarray:
    with np.errstate(under="ignore"):
        probabilities = scores / scores.sum(dtype=np.float64)
    _positive(probabilities, indices, "probability/support")
    return probabilities


def _final_weights(log_weights: np.ndarray, beta: float, indices: np.ndarray) -> np.ndarray:
    if beta == 0:
        return np.ones(log_weights.shape, dtype=np.float64)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        weights = np.exp(beta * log_weights)
    _positive(weights, indices, "final beta weight")
    return weights


def _log_weights(q: np.ndarray, population: int, tail: np.ndarray, mode: str) -> np.ndarray:
    negative_log_q = -np.log(q)
    if mode == INDEPENDENT:
        return negative_log_q - math.log(population)
    log_tail = np.full(tail.shape, -np.inf, dtype=np.float64)
    np.log(tail, out=log_tail, where=tail > 0)
    return np.logaddexp(log_tail, negative_log_q) - math.log(population)


def _prepare(
    priorities: np.ndarray, alpha: float, beta: float, batch_size: int, mode: str, weight_dtype: np.dtype
) -> tuple[np.ndarray, np.ndarray, float]:
    if not isinstance(priorities, np.ndarray) or priorities.dtype != np.float64 or priorities.ndim != 1 or not priorities.size:
        raise ValueError("PER priorities must be a nonempty one-dimensional float64 array")
    indices = np.arange(priorities.size, dtype=np.int64)
    _positive(priorities, indices, "priority")
    alpha_value, beta_value = _unit_interval(alpha, "alpha"), _unit_interval(beta, "beta")
    if type(mode) is not str or mode not in WEIGHT_RULES:
        raise ValueError(f"PER sampling mode is unsupported: {mode!r}")
    if isinstance(batch_size, (bool, np.bool_)) or not isinstance(batch_size, (int, np.integer)) or batch_size <= 0:
        raise ValueError("PER batch_size must be a positive integer")
    if mode == SUCCESSIVE and batch_size > priorities.size:
        raise ValueError(f"Buffer size ({priorities.size}) < batch_size ({batch_size})")
    # Log centering preserves alpha<1 support even when p/max(p) would
    # underflow before exponentiation. Scores are at most one, so sums stay finite.
    logs = np.log(priorities)
    with np.errstate(under="ignore"):
        scores = np.exp(alpha_value * (logs - logs.max()))
    _positive(scores, indices, "scaled priority/support")
    probabilities = _probabilities(scores, indices)
    if beta_value != 0 and not (mode == SUCCESSIVE and batch_size == priorities.size):
        # Each later residual q_i is >= its initial P_i; the first-position
        # correction bounds all possible final weights before consuming RNG.
        tail = np.full(priorities.size, batch_size - 1, dtype=np.float64)
        maximum_weights = _final_weights(_log_weights(probabilities, priorities.size, tail, mode), beta_value, indices)
        if weight_dtype != np.dtype(np.float64):
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                transported = maximum_weights.astype(weight_dtype)
            _positive(transported, indices, "final beta weight")
    return scores, probabilities, beta_value


def _receipt(scores: np.ndarray, indices: np.ndarray, beta: float, mode: str) -> SamplingReceipt:
    population, batch = len(scores), len(indices)
    if mode == INDEPENDENT:
        conditional = _probabilities(scores, np.arange(population, dtype=np.int64))[indices].copy()
    else:
        conditional = np.empty(batch, dtype=np.float64)
        remaining = np.ones(population, dtype=np.bool_)
        for position, index in enumerate(indices):
            support = np.flatnonzero(remaining)
            probabilities = _probabilities(scores[support], support)
            conditional[position] = probabilities[int(np.searchsorted(support, index))]
            remaining[index] = False
    if beta == 0 or (mode == SUCCESSIVE and batch == population):
        weights = np.ones(batch, dtype=np.float64)
    else:
        tail = np.arange(batch - 1, -1, -1, dtype=np.float64)
        weights = _final_weights(_log_weights(conditional, population, tail, mode), beta, indices)
    return SamplingReceipt(indices, weights, population, conditional, mode, "transition", WEIGHT_RULES[mode])


def _sample(
    priorities: np.ndarray,
    alpha: float,
    beta: float,
    batch_size: int,
    mode: str,
    choice: Callable[..., Any],
    global_legacy: bool,
    weight_dtype: np.dtype,
) -> SamplingReceipt:
    scores, probabilities, beta_value = _prepare(priorities, alpha, beta, batch_size, mode, weight_dtype)
    if mode == INDEPENDENT or global_legacy:
        indices = np.asarray(choice(len(scores), batch_size, p=probabilities, replace=mode == INDEPENDENT), dtype=np.int64)
    else:
        # Re-normalize the remaining support rather than subtracting previously
        # selected mass from a total that may round away the residual population.
        indices = np.empty(batch_size, dtype=np.int64)
        remaining = np.ones(len(scores), dtype=np.bool_)
        for position in range(batch_size):
            support = np.flatnonzero(remaining)
            conditional = _probabilities(scores[support], support)
            index = int(choice(support, p=conditional, replace=False))
            indices[position] = index
            remaining[index] = False
    return _receipt(scores, indices, beta_value, mode)


def sample_units(
    priorities: np.ndarray, *, alpha: float, beta: float, batch_size: int, mode: str, rng: np.random.Generator
) -> SamplingReceipt:
    """Sample with an explicit caller-owned Generator and owned float64 receipt."""
    if not isinstance(rng, np.random.Generator):
        raise ValueError("PER rng must be an explicit numpy.random.Generator")
    return _sample(priorities, alpha, beta, batch_size, mode, rng.choice, False, np.dtype(np.float64))


def sample_legacy_units(priorities: np.ndarray, *, alpha: float, beta: float, batch_size: int) -> SamplingReceipt:
    """Preserve global NumPy successive selection, with the corrected estimator."""
    return _sample(priorities, alpha, beta, batch_size, SUCCESSIVE, np.random.choice, True, np.dtype(np.float64))


def sample_legacy_float32_units(priorities: np.ndarray, *, alpha: float, beta: float, batch_size: int) -> SamplingReceipt:
    """Preflight legacy dictionary transport before drawing; keep the receipt64."""
    return _sample(priorities, alpha, beta, batch_size, SUCCESSIVE, np.random.choice, True, np.dtype(np.float32))
