# Actual fixedsourcecandidate R1

Base 64748bdf0b623c66bdc400238d4c17645bd6fba7; tree 82b428748d2de3f46caca601893cb3308cdbb91a. Scopeexact4wholefiles/2886actual<=3750; no fifthsourcehelper. Actualdeltaall4ownedfilesbelow. Newtestinputtransportpreserves214cases/assertions, constructorsnewrng/unit required. Allsource/tests/index/trackeddocsfrozen. RequiredactualPOP/runner/nativeintegration remainsOPEN.

```diff
diff --git a/src/townlet/exploration/adaptive_intrinsic.py b/src/townlet/exploration/adaptive_intrinsic.py
index 4b7676a4..ac1a85f4 100644
--- a/src/townlet/exploration/adaptive_intrinsic.py
+++ b/src/townlet/exploration/adaptive_intrinsic.py
@@ -1,14 +1,28 @@
 """Adaptive intrinsic exploration with variance-based annealing."""
 
-from typing import Any
+from __future__ import annotations
+
+import math
+from copy import deepcopy
+from dataclasses import dataclass
+from typing import Any, Literal
 
 import torch
 
+from townlet.config.bac_options import RNDOptions
 from townlet.exploration.base import ExplorationStrategy
-from townlet.exploration.rnd import RNDExploration
+from townlet.exploration.rnd import PredictorServiceCounters, PredictorServiceReceipt, RNDExploration
+from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState
 from townlet.training.state import BatchedAgentState
 
 
+@dataclass
+class _PreparedAdaptive:
+    owner: object
+    attributes: dict[str, Any]
+    consumed: bool
+
+
 class AdaptiveIntrinsicExploration(ExplorationStrategy):
     """RND with adaptive annealing based on survival variance.
 
@@ -35,6 +49,9 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
         epsilon_min: float = 0.01,
         epsilon_decay: float = 0.995,
         device: torch.device = torch.device("cpu"),
+        *,
+        rng: WorldRNGState | None,
+        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
     ):
         """Initialize adaptive intrinsic exploration.
 
@@ -55,6 +72,17 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
             epsilon_decay: Epsilon decay rate
             device: Device for tensors
         """
+        self._validate_config(
+            {
+                "initial_intrinsic_weight": initial_intrinsic_weight,
+                "min_intrinsic_weight": min_intrinsic_weight,
+                "variance_threshold": variance_threshold,
+                "min_survival_fraction": min_survival_fraction,
+                "max_episode_length": max_episode_length,
+                "survival_window": survival_window,
+                "decay_rate": decay_rate,
+            }
+        )
         # RND instance (composition)
         self.rnd = RNDExploration(
             obs_dim=obs_dim,
@@ -65,6 +93,8 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
             epsilon_min=epsilon_min,
             epsilon_decay=epsilon_decay,
             device=device,
+            rng=rng,
+            service_clock_unit=service_clock_unit,
         )
 
         # Annealing parameters
@@ -82,6 +112,50 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
         # Survival tracking
         self.survival_history: list[float] = []
 
+    @staticmethod
+    def _validate_config(config: dict[str, Any]) -> None:
+        for name, value in config.items():
+            if name in {"max_episode_length", "survival_window"}:
+                if type(value) is not int or value <= 0:
+                    raise ValueError(f"Adaptive {name} must be a positive exact integer")
+            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
+                raise ValueError(f"Adaptive {name} must be a finite nonnegative scalar")
+        if config["min_intrinsic_weight"] > config["initial_intrinsic_weight"]:
+            raise ValueError("Adaptive minimum weight exceeds initial weight")
+        if config["min_survival_fraction"] > 1 or config["decay_rate"] > 1:
+            raise ValueError("Adaptive survival fraction and decay rate must be in [0,1]")
+        try:
+            int(config["min_survival_fraction"] * config["max_episode_length"])
+        except (OverflowError, ValueError) as error:
+            raise ValueError("Adaptive derived survival threshold is not representable") from error
+
+    def _config(self) -> dict[str, Any]:
+        return {
+            "initial_intrinsic_weight": self.initial_intrinsic_weight,
+            "min_intrinsic_weight": self.min_intrinsic_weight,
+            "variance_threshold": self.variance_threshold,
+            "min_survival_fraction": self.min_survival_fraction,
+            "max_episode_length": self.max_episode_length,
+            "survival_window": self.survival_window,
+            "decay_rate": self.decay_rate,
+        }
+
+    @property
+    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
+        return self.rnd.service_clock_unit
+
+    def configure_service(self, options: RNDOptions) -> None:
+        self.rnd.configure_service(options)
+
+    def predictor_service_counters(self) -> PredictorServiceCounters:
+        return self.rnd.predictor_service_counters()
+
+    def admit_and_service_at(self, observations: torch.Tensor, *, clock: ServiceClock) -> PredictorServiceReceipt:
+        return self.rnd.admit_and_service_at(observations, clock=clock)
+
+    def admit_and_service(self, observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt:
+        return self.rnd.admit_and_service(observations, vector_tick=vector_tick)
+
     def select_actions(
         self,
         q_values: torch.Tensor,
@@ -137,45 +211,36 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
         Args:
             survival_time: Number of steps agent survived this episode
         """
-        self.survival_history.append(survival_time)
-
-        # Keep only recent window
-        if len(self.survival_history) > self.survival_window:
-            self.survival_history = self.survival_history[-self.survival_window :]
-
-        # Check for annealing
-        if self.should_anneal():
-            self.anneal_weight()
-
-    def should_anneal(self) -> bool:
-        """Check if variance is below threshold AND performance is good.
-
-        Returns:
-            True if agent performance is consistent enough to reduce exploration
-
-        Note:
-            Uses incremental window checking (min 10 episodes) to avoid abrupt
-            behavior changes when hitting full window size. This provides smoother
-            annealing onset and earlier feedback on performance consistency.
-        """
-        # Need minimum data for reliable variance calculation
-        if len(self.survival_history) < 10:
-            return False
-
-        # Use whatever recent data we have (up to window size)
-        # This allows incremental checking instead of waiting for full window
-        window_size = min(self.survival_window, len(self.survival_history))
-        recent_survivals = torch.tensor(
-            self.survival_history[-window_size:],
-            dtype=torch.float32,
+        self._history_decision(self.survival_history)
+        prospective = [*self.survival_history, survival_time][-self.survival_window :]
+        anneal = self._history_decision(prospective)
+        weight = (
+            max(self.current_intrinsic_weight * self.decay_rate, self.min_intrinsic_weight) if anneal else self.current_intrinsic_weight
         )
-        variance = torch.var(recent_survivals).item()
-        mean_survival = torch.mean(recent_survivals).item()
+        self.survival_history, self.current_intrinsic_weight = prospective, weight
+
+    def _history_decision(self, history: list[float]) -> bool:
+        if type(history) is not list or len(history) > self.survival_window:
+            raise ValueError("Adaptive history must be an owned list within the selected window")
+        for value in history:
+            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
+                raise ValueError("Adaptive survival history requires finite nonnegative scalars")
+        try:
+            values = torch.tensor(history, dtype=torch.float32)
+        except (RuntimeError, OverflowError) as error:
+            raise ValueError("Adaptive history cannot be represented for variance computation") from error
+        if not torch.isfinite(values).all().item():
+            raise ValueError("Adaptive history is not finite in float32")
+        if len(history) < 10:
+            return False
+        variance, mean = torch.var(values).item(), torch.mean(values).item()
+        if not math.isfinite(variance) or not math.isfinite(mean):
+            raise ValueError("Adaptive history variance/mean is nonfinite")
+        return variance < self.variance_threshold and mean > self.min_survival_for_annealing
 
-        # DEFENSIVE: Only anneal if BOTH low variance AND good performance
-        # Low variance + low survival = "consistently failing" (NOT ready to anneal)
-        # Low variance + high survival = "consistently succeeding" (ready to anneal)
-        return variance < self.variance_threshold and mean_survival > self.min_survival_for_annealing
+    def should_anneal(self) -> bool:
+        """Preserve the variance estimator, threshold and minimum ten survivals."""
+        return self._history_decision(self.survival_history)
 
     def anneal_weight(self) -> None:
         """Reduce intrinsic weight via exponential decay."""
@@ -191,36 +256,60 @@ class AdaptiveIntrinsicExploration(ExplorationStrategy):
         self.rnd.decay_epsilon()
 
     def checkpoint_state(self) -> dict[str, Any]:
-        """Return serializable state for checkpoint saving.
+        """Current native snapshot with independent nested tensors and history."""
+        return deepcopy(
+            {
+                "schema": "adaptive-intrinsic-state-v2",
+                "rnd_state": self.rnd.checkpoint_state(),
+                **self._config(),
+                "current_intrinsic_weight": self.current_intrinsic_weight,
+                "min_survival_for_annealing": self.min_survival_for_annealing,
+                "survival_history": self.survival_history,
+            }
+        )
 
-        Returns:
-            Dict with RND state, intrinsic weight, and survival history
-        """
-        return {
-            "rnd_state": self.rnd.checkpoint_state(),
-            "current_intrinsic_weight": self.current_intrinsic_weight,
-            "min_intrinsic_weight": self.min_intrinsic_weight,
-            "variance_threshold": self.variance_threshold,
-            "min_survival_fraction": self.min_survival_fraction,
-            "max_episode_length": self.max_episode_length,
-            "survival_window": self.survival_window,
-            "decay_rate": self.decay_rate,
-            "survival_history": self.survival_history,
-        }
+    def validate_state(self, state: dict[str, Any]) -> None:
+        self.prepare_state(state)
+
+    def prepare_state(self, state: dict[str, Any]) -> _PreparedAdaptive:
+        """Validate all outer semantics before preparing nested learned state."""
+        try:
+            state = deepcopy(state)
+            if (
+                not isinstance(state, dict)
+                or state.keys() != self.checkpoint_state().keys()
+                or state["schema"] != "adaptive-intrinsic-state-v2"
+            ):
+                raise ValueError("Adaptive requires complete current native state")
+            config = {name: state[name] for name in self._config()}
+            self._validate_config(config)
+            if config != self._config():
+                raise ValueError("Adaptive checkpoint configuration differs from destination")
+            threshold = state["min_survival_for_annealing"]
+            if type(threshold) is not int or threshold != int(config["min_survival_fraction"] * config["max_episode_length"]):
+                raise ValueError("Adaptive derived survival threshold is inconsistent")
+            weight = state["current_intrinsic_weight"]
+            if (
+                isinstance(weight, bool)
+                or not isinstance(weight, (int, float))
+                or not math.isfinite(weight)
+                or not self.min_intrinsic_weight <= weight <= self.initial_intrinsic_weight
+            ):
+                raise ValueError("Adaptive current weight is outside configured bounds")
+            self._history_decision(state["survival_history"])
+            candidate = deepcopy(self)
+            candidate.rnd.load_state(state["rnd_state"])
+            candidate.current_intrinsic_weight = weight
+            candidate.survival_history = state["survival_history"]
+            return _PreparedAdaptive(self, candidate.__dict__, False)
+        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
+            raise ValueError("Adaptive checkpoint is malformed") from error
+
+    def install_state(self, prepared: _PreparedAdaptive) -> None:
+        if type(prepared) is not _PreparedAdaptive or prepared.owner is not self or prepared.consumed:
+            raise ValueError("Adaptive prepared state belongs to another destination or was consumed")
+        prepared.consumed = True
+        self.__dict__ = prepared.attributes
 
     def load_state(self, state: dict[str, Any]) -> None:
-        """Restore from checkpoint.
-
-        Args:
-            state: Dict from checkpoint_state()
-        """
-        self.rnd.load_state(state["rnd_state"])
-        self.current_intrinsic_weight = state["current_intrinsic_weight"]
-        self.min_intrinsic_weight = state["min_intrinsic_weight"]
-        self.variance_threshold = state["variance_threshold"]
-        self.survival_window = state["survival_window"]
-        self.decay_rate = state["decay_rate"]
-        self.min_survival_fraction = state["min_survival_fraction"]
-        self.max_episode_length = state["max_episode_length"]
-        self.min_survival_for_annealing = int(self.min_survival_fraction * self.max_episode_length)
-        self.survival_history = state["survival_history"]
+        self.install_state(self.prepare_state(state))
diff --git a/src/townlet/exploration/icm.py b/src/townlet/exploration/icm.py
index 2517936b..66e68605 100644
--- a/src/townlet/exploration/icm.py
+++ b/src/townlet/exploration/icm.py
@@ -4,8 +4,10 @@ from __future__ import annotations
 
 import math
 from collections import deque
+from contextlib import nullcontext
 from copy import deepcopy
-from typing import Any, cast
+from dataclasses import dataclass
+from typing import Any, Literal, cast
 
 import torch
 from torch import Tensor, nn
@@ -13,15 +15,24 @@ from torch.nn import functional
 
 from townlet.config.exploration_policy import ExplorationServiceReceipt, IntrinsicTransitionContext, ResolvedExplorationPolicy
 from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
+from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState
 
 _COUNTERS = ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "mandatory_service_updates")
 
 
+@dataclass
+class _PreparedICM:
+    owner: object
+    attributes: dict[str, Any]
+    consumed: bool
+
+
 def _number(value: Any, name: str, integer: bool, minimum: float) -> None:
-    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
+    if integer:
+        if type(value) is not int or value < minimum:
+            raise ValueError(f"ICM {name} requires an exact integer >= {minimum}")
+    elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
         raise ValueError(f"ICM {name} requires a finite number >= {minimum}")
-    if integer and not isinstance(value, int):
-        raise ValueError(f"ICM {name} requires an integer")
 
 
 def _owned(value: Any) -> Any:
@@ -57,7 +68,13 @@ class ICMExploration(EpsilonGreedyExploration):
         training_batch_size: int,
         max_pending_transitions: int,
         device: torch.device | str,
+        rng: WorldRNGState | None,
+        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
     ):
+        ServiceClock(service_clock_unit, 0)
+        if rng is not None and not isinstance(rng, WorldRNGState):
+            raise ValueError("ICM rng must be an actual world RNG owner or explicit None")
+        self._service_clock_unit = service_clock_unit
         if not isinstance(policy, ResolvedExplorationPolicy) or policy.strategy != "icm":
             raise ValueError("ICM requires a resolved icm policy")
         parameters = {
@@ -76,6 +93,9 @@ class ICMExploration(EpsilonGreedyExploration):
             raise ValueError("ICM requires positive learning_rate and capacity >= training_batch_size")
         if parameters != dict(policy.provider_parameters):
             raise ValueError("ICM constructor parameters disagree with the selected policy")
+        device = torch.device(device)
+        if device.type not in {"cpu", "cuda"}:
+            raise ValueError("ICM requires a concrete CPU or CUDA destination")
         super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)
         self.policy = policy
         self.obs_dim, self.action_dim = obs_dim, action_dim
@@ -83,9 +103,13 @@ class ICMExploration(EpsilonGreedyExploration):
         self.learning_rate = float(learning_rate)
         self.inverse_weight, self.forward_weight = float(inverse_weight), float(forward_weight)
         self.training_batch_size, self.max_pending_transitions = training_batch_size, max_pending_transitions
-        self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
-        self.inverse_model = nn.Sequential(nn.Linear(2 * feature_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, action_dim))
-        self.forward_model = nn.Sequential(nn.Linear(feature_dim + action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
+        with rng.activate("model_init") if rng is not None else nullcontext():
+            self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
+            self.inverse_model = nn.Sequential(nn.Linear(2 * feature_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, action_dim))
+        with rng.activate("predictor") if rng is not None else nullcontext():
+            self.forward_model = nn.Sequential(
+                nn.Linear(feature_dim + action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim)
+            )
         for module in (self.encoder, self.inverse_model, self.forward_model):
             module.to(device=device, dtype=torch.float32)
         self.device = next(self.encoder.parameters()).device
@@ -94,8 +118,12 @@ class ICMExploration(EpsilonGreedyExploration):
         self._pending: deque[dict[str, Any]] = deque()
         self._counters = dict.fromkeys(_COUNTERS, 0)
         self._last_loss = 0.0
-        self._service_tick: int | None = None
-        self._ordinary_updates_this_tick = 0
+        self._service_position: int | None = 0 if service_clock_unit == "world_eligible_admission" else None
+        self._ordinary_updates_at_position = 0
+
+    @property
+    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
+        return self._service_clock_unit
 
     def _parameters(self) -> list[nn.Parameter]:
         return [parameter for module in (self.encoder, self.inverse_model, self.forward_model) for parameter in module.parameters()]
@@ -104,6 +132,10 @@ class ICMExploration(EpsilonGreedyExploration):
         if not isinstance(context, IntrinsicTransitionContext):
             raise ValueError("ICM requires actual predecessor/actions/successor IntrinsicTransitionContext")
         predecessor, actions, successor, active = context.predecessor, context.actions, context.successor, context.active_on_entry
+        if any(
+            value.layout != torch.strided or value.device.type not in {"cpu", "cuda"} for value in (predecessor, actions, successor, active)
+        ):
+            raise ValueError("ICM context requires concrete dense CPU/CUDA tensors")
         if predecessor.ndim != 2 or predecessor.shape[1] != self.obs_dim or successor.shape != predecessor.shape:
             raise ValueError("ICM transition observations require [N, obs_dim] geometry")
         if (
@@ -167,16 +199,49 @@ class ICMExploration(EpsilonGreedyExploration):
         if mandatory:
             self._counters["mandatory_service_updates"] += 1
         else:
-            self._ordinary_updates_this_tick += 1
+            self._ordinary_updates_at_position += 1
 
     def admit_and_service(self, context: IntrinsicTransitionContext) -> ExplorationServiceReceipt:
+        """Current shared grouped service with explicit context vector cadence."""
+        if self.service_clock_unit != "vector_tick":
+            raise ValueError("Private ICM requires explicit eligible-admission service")
+        if not isinstance(context, IntrinsicTransitionContext):
+            raise ValueError("ICM requires an actual transition context")
+        return self.admit_and_service_at(context, clock=ServiceClock("vector_tick", context.vector_tick))
+
+    def admit_and_service_at(self, context: IntrinsicTransitionContext, *, clock: ServiceClock) -> ExplorationServiceReceipt:
         predecessor, actions, successor, active = self._context(context)
-        if self._service_tick is not None and context.vector_tick < self._service_tick:
-            raise ValueError("ICM service vector_tick must be monotonic")
+        if type(clock) is not ServiceClock:
+            raise ValueError("ICM service requires ServiceClock")
+        ServiceClock(clock.unit, clock.position)
+        ServiceClock("vector_tick", context.vector_tick)
+        if clock.unit != self.service_clock_unit:
+            raise ValueError("ICM service clock differs from selected unit")
+        indices = active.nonzero(as_tuple=False).flatten().tolist()
+        previous = self._service_position
+        if clock.unit == "vector_tick":
+            if clock.position != context.vector_tick or (previous is not None and clock.position < previous):
+                raise ValueError("ICM shared clock must match context and not regress")
+        elif previous is None or clock.position != previous + len(indices):
+            raise ValueError("ICM private clock delta must equal actual eligible admissions")
         before = dict(self._counters)
-        if context.vector_tick != self._service_tick:
-            self._service_tick, self._ordinary_updates_this_tick = context.vector_tick, 0
-        for index in active.nonzero(as_tuple=False).flatten().tolist():
+        if clock.unit == "vector_tick":
+            self._admit_rows(predecessor, actions, successor, indices, clock.position)
+        else:
+            assert previous is not None
+            for offset, index in enumerate(indices):
+                self._admit_rows(predecessor, actions, successor, [index], previous + offset + 1)
+        return ExplorationServiceReceipt(
+            provider="icm",
+            **{name: self._counters[name] - before[name] for name in _COUNTERS},
+            pending_rows=len(self._pending),
+            last_loss=self._last_loss,
+        )
+
+    def _admit_rows(self, predecessor: Tensor, actions: Tensor, successor: Tensor, indices: list[int], position: int) -> None:
+        if position != self._service_position:
+            self._service_position, self._ordinary_updates_at_position = position, 0
+        for index in indices:
             if len(self._pending) == self.max_pending_transitions:
                 if self.policy.overflow_policy == "service_before_admit":
                     self._train_batch(True)
@@ -192,15 +257,9 @@ class ICMExploration(EpsilonGreedyExploration):
             )
             self._counters["admitted_rows"] += 1
         while len(self._pending) >= self.training_batch_size:
-            if self.policy.service_mode == "paced_fifo" and self._ordinary_updates_this_tick >= self.policy.max_updates_per_tick:
+            if self.policy.service_mode == "paced_fifo" and self._ordinary_updates_at_position >= self.policy.max_updates_per_tick:
                 break
             self._train_batch(False)
-        return ExplorationServiceReceipt(
-            provider="icm",
-            **{name: self._counters[name] - before[name] for name in _COUNTERS},
-            pending_rows=len(self._pending),
-            last_loss=self._last_loss,
-        )
 
     def _config(self) -> dict[str, Any]:
         return {
@@ -221,7 +280,7 @@ class ICMExploration(EpsilonGreedyExploration):
             dict[str, Any],
             _owned(
                 {
-                    "schema": "icm-state-v1",
+                    "schema": "icm-state-v2",
                     "policy": self.policy.to_dict(),
                     "policy_identity": self.policy.policy_identity,
                     "config": self._config(),
@@ -235,8 +294,9 @@ class ICMExploration(EpsilonGreedyExploration):
                     "pending": list(self._pending),
                     "counters": self._counters,
                     "last_loss": self._last_loss,
-                    "service_tick": self._service_tick,
-                    "ordinary_updates_this_tick": self._ordinary_updates_this_tick,
+                    "service_clock_unit": self.service_clock_unit,
+                    "service_position": self._service_position,
+                    "ordinary_updates_at_position": self._ordinary_updates_at_position,
                 }
             ),
         )
@@ -262,12 +322,17 @@ class ICMExploration(EpsilonGreedyExploration):
         expected = self.optimizer.state_dict()["param_groups"]
         if not isinstance(payload, dict) or set(payload) != {"state", "param_groups"} or payload["param_groups"] != expected:
             raise ValueError("ICM optimizer parameter groups disagree with selected configuration")
+        for group, reference in zip(payload["param_groups"], expected, strict=True):
+            if any(type(group[key]) is not type(value) for key, value in reference.items()):
+                raise ValueError("ICM optimizer group field types disagree with selected configuration")
+            if any(type(value) is not int for value in group["params"]) or any(type(value) is not float for value in group["betas"]):
+                raise ValueError("ICM optimizer parameter IDs/betas require exact native types")
         states = payload["state"]
         identifiers = expected[0]["params"]
         required: set[int] = set()
         if updates:
             required = set(identifiers)
-        if not isinstance(states, dict) or set(states) != required:
+        if not isinstance(states, dict) or set(states) != required or any(type(key) is not int for key in states):
             raise ValueError("ICM optimizer state does not match successful update count")
         for identifier, parameter in zip(identifiers, parameters, strict=True):
             if not updates:
@@ -299,11 +364,17 @@ class ICMExploration(EpsilonGreedyExploration):
         optimizer.load_state_dict(_owned(payload))
         return optimizer
 
-    def load_state(self, state: dict[str, Any]) -> None:
-        """Validate all transported state off-side before replacing any live state."""
-        if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "icm-state-v1":
-            raise ValueError("ICM requires complete icm-state-v1 checkpoint")
+    def validate_state(self, state: dict[str, Any]) -> None:
+        self.prepare_state(state)
+
+    def prepare_state(self, state: dict[str, Any]) -> _PreparedICM:
+        """Validate and own every transported field before any live installation."""
         try:
+            state = _owned(state)
+            if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "icm-state-v2":
+                raise ValueError("ICM requires complete icm-state-v2 checkpoint")
+            if not isinstance(state["policy"], dict) or state["policy"].keys() != self.policy.to_dict().keys():
+                raise ValueError("ICM checkpoint requires current complete policy fields")
             policy = ResolvedExplorationPolicy.from_dict(state["policy"])
             if policy.policy_identity != state["policy_identity"] or policy.policy_identity != self.policy.policy_identity:
                 raise ValueError("ICM checkpoint selected policy identity disagrees")
@@ -316,7 +387,8 @@ class ICMExploration(EpsilonGreedyExploration):
                     raise ValueError(f"ICM checkpoint configuration disagrees at {name}")
             if not isinstance(config["device"], str):
                 raise ValueError("ICM checkpoint source device requires a device string")
-            torch.device(config["device"])
+            if torch.device(config["device"]).type not in {"cpu", "cuda"}:
+                raise ValueError("ICM checkpoint source device must be CPU or CUDA")
             counters = state["counters"]
             if not isinstance(counters, dict) or set(counters) != set(_COUNTERS):
                 raise ValueError("ICM checkpoint counters are incomplete")
@@ -345,13 +417,18 @@ class ICMExploration(EpsilonGreedyExploration):
                 raise ValueError("ICM checkpoint service counters disagree")
             if counters["admitted_rows"] != counters["consumed_rows"] + counters["dropped_rows"] + len(pending):
                 raise ValueError("ICM checkpoint transition conservation failed")
-            tick, budget = state["service_tick"], state["ordinary_updates_this_tick"]
+            if type(state["service_clock_unit"]) is not str or state["service_clock_unit"] != self.service_clock_unit:
+                raise ValueError("ICM checkpoint service unit differs from destination")
+            tick, budget = state["service_position"], state["ordinary_updates_at_position"]
             _number(budget, "ordinary service budget", True, 0)
             if tick is None:
                 if counters["admitted_rows"] or updates or budget:
                     raise ValueError("ICM unstarted service has nonempty counters")
             else:
-                _number(tick, "service_tick", True, 0)
+                _number(tick, "service_position", True, 0)
+            if self.service_clock_unit == "world_eligible_admission":
+                if tick != counters["admitted_rows"] or (tick == 0 and (updates or budget)):
+                    raise ValueError("ICM private service position disagrees with admissions")
             if budget > updates - counters["mandatory_service_updates"] or (
                 policy.service_mode == "paced_fifo" and budget > policy.max_updates_per_tick
             ):
@@ -373,8 +450,19 @@ class ICMExploration(EpsilonGreedyExploration):
             owned_pending = deque(_owned(pending))
         except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
             raise ValueError("ICM checkpoint is malformed") from error
-        self.encoder, self.inverse_model, self.forward_model, self.optimizer = encoder, inverse, forward, optimizer
-        self.policy, self._source_device = policy, config["device"]
-        self.epsilon, self.epsilon_decay, self.epsilon_min = state["epsilon"], state["epsilon_decay"], state["epsilon_min"]
-        self._pending, self._counters, self._last_loss = owned_pending, dict(counters), float(state["last_loss"])
-        self._service_tick, self._ordinary_updates_this_tick = tick, budget
+        candidate = deepcopy(self)
+        candidate.encoder, candidate.inverse_model, candidate.forward_model, candidate.optimizer = encoder, inverse, forward, optimizer
+        candidate.policy, candidate._source_device = policy, config["device"]
+        candidate.epsilon, candidate.epsilon_decay, candidate.epsilon_min = state["epsilon"], state["epsilon_decay"], state["epsilon_min"]
+        candidate._pending, candidate._counters, candidate._last_loss = owned_pending, dict(counters), float(state["last_loss"])
+        candidate._service_position, candidate._ordinary_updates_at_position = tick, budget
+        return _PreparedICM(self, candidate.__dict__, False)
+
+    def install_state(self, prepared: _PreparedICM) -> None:
+        if type(prepared) is not _PreparedICM or prepared.owner is not self or prepared.consumed:
+            raise ValueError("ICM prepared state belongs to another destination or was consumed")
+        prepared.consumed = True
+        self.__dict__ = prepared.attributes
+
+    def load_state(self, state: dict[str, Any]) -> None:
+        self.install_state(self.prepare_state(state))
diff --git a/src/townlet/exploration/rnd.py b/src/townlet/exploration/rnd.py
index cb35be9d..eca3bead 100644
--- a/src/townlet/exploration/rnd.py
+++ b/src/townlet/exploration/rnd.py
@@ -3,9 +3,10 @@
 from __future__ import annotations
 
 import math
+from contextlib import nullcontext
 from copy import deepcopy
 from dataclasses import dataclass
-from typing import Any, cast
+from typing import Any, Literal, cast
 
 import numpy as np
 import torch
@@ -15,6 +16,7 @@ import torch.nn.functional as F  # noqa: N812
 from townlet.config.bac_options import RNDOptions
 from townlet.exploration.action_selection import epsilon_greedy_action_selection
 from townlet.exploration.base import ExplorationStrategy
+from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState
 from townlet.training.state import BatchedAgentState
 
 
@@ -47,6 +49,13 @@ class PredictorServiceReceipt:
     overflow_optimizer_updates: int
 
 
+@dataclass
+class _PreparedRND:
+    owner: object
+    attributes: dict[str, Any]
+    consumed: bool
+
+
 class RunningMeanStd:
     """Running mean and standard deviation tracker.
 
@@ -149,6 +158,9 @@ class RNDExploration(ExplorationStrategy):
         epsilon_min: float = 0.01,
         epsilon_decay: float = 0.995,
         device: torch.device = torch.device("cpu"),
+        *,
+        rng: WorldRNGState | None,
+        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
     ):
         """Initialize RND with fixed and predictor networks.
 
@@ -162,8 +174,26 @@ class RNDExploration(ExplorationStrategy):
             epsilon_decay: Epsilon decay rate
             device: Device for tensors
         """
-        if type(training_batch_size) is not int or training_batch_size <= 0:
-            raise ValueError("RND training_batch_size must be a positive integer")
+        ServiceClock(service_clock_unit, 0)
+        if rng is not None and not isinstance(rng, WorldRNGState):
+            raise ValueError("RND rng must be an actual world RNG owner or explicit None")
+        for name, value in (("obs_dim", obs_dim), ("embed_dim", embed_dim), ("training_batch_size", training_batch_size)):
+            if type(value) is not int or value <= 0:
+                raise ValueError(f"RND {name} must be a positive integer")
+        for name, value in (
+            ("learning_rate", learning_rate),
+            ("epsilon_start", epsilon_start),
+            ("epsilon_min", epsilon_min),
+            ("epsilon_decay", epsilon_decay),
+        ):
+            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
+                raise ValueError(f"RND {name} must be finite numeric configuration")
+        if learning_rate < 0 or not 0 <= epsilon_min <= epsilon_start <= 1 or not 0 <= epsilon_decay <= 1:
+            raise ValueError("RND learning rate/epsilon configuration is invalid")
+        device = torch.device(device)
+        if device.type not in {"cpu", "cuda"}:
+            raise ValueError("RND requires a concrete CPU or CUDA destination")
+        self._service_clock_unit = service_clock_unit
         self.obs_dim = obs_dim
         self.embed_dim = embed_dim
         self.training_batch_size = training_batch_size
@@ -175,12 +205,14 @@ class RNDExploration(ExplorationStrategy):
         self.epsilon_decay = epsilon_decay
 
         # Fixed network (random, frozen)
-        self.fixed_network = RNDNetwork(obs_dim, embed_dim).to(device)
+        with rng.activate("target") if rng is not None else nullcontext():
+            self.fixed_network = RNDNetwork(obs_dim, embed_dim).to(device)
         for param in self.fixed_network.parameters():
             param.requires_grad = False
 
         # Predictor network (trained to match fixed)
-        self.predictor_network = RNDNetwork(obs_dim, embed_dim).to(device)
+        with rng.activate("predictor") if rng is not None else nullcontext():
+            self.predictor_network = RNDNetwork(obs_dim, embed_dim).to(device)
 
         # Optimizer for predictor
         self.optimizer = torch.optim.Adam(self.predictor_network.parameters(), lr=learning_rate)
@@ -193,12 +225,20 @@ class RNDExploration(ExplorationStrategy):
         self._consumed_rows = 0
         self._dropped_rows = 0
         self._optimizer_updates = 0
-        self._vector_tick: int | None = None
-        self._paced_updates_this_tick = 0
+        self._service_position: int | None = 0 if service_clock_unit == "world_eligible_admission" else None
+        self._ordinary_updates_at_position = 0
 
         # Running statistics for intrinsic reward normalization
         self.reward_rms = RunningMeanStd()
 
+    @property
+    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
+        return self._service_clock_unit
+
+    def _require_shared(self) -> None:
+        if self.service_clock_unit != "vector_tick":
+            raise ValueError("Private RND learning requires explicit eligible-admission clock")
+
     def select_actions(
         self,
         q_values: torch.Tensor,
@@ -235,12 +275,21 @@ class RNDExploration(ExplorationStrategy):
         Returns:
             [batch] normalized intrinsic rewards
         """
+        self._validate_observations(observations)
+        if type(update_stats) is not bool:
+            raise ValueError("RND update_stats requires bool")
+        if observations.device != next(self.predictor_network.parameters()).device:
+            raise ValueError("RND reward observations must match the provider device")
+        if len(observations) == 0:
+            return torch.empty(0, device=observations.device, dtype=observations.dtype)
         with torch.no_grad():
             target_features: torch.Tensor = self.fixed_network(observations)
             predicted_features: torch.Tensor = self.predictor_network(observations)
             # MSE per sample (high error = novel = high reward)
             mse_per_sample = ((target_features - predicted_features) ** 2).mean(dim=1)
 
+            if not torch.isfinite(mse_per_sample).all().item():
+                raise ValueError("RND produced nonfinite novelty")
             # Optionally update running statistics (only during training rollouts)
             if update_stats:
                 mse_numpy = mse_per_sample.cpu().numpy()
@@ -258,27 +307,34 @@ class RNDExploration(ExplorationStrategy):
         Args:
             batch: Experience batch with 'observations' key
         """
+        self._require_shared()
         if "observations" not in batch:
             return
-
         observations = batch["observations"]
-
+        self._validate_observations(observations)
+        self._validate_buffer()
         if self.service_options is not None:
-            # The unclocked compatibility API denotes the next local service tick.
-            if self._vector_tick is not None:
-                self.step_counter = max(self.step_counter, self._vector_tick + 1)
-            self.admit_and_service(observations, vector_tick=self.step_counter)
-            self.step_counter += 1
+            prospective = self.step_counter
+            if self._service_position is not None:
+                prospective = max(prospective, self._service_position + 1)
+            self.admit_and_service(observations, vector_tick=prospective)
+            self.step_counter = prospective + 1
             return
-        # Explicit legacy adapter: one minibatch per call, retaining its old API.
-        self._validate_observations(observations)
         self.obs_buffer.extend(row.detach().clone() for row in observations)
         self._admitted_rows += len(observations)
         self.update_predictor()
 
+    def _validate_buffer(self) -> None:
+        for row in self.obs_buffer:
+            if not isinstance(row, torch.Tensor) or row.ndim != 1:
+                raise ValueError("RND pending observations require owned observation rows")
+            self._validate_observations(row.unsqueeze(0))
+
     def _validate_observations(self, observations: torch.Tensor) -> None:
         if (
             not isinstance(observations, torch.Tensor)
+            or observations.layout != torch.strided
+            or observations.device.type not in {"cpu", "cuda"}
             or observations.ndim != 2
             or observations.shape[1] != self.obs_dim
             or observations.dtype != next(self.predictor_network.parameters()).dtype
@@ -289,6 +345,8 @@ class RNDExploration(ExplorationStrategy):
                 raise ValueError("RND observations must be finite floating rows with matching width and dtype")
 
     def _validated_options(self, options: RNDOptions) -> RNDOptions:
+        if not isinstance(options, RNDOptions):
+            raise ValueError("RND service requires resolved RNDOptions")
         checked = RNDOptions.model_validate(options.model_dump())
         if any(value is None for value in checked.model_dump().values()):
             raise ValueError("RND service requires centrally resolved, explicit options")
@@ -324,22 +382,49 @@ class RNDExploration(ExplorationStrategy):
         )
 
     def admit_and_service(self, observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt:
-        """Admit only caller-selected eligible predecessor rows in bounded chunks.
+        """Current shared grouped admission; equal ticks share ordinary budget."""
+        self._require_shared()
+        return self.admit_and_service_at(observations, clock=ServiceClock("vector_tick", vector_tick))
 
-        The caller owns eligibility and local clocks. Repeated calls at the same
-        tick share the ordinary paced budget. Lossless mandatory overflow service
-        may exceed that budget and is reported separately. Each loop either admits,
-        consumes, or explicitly drops rows, including oversized input tensors.
-        """
+    def admit_and_service_at(self, observations: torch.Tensor, *, clock: ServiceClock) -> PredictorServiceReceipt:
+        """Validate the entire call before servicing explicit shared/private clocks."""
         self._validate_observations(observations)
+        self._validate_buffer()
+        if self.service_options is None:
+            raise ValueError("Configure resolved RND service options before admission")
+        self._validated_options(self.service_options)
+        if type(clock) is not ServiceClock:
+            raise ValueError("RND service requires ServiceClock")
+        ServiceClock(clock.unit, clock.position)
+        if clock.unit != self.service_clock_unit:
+            raise ValueError("RND service clock unit differs from selected unit")
+        previous = self._service_position
+        if clock.unit == "vector_tick":
+            if previous is not None and clock.position < previous:
+                raise ValueError("RND vector clock must not regress")
+            return self._admit_service_rows(observations, clock.position)
+        assert previous is not None
+        if clock.position != previous + len(observations):
+            raise ValueError("RND private clock delta must equal actual eligible admissions")
+        receipts = [self._admit_service_rows(row.unsqueeze(0), previous + index + 1) for index, row in enumerate(observations)]
+        losses = [receipt.last_loss for receipt in receipts if receipt.last_loss is not None]
+        return PredictorServiceReceipt(
+            admitted_rows=len(observations),
+            consumed_rows=sum(item.consumed_rows for item in receipts),
+            dropped_rows=sum(item.dropped_rows for item in receipts),
+            pending_rows=len(self.obs_buffer),
+            optimizer_updates=sum(item.optimizer_updates for item in receipts),
+            last_loss=losses[-1] if losses else None,
+            paced_optimizer_updates=sum(item.paced_optimizer_updates for item in receipts),
+            overflow_optimizer_updates=sum(item.overflow_optimizer_updates for item in receipts),
+        )
+
+    def _admit_service_rows(self, observations: torch.Tensor, position: int) -> PredictorServiceReceipt:
         options = self.service_options
-        if options is None:
-            raise ValueError("configure_service with resolved options before bounded RND admission")
-        if type(vector_tick) is not int or vector_tick < 0 or (self._vector_tick is not None and vector_tick < self._vector_tick):
-            raise ValueError("RND vector_tick must be a nonnegative monotone integer")
-        if vector_tick != self._vector_tick:
-            self._vector_tick = vector_tick
-            self._paced_updates_this_tick = 0
+        assert options is not None
+        if position != self._service_position:
+            self._service_position = position
+            self._ordinary_updates_at_position = 0
         capacity = options.max_pending_rows
         budget = options.max_updates_per_tick
         assert capacity is not None and budget is not None
@@ -349,17 +434,17 @@ class RNDExploration(ExplorationStrategy):
         offset = 0
         while True:
             while len(self.obs_buffer) >= self.training_batch_size:
-                if options.service_mode == "paced_fifo" and self._paced_updates_this_tick >= budget:
+                if options.service_mode == "paced_fifo" and self._ordinary_updates_at_position >= budget:
                     break
-                last_loss = self.update_predictor()
+                last_loss = self._update_predictor()
                 paced += 1
-                self._paced_updates_this_tick += 1
+                self._ordinary_updates_at_position += 1
             if offset == len(observations):
                 break
             room = capacity - len(self.obs_buffer)
             if room == 0:
                 if options.overflow_policy == "service_before_admit":
-                    last_loss = self.update_predictor()
+                    last_loss = self._update_predictor()
                     overflow += 1
                     continue
                 count = min(len(observations) - offset, capacity)
@@ -394,6 +479,11 @@ class RNDExploration(ExplorationStrategy):
         Returns:
             Prediction loss (for logging)
         """
+        self._require_shared()
+        self._validate_buffer()
+        return self._update_predictor()
+
+    def _update_predictor(self) -> float:
         # Direct callers own the public buffer and may admit rows without a tick.
         self._admitted_rows = max(self._admitted_rows, self._consumed_rows + self._dropped_rows + len(self.obs_buffer))
         if len(self.obs_buffer) < self.training_batch_size:
@@ -407,9 +497,16 @@ class RNDExploration(ExplorationStrategy):
         predicted = self.predictor_network(obs_batch)
         loss = F.mse_loss(predicted, target)
 
+        if not torch.isfinite(loss).item():
+            raise ValueError("RND objective is nonfinite")
         # Gradient step
         self.optimizer.zero_grad()
         loss.backward()
+        if any(
+            parameter.grad is not None and not torch.isfinite(parameter.grad).all().item()
+            for parameter in self.predictor_network.parameters()
+        ):
+            raise ValueError("RND objective produced nonfinite gradients")
         self.optimizer.step()
         del self.obs_buffer[: self.training_batch_size]
         self._consumed_rows += self.training_batch_size
@@ -446,6 +543,7 @@ class RNDExploration(ExplorationStrategy):
     def checkpoint_state(self) -> dict[str, Any]:
         """Owned snapshot, including FIFO order and clocks for learned-state resume."""
         state = self.available_state()
+        state["schema"] = "rnd-state-v2"
         pending = torch.empty((0, self.obs_dim), device=self.device)
         if self.obs_buffer:
             pending = torch.stack(self.obs_buffer).detach().clone()
@@ -456,7 +554,7 @@ class RNDExploration(ExplorationStrategy):
         if self.service_options is not None:
             options = self.service_options.model_dump()
         state["predictor_service"] = {
-            "version": 1,
+            "version": 2,
             "training_batch_size": self.training_batch_size,
             "options": options,
             "pending_observations": pending,
@@ -465,10 +563,11 @@ class RNDExploration(ExplorationStrategy):
             "dropped_rows": self._dropped_rows,
             "optimizer_updates": self._optimizer_updates,
             # Capture the trusted live clock, including public manual optimizer
-            # steps and historical imports. Restore validates this saved offset.
+            # steps outside recorded service updates. Restore validates this saved offset.
             "optimizer_step_offset": self._optimizer_step(self.optimizer) - self._optimizer_updates,
-            "vector_tick": self._vector_tick,
-            "paced_updates_this_tick": self._paced_updates_this_tick,
+            "service_clock_unit": self.service_clock_unit,
+            "service_position": self._service_position,
+            "ordinary_updates_at_position": self._ordinary_updates_at_position,
             "step_counter": self.step_counter,
         }
         return state
@@ -500,7 +599,11 @@ class RNDExploration(ExplorationStrategy):
         for group, reference in zip(groups, expected, strict=True):
             if not isinstance(group, dict) or set(group) != set(reference):
                 raise ValueError("RND checkpoint optimizer group fields mismatch")
-            if not isinstance(group["params"], list) or any(type(index) is not int for index in group["params"]):
+            if (
+                not isinstance(group["params"], list)
+                or any(type(index) is not int for index in group["params"])
+                or group["params"] != reference["params"]
+            ):
                 raise ValueError("RND checkpoint optimizer parameter IDs invalid")
             betas = group["betas"]
             if not isinstance(betas, (tuple, list)) or len(betas) != 2:
@@ -525,13 +628,20 @@ class RNDExploration(ExplorationStrategy):
         if set(state) != expected_keys:
             raise ValueError("RND available-state fields mismatch")
         self._finite_tree(state)
-        if state["obs_dim"] != self.obs_dim or state["embed_dim"] != self.embed_dim:
+        if (
+            type(state["obs_dim"]) is not int
+            or type(state["embed_dim"]) is not int
+            or state["obs_dim"] != self.obs_dim
+            or state["embed_dim"] != self.embed_dim
+        ):
             raise ValueError("RND checkpoint network geometry mismatch")
         for key in ("epsilon", "epsilon_min", "epsilon_decay", "reward_rms_mean", "reward_rms_var", "reward_rms_count"):
             if isinstance(state[key], bool) or not isinstance(state[key], (int, float, np.floating)):
                 raise ValueError(f"RND checkpoint {key} must be a finite scalar")
         if any(not 0 <= state[key] <= 1 for key in ("epsilon", "epsilon_min", "epsilon_decay")):
             raise ValueError("RND checkpoint epsilon settings outside [0,1]")
+        if state["epsilon"] < state["epsilon_min"]:
+            raise ValueError("RND checkpoint epsilon is below its floor")
         if state["reward_rms_var"] < 0 or state["reward_rms_count"] <= 0:
             raise ValueError("RND checkpoint normalization variance/count invalid")
         fixed, predictor, optimizer = deepcopy((self.fixed_network, self.predictor_network, self.optimizer))
@@ -572,7 +682,7 @@ class RNDExploration(ExplorationStrategy):
                     if not isinstance(tensor, torch.Tensor):
                         raise ValueError("RND checkpoint optimizer moments must be tensors")
                     if name == "step":
-                        if tensor.numel() != 1 or tensor.item() < 0 or tensor.item() != int(tensor.item()):
+                        if tensor.shape != () or not tensor.is_floating_point() or tensor.item() < 0 or tensor.item() != int(tensor.item()):
                             raise ValueError("RND checkpoint optimizer step invalid")
                         steps.add(int(tensor.item()))
                     elif tensor.shape != parameter.shape or tensor.dtype != parameter.dtype:
@@ -602,45 +712,43 @@ class RNDExploration(ExplorationStrategy):
             state["reward_rms_count"],
         )
 
-    def load_available_state(self, state: dict[str, Any]) -> None:
-        """Explicit historical import of available state only; never invent old tails/RNG.
-
-        Preserves destination pending work/clocks, matching the historical API.
-        Source pending work and RNG are unavailable; this is not tail continuation.
-        """
-        prepared = self._prepare_available_state(state)
-        self._install_available_state(state, prepared)
-
     def validate_state(self, state: dict[str, Any]) -> None:
-        """Validate a full continuation payload without modifying live state."""
-        if "predictor_service" not in state:
-            self._prepare_available_state(state)
-        else:
-            self._prepare_state(state)
+        """Pure complete current-native validation, with no live installation."""
+        self.prepare_state(state)
 
     def _prepare_state(self, state: dict[str, Any]) -> tuple[tuple[Any, Any, Any], list[torch.Tensor], dict[str, Any]]:
-        if "predictor_service" not in state:
-            raise ValueError("RND continuation requires predictor_service; use load_available_state for historical imports")
-        available = {key: value for key, value in state.items() if key != "predictor_service"}
+        if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "rnd-state-v2":
+            raise ValueError("RND requires complete current rnd-state-v2 checkpoint")
+        available = {key: value for key, value in state.items() if key not in {"schema", "predictor_service"}}
         prepared = self._prepare_available_state(available)
         service = state["predictor_service"]
         if not isinstance(service, dict) or set(service) != set(self.checkpoint_state()["predictor_service"]):
             raise ValueError("RND predictor service checkpoint fields mismatch")
         if (
             type(service["version"]) is not int
-            or service["version"] != 1
+            or service["version"] != 2
             or type(service["training_batch_size"]) is not int
             or service["training_batch_size"] != self.training_batch_size
         ):
             raise ValueError("RND predictor service version/minibatch mismatch")
         options = None
         if service["options"] is not None:
-            options = self._validated_options(RNDOptions.model_validate(service["options"]))
+            expected_options = self.service_options.model_dump() if self.service_options is not None else {}
+            raw_options = service["options"]
+            if (
+                not isinstance(raw_options, dict)
+                or raw_options.keys() != expected_options.keys()
+                or any(
+                    type(value) is not type(expected_options[key]) or value != expected_options[key] for key, value in raw_options.items()
+                )
+            ):
+                raise ValueError("RND checkpoint requires exact selected service options")
+            options = self._validated_options(RNDOptions.model_validate(raw_options))
         if options != self.service_options:
             raise ValueError("RND checkpoint service policy differs from configured destination")
         pending = service["pending_observations"]
         self._validate_observations(pending)
-        for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "paced_updates_this_tick", "step_counter"):
+        for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "ordinary_updates_at_position", "step_counter"):
             if type(service[key]) is not int or service[key] < 0:
                 raise ValueError(f"RND service {key} must be a nonnegative integer")
         offset = service["optimizer_step_offset"]
@@ -648,42 +756,59 @@ class RNDExploration(ExplorationStrategy):
             raise ValueError("RND optimizer step offset must describe a nonnegative Adam clock")
         if self._optimizer_step(prepared[2]) != service["optimizer_updates"] + offset:
             raise ValueError("RND Adam history does not match versioned service optimizer updates")
-        tick = service["vector_tick"]
+        if type(service["service_clock_unit"]) is not str or service["service_clock_unit"] != self.service_clock_unit:
+            raise ValueError("RND checkpoint service unit differs from destination")
+        tick = service["service_position"]
         if tick is not None and (type(tick) is not int or tick < 0):
-            raise ValueError("RND service vector_tick invalid")
+            raise ValueError("RND service position invalid")
         if service["admitted_rows"] != service["consumed_rows"] + service["dropped_rows"] + len(pending):
             raise ValueError("RND service row accounting mismatch")
         if service["consumed_rows"] != service["optimizer_updates"] * self.training_batch_size:
             raise ValueError("RND service optimizer accounting mismatch")
-        if tick is None and service["paced_updates_this_tick"] != 0:
+        if self.service_clock_unit == "world_eligible_admission":
+            if options is None or tick != service["admitted_rows"] or service["step_counter"] != 0:
+                raise ValueError("RND private native clock/configuration disagrees with admissions")
+            if tick == 0 and (service["optimizer_updates"] or service["ordinary_updates_at_position"]):
+                raise ValueError("RND unstarted private service has work")
+        if tick is None and service["ordinary_updates_at_position"] != 0:
             raise ValueError("RND service pacing requires a tick")
-        if service["paced_updates_this_tick"] > service["optimizer_updates"]:
+        if service["ordinary_updates_at_position"] > service["optimizer_updates"]:
             raise ValueError("RND service paced updates exceed total optimizer updates")
         if options is not None:
             assert options.max_pending_rows is not None and options.max_updates_per_tick is not None
             if len(pending) > options.max_pending_rows:
                 raise ValueError("RND pending observations exceed capacity")
-            if options.service_mode == "paced_fifo" and service["paced_updates_this_tick"] > options.max_updates_per_tick:
+            if options.service_mode == "paced_fifo" and service["ordinary_updates_at_position"] > options.max_updates_per_tick:
                 raise ValueError("RND service paced budget exceeded")
             # The explicit direct one-minibatch API may leave complete batches;
             # occupancy admit_and_service drains these on its next invocation.
         pending_rows = [row.detach().to(self.device).clone() for row in pending]
         return prepared, pending_rows, service
 
+    def prepare_state(self, state: dict[str, Any]) -> _PreparedRND:
+        """Own and prepare every field off-side before a destination-bound commit."""
+        try:
+            owned = deepcopy(state)
+            prepared, pending_rows, service = self._prepare_state(owned)
+            candidate = deepcopy(self)
+            candidate._install_available_state(owned, prepared)
+            candidate.obs_buffer = pending_rows
+            candidate._admitted_rows = service["admitted_rows"]
+            candidate._consumed_rows = service["consumed_rows"]
+            candidate._dropped_rows = service["dropped_rows"]
+            candidate._optimizer_updates = service["optimizer_updates"]
+            candidate._service_position = service["service_position"]
+            candidate._ordinary_updates_at_position = service["ordinary_updates_at_position"]
+            candidate.step_counter = service["step_counter"]
+            return _PreparedRND(self, candidate.__dict__, False)
+        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
+            raise ValueError("RND checkpoint is malformed") from error
+
+    def install_state(self, prepared: _PreparedRND) -> None:
+        if type(prepared) is not _PreparedRND or prepared.owner is not self or prepared.consumed:
+            raise ValueError("RND prepared state belongs to another destination or was consumed")
+        prepared.consumed = True
+        self.__dict__ = prepared.attributes
+
     def load_state(self, state: dict[str, Any]) -> None:
-        """Validate all owned checkpoint payloads before atomic installation."""
-        if "predictor_service" not in state:
-            # Exact old schema dispatch, not recovery from malformed current state.
-            self.load_available_state(state)
-            return
-        prepared, pending_rows, service = self._prepare_state(state)
-        self._install_available_state(state, prepared)
-        self.obs_buffer = pending_rows
-        self._admitted_rows, self._consumed_rows, self._dropped_rows = (
-            service["admitted_rows"],
-            service["consumed_rows"],
-            service["dropped_rows"],
-        )
-        self._optimizer_updates = service["optimizer_updates"]
-        self._vector_tick, self._paced_updates_this_tick = service["vector_tick"], service["paced_updates_this_tick"]
-        self.step_counter = service["step_counter"]
+        self.install_state(self.prepare_state(state))
diff --git a/tests/test_townlet/regressions/bac/test_pw_local_service.py b/tests/test_townlet/regressions/bac/test_pw_local_service.py
new file mode 100644
index 00000000..072a58ce
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_pw_local_service.py
@@ -0,0 +1,1289 @@
+"""PW04 producer contracts; actual POP/ordinary-runner qualification is separate.
+
+All learning witnesses use the real providers and Adam with positive learning
+rates. Current fixtures are constructed before assertions on the adopted ABI,
+so the initial RED identifies a missing backend guarantee, not an import error.
+"""
+
+from __future__ import annotations
+
+import inspect
+import random
+from copy import deepcopy
+from functools import cache
+from pathlib import Path
+from typing import Any
+
+import numpy as np
+import pytest
+import torch
+import torch.nn.functional as functional
+import yaml
+
+from townlet.config.bac_options import BaCOptions, RNDOptions
+from townlet.config.drive_as_code import IntrinsicStrategyConfig
+from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy, resolve_exploration_policy
+from townlet.config.training_v2_config import TrainingV2Config
+from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
+from townlet.exploration.icm import ICMExploration
+from townlet.exploration.rnd import RNDExploration
+from townlet.exploration.world_curiosity_state import OwnedWorldBackend, ServiceClock, WorldCuriosityDescriptor, WorldRNGState
+
+PROVIDERS = ("rnd", "icm", "adaptive")
+OVERFLOW = ("service_before_admit", "drop_oldest", "drop_newest")
+PRIVATE = "world_eligible_admission"
+SHARED = "vector_tick"
+
+
+def _equal(left: Any, right: Any) -> None:
+    if isinstance(left, torch.Tensor):
+        assert isinstance(right, torch.Tensor)
+        assert left.device == right.device
+        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
+    elif isinstance(left, np.ndarray):
+        assert isinstance(right, np.ndarray)
+        assert left.dtype == right.dtype
+        np.testing.assert_array_equal(left, right)
+    elif isinstance(left, dict):
+        assert isinstance(right, dict) and left.keys() == right.keys()
+        for key in left:
+            _equal(left[key], right[key])
+    elif isinstance(left, (tuple, list)):
+        assert type(left) is type(right) and len(left) == len(right)
+        for a, b in zip(left, right, strict=True):
+            _equal(a, b)
+    else:
+        assert left == right
+
+
+def _ambient() -> tuple[Any, ...]:
+    return torch.get_rng_state().clone(), random.getstate(), deepcopy(np.random.get_state())
+
+
+def _rows(count: int, start: int = 0) -> torch.Tensor:
+    values = torch.arange(start * 3, (start + count) * 3, dtype=torch.float32).reshape(count, 3)
+    return values / 19 + torch.tensor([0.3, -0.7, 1.1])
+
+
+def _rnd(backend: Any) -> RNDExploration:
+    return backend.rnd if isinstance(backend, AdaptiveIntrinsicExploration) else backend
+
+
+def _native(backend: Any) -> dict[str, Any]:
+    return backend.checkpoint_state()
+
+
+def _inner(state: dict[str, Any]) -> dict[str, Any]:
+    return state["rnd_state"] if "rnd_state" in state else state
+
+
+def _service_state(state: dict[str, Any]) -> dict[str, Any]:
+    state = _inner(state)
+    return state["predictor_service"] if "predictor_service" in state else state
+
+
+def _position(backend: Any) -> int:
+    value = _service_state(_native(backend))["service_position"]
+    return 0 if value is None else value
+
+
+def _parameters(state: dict[str, Any]) -> dict[str, torch.Tensor]:
+    state = _inner(state)
+    if "predictor_network" in state:
+        return state["predictor_network"]
+    return {f"{module}/{key}": value for module in ("encoder", "inverse_model", "forward_model") for key, value in state[module].items()}
+
+
+def _learned(before: dict[str, Any], after: dict[str, Any]) -> None:
+    old, new = _parameters(before), _parameters(after)
+    assert any(not torch.equal(old[key], new[key]) for key in old)
+    optimizer = _inner(after)["optimizer"]
+    assert optimizer["state"]
+    assert all(float(group["lr"]) > 0 for group in optimizer["param_groups"])
+    assert all(float(value["step"]) > 0 for value in optimizer["state"].values())
+    assert any(torch.count_nonzero(value["exp_avg"]).item() for value in optimizer["state"].values())
+    if "fixed_network" in _inner(before):
+        _equal(_inner(before)["fixed_network"], _inner(after)["fixed_network"])
+
+
+def _conserved(backend: Any) -> None:
+    state = _inner(_native(backend))
+    service = _service_state(state)
+    if "predictor_service" in state:
+        pending = len(service["pending_observations"])
+        counters = service
+    else:
+        pending = len(state["pending"])
+        counters = state["counters"]
+    assert counters["admitted_rows"] == counters["consumed_rows"] + counters["dropped_rows"] + pending
+    assert counters["consumed_rows"] == counters["optimizer_updates"] * 2
+    if service["service_clock_unit"] == PRIVATE:
+        assert service["service_position"] == counters["admitted_rows"]
+
+
+def _require_api(backend: Any) -> None:
+    # The caller has already constructed/configured the actual current provider.
+    assert isinstance(backend.checkpoint_state(), dict)
+    for name in ("admit_and_service_at", "validate_state", "prepare_state", "install_state"):
+        assert callable(getattr(backend, name, None)), f"PW04 missing backend ABI: {type(backend).__name__}.{name}"
+    parameters = inspect.signature(type(backend)).parameters
+    for name in ("rng", "service_clock_unit"):
+        assert name in parameters, f"PW04 missing constructor ABI: {type(backend).__name__}.{name}"
+
+
+# Fixture construction uses the root-supplied finite public type receipt.
+@cache
+def _policy(kind: str, overflow: str, unit: str) -> ResolvedExplorationPolicy:
+    level = Path("/workspace/hamlet/configs/test/token_set_smoke/levels/L0_test")
+    raw_training = yaml.safe_load((level / "training.yaml").read_text())["training"]
+    raw_training["population"]["size"] = 2
+    raw_training["replay_buffer"]["batch_size"] = 2
+    raw_training["intrinsic"]["rnd"]["feature_dim"] = 3
+    raw_training["intrinsic"]["rnd"]["learning_rate"] = 0.01
+    training = TrainingV2Config.model_validate(raw_training)
+    raw_drive = yaml.safe_load((level / "drive.yaml").read_text())["drive"]["intrinsic"]
+    raw_drive["strategy"] = "adaptive_rnd" if kind == "adaptive" else kind
+    private = unit == PRIVATE
+    options = BaCOptions.model_validate(
+        {
+            "curiosity_scope": {
+                "scope": "per_world" if private else "shared",
+                "seed_policy": "world_id_derived_v1" if private else "legacy_shared_v1",
+            },
+            "rnd": {
+                "service_mode": "paced_fifo",
+                "max_updates_per_tick": 1,
+                "max_pending_rows": 4,
+                "overflow_policy": overflow,
+            },
+            "providers": {
+                "icm": {
+                    "feature_dim": 3,
+                    "hidden_dim": 7,
+                    "learning_rate": 0.01,
+                    "inverse_weight": 0.8,
+                    "forward_weight": 0.2,
+                    "training_batch_size": 2,
+                    "max_pending_transitions": 4,
+                }
+            },
+        }
+    )
+    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(raw_drive), training, options)
+
+
+def _build(kind: str, overflow: str, unit: str, **extra: Any) -> Any:
+    inputs = {"rng": None, "service_clock_unit": unit, **extra}
+    if kind == "icm":
+        return ICMExploration(
+            _policy(kind, overflow, unit),
+            obs_dim=3,
+            action_dim=3,
+            feature_dim=3,
+            hidden_dim=7,
+            learning_rate=0.01,
+            inverse_weight=0.8,
+            forward_weight=0.2,
+            training_batch_size=2,
+            max_pending_transitions=4,
+            device=torch.device("cpu"),
+            **inputs,
+        )
+    if kind == "adaptive":
+        backend = AdaptiveIntrinsicExploration(
+            obs_dim=3,
+            embed_dim=3,
+            rnd_learning_rate=0.01,
+            rnd_training_batch_size=2,
+            initial_intrinsic_weight=1.0,
+            min_intrinsic_weight=0.1,
+            variance_threshold=100.0,
+            min_survival_fraction=0.2,
+            max_episode_length=100,
+            survival_window=12,
+            decay_rate=0.9,
+            **inputs,
+        )
+    else:
+        backend = RNDExploration(obs_dim=3, embed_dim=3, learning_rate=0.01, training_batch_size=2, **inputs)
+    options = RNDOptions(
+        service_mode="paced_fifo",
+        max_updates_per_tick=1,
+        max_pending_rows=4,
+        overflow_policy=overflow,
+    )
+    # Retain the original nested configuration fixture while transporting the
+    # required constructor inputs; the preflight and behavioral assertions stay intact.
+    _rnd(backend).configure_service(options)
+    return backend
+
+
+def _make(kind: str, *, overflow: str = "service_before_admit", unit: str = PRIVATE, rng: Any = None) -> Any:
+    with torch.random.fork_rng(devices=[]):
+        torch.manual_seed(314)
+        current = _build(kind, overflow, unit)
+        _require_api(current)
+        if kind == "adaptive":
+            for name in ("configure_service", "predictor_service_counters", "admit_and_service"):
+                assert callable(getattr(current, name, None)), f"PW04 missing adaptive delegation: {name}"
+        torch.manual_seed(314)
+        backend = _build(kind, overflow, unit, service_clock_unit=unit, rng=rng)
+    assert backend.service_clock_unit == unit
+    return backend
+
+
+def _rng(kind: str, world: str = "world-a") -> Any:
+    descriptor = WorldCuriosityDescriptor.from_policy(
+        _policy(kind, "service_before_admit", PRIVATE),
+        world_ids=("world-a", "world-b"),
+        observation_dim=3,
+        action_dim=3,
+        training_seed=17,
+    )
+    return WorldRNGState.create(descriptor=descriptor, world_id=world, cuda_devices=())
+
+
+def _owned(kind: str) -> Any:
+    # Check the actual current provider fixture before invoking the new hooks.
+    _make(kind)
+    return OwnedWorldBackend.construct(
+        rng=_rng(kind),
+        factory=lambda candidate_rng: _build(
+            kind,
+            "service_before_admit",
+            PRIVATE,
+            service_clock_unit=PRIVATE,
+            rng=candidate_rng,
+        ),
+    )
+
+
+def _context(rows: torch.Tensor, tick: int, *, active: torch.Tensor | None = None) -> IntrinsicTransitionContext:
+    count = len(rows)
+    if active is None:
+        active = torch.ones(count, dtype=torch.bool)
+    return IntrinsicTransitionContext(
+        predecessor=rows,
+        actions=torch.round((rows[:, 0] - 0.3) * 19 / 3).to(torch.int64) % 3,
+        successor=rows * 0.7 + torch.tensor([0.2, 0.1, -0.3]),
+        active_on_entry=active,
+        vector_tick=tick,
+    )
+
+
+def _serve(
+    backend: Any,
+    rows: torch.Tensor,
+    *,
+    tick: int = 1,
+    position: int | None = None,
+    active: torch.Tensor | None = None,
+) -> Any:
+    unit = backend.service_clock_unit
+    count = len(rows) if active is None else int(active.sum().item())
+    if position is None:
+        position = _position(backend) + count if unit == PRIVATE else tick
+    clock = ServiceClock(unit, position)
+    if isinstance(backend, ICMExploration):
+        return backend.admit_and_service_at(_context(rows, tick, active=active), clock=clock)
+    assert active is None
+    return backend.admit_and_service_at(rows, clock=clock)
+
+
+def _traced(backend: Any, rows: torch.Tensor, **kwargs: Any) -> tuple[Any, list[dict[str, Any]]]:
+    """Observe real network forwards and Adam steps without replacing either."""
+    provider = _rnd(backend)
+    current: dict[str, Any] = {}
+    updates: list[dict[str, Any]] = []
+    handles = []
+
+    def remember(name: str) -> Any:
+        def hook(module: Any, inputs: Any, output: torch.Tensor) -> None:
+            current[name] = (inputs[0].detach().clone(), output.detach().clone())
+
+        return hook
+
+    if isinstance(provider, ICMExploration):
+        encoded: list[tuple[torch.Tensor, torch.Tensor]] = []
+
+        def encoder_hook(module: Any, inputs: Any, output: torch.Tensor) -> None:
+            encoded.append((inputs[0].detach().clone(), output.detach().clone()))
+
+        handles.append(provider.encoder.register_forward_hook(encoder_hook))
+        handles.append(provider.inverse_model.register_forward_hook(remember("inverse")))
+        handles.append(provider.forward_model.register_forward_hook(remember("forward")))
+
+        def before_step(optimizer: Any, args: Any, kwargs: Any) -> None:
+            assert len(encoded) == 2
+            predecessor, target = encoded[0][0], encoded[1][1]
+            forward_inputs, predicted = current["forward"]
+            actions = forward_inputs[:, -provider.action_dim :].argmax(dim=1)
+            loss = provider.inverse_weight * functional.cross_entropy(current["inverse"][1], actions)
+            loss = loss + provider.forward_weight * (predicted - target).square().mean()
+            updates.append({"rows": predecessor, "actions": actions.clone(), "successor": encoded[1][0], "loss": float(loss)})
+            encoded.clear()
+
+    else:
+        handles.append(provider.fixed_network.register_forward_hook(remember("target")))
+        handles.append(provider.predictor_network.register_forward_hook(remember("predictor")))
+
+        def before_step(optimizer: Any, args: Any, kwargs: Any) -> None:
+            observations, prediction = current["predictor"]
+            loss = functional.mse_loss(prediction, current["target"][1])
+            updates.append({"rows": observations, "loss": float(loss)})
+
+    handles.append(provider.optimizer.register_step_pre_hook(before_step))
+    try:
+        receipt = _serve(backend, rows, **kwargs)
+    finally:
+        for handle in handles:
+            handle.remove()
+    assert receipt.optimizer_updates == len(updates)
+    if updates:
+        assert receipt.last_loss == updates[-1]["loss"]
+    _conserved(backend)
+    return receipt, updates
+
+
+def _reward(backend: Any, rows: torch.Tensor, tick: int) -> torch.Tensor:
+    if isinstance(backend, ICMExploration):
+        return backend.compute_transition_novelty(_context(rows, tick), update_stats=True)
+    return backend.compute_intrinsic_rewards(rows, update_stats=True)
+
+
+def _warm(backend: Any) -> None:
+    initial = _native(backend)
+    _serve(backend, _rows(5))
+    _reward(backend, _rows(3, 9), 1)
+    if isinstance(backend, AdaptiveIntrinsicExploration):
+        for _ in range(12):
+            backend.update_on_episode_end(40.0)
+        assert backend.current_intrinsic_weight < backend.initial_intrinsic_weight
+    _learned(initial, _native(backend))
+    _conserved(backend)
+
+
+def _full_tail(backend: Any) -> torch.Tensor:
+    """Import a legal full tail; do not pretend fresh private pacing creates it."""
+    _warm(backend)
+    state = _native(backend)
+    inner = _inner(state)
+    service = _service_state(state)
+    rows = _rows(4, 30)
+    if isinstance(backend, ICMExploration):
+        context = _context(rows, 1)
+        inner["pending"] = [
+            {"predecessor": context.predecessor[i].clone(), "action": int(context.actions[i]), "successor": context.successor[i].clone()}
+            for i in range(4)
+        ]
+        counters = inner["counters"]
+    else:
+        service["pending_observations"] = rows.clone()
+        counters = service
+    counters["admitted_rows"] = counters["consumed_rows"] + counters["dropped_rows"] + 4
+    service["service_position"] = counters["admitted_rows"]
+    backend.validate_state(state)
+    backend.load_state(state)
+    _equal(state, _native(backend))
+    return rows
+
+
+def _must_refuse_unchanged(backend: Any, operation: Any) -> None:
+    before, ambient = _native(backend), _ambient()
+    with pytest.raises(ValueError):
+        operation()
+    _equal(before, _native(backend))
+    _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("full_tail", (False, True))
+def test_local_clock_ignores_idle_vector_ticks(kind: str, full_tail: bool) -> None:
+    backend = _make(kind)
+    if full_tail:
+        _full_tail(backend)
+    else:
+        _warm(backend)
+    before = _native(backend)
+    position = _position(backend)
+    for tick in (2, 73, 10000, 10000):
+        rows = _rows(3) if kind == "icm" else _rows(0)
+        active = torch.zeros(3, dtype=torch.bool) if kind == "icm" else None
+        receipt, updates = _traced(backend, rows, tick=tick, position=position, active=active)
+        assert receipt.admitted_rows == receipt.consumed_rows == receipt.dropped_rows == receipt.optimizer_updates == 0
+        assert updates == []
+        _equal(before, _native(backend))
+    _must_refuse_unchanged(backend, lambda: _serve(backend, _rows(0), position=position + 1))
+    _must_refuse_unchanged(backend, lambda: _serve(backend, _rows(1), position=position))
+    receipt, updates = _traced(backend, _rows(1, 50), tick=10001)
+    assert receipt.admitted_rows == 1
+    assert updates
+    assert _position(backend) == position + 1
+    _learned(before, _native(backend))
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("overflow", OVERFLOW)
+def test_backend_losses_and_quotas_are_world_local(kind: str, overflow: str) -> None:
+    world1 = _make(kind, overflow=overflow)
+    _warm(world1)
+    initial = _native(world1)
+    other_schedule = _make(kind, overflow=overflow)
+    other_schedule.load_state(initial)
+    world0 = _make(kind, overflow=overflow)
+    before0 = _native(world0)
+    before1 = _native(world1)
+    first_trace, second_trace = [], []
+    for step, count in enumerate((1, 3, 2, 1), start=1):
+        local = _rows(count, 60 + step * 7)
+        receipt, trace = _traced(world1, local, tick=step)
+        first_trace.extend(trace)
+        for pressure in range(step + 1):
+            pressure_receipt, _ = _traced(world0, _rows(7, 150 + pressure * 11), tick=step * 100 + pressure)
+            assert pressure_receipt.optimizer_updates > 0
+            assert pressure_receipt.dropped_rows == 0
+            _reward(world0, _rows(3, 20 + pressure), step)
+            if kind == "adaptive":
+                for _ in range(12):
+                    world0.update_on_episode_end(40.0)
+        for idle in range(3):
+            empty_receipt, empty_trace = _traced(other_schedule, _rows(0), tick=step * 1000 + idle)
+            assert empty_receipt.optimizer_updates == 0 and not empty_trace
+        other_receipt, other_trace = _traced(other_schedule, local, tick=step * 1000 + 99)
+        second_trace.extend(other_trace)
+        assert receipt == other_receipt
+        _equal(_reward(world1, local, step), _reward(other_schedule, local, step * 1000 + 99))
+        if kind == "adaptive":
+            world1.update_on_episode_end(40.0)
+            other_schedule.update_on_episode_end(40.0)
+        _equal(_native(world1), _native(other_schedule))
+    _equal(first_trace, second_trace)
+    _learned(before0, _native(world0))
+    _learned(before1, _native(world1))
+    assert first_trace
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("overflow", OVERFLOW)
+@pytest.mark.parametrize("full_tail", (False, True))
+def test_private_admission_partition_invariance(kind: str, overflow: str, full_tail: bool) -> None:
+    whole = _make(kind, overflow=overflow)
+    if full_tail:
+        _full_tail(whole)
+    split = _make(kind, overflow=overflow)
+    split.load_state(_native(whole))
+    rows = _rows(7, 80)
+    full_receipt, full_trace = _traced(whole, rows)
+    split_trace = []
+    totals = {key: 0 for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates")}
+    offset = 0
+    # Observation-derived actions preserve the exact transition across partitions.
+    for tick, count in enumerate((1, 3, 0, 2, 1), start=1):
+        receipt, trace = _traced(split, rows[offset : offset + count], tick=tick * 19)
+        split_trace.extend(trace)
+        offset += count
+        for key in totals:
+            totals[key] += getattr(receipt, key)
+    assert offset == len(rows)
+    for key, value in totals.items():
+        assert value == getattr(full_receipt, key)
+    _equal(full_trace, split_trace)
+    _equal(_native(whole), _native(split))
+    if kind != "icm":
+        assert full_receipt.dropped_rows == full_receipt.overflow_optimizer_updates == 0
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+@pytest.mark.parametrize("overflow", OVERFLOW)
+def test_shared_same_tick_overflow_really_learns(kind: str, overflow: str) -> None:
+    backend = _make(kind, overflow=overflow, unit=SHARED)
+    before = _native(backend)
+    rows = _rows(10, 10)
+    receipt, trace = _traced(backend, rows, tick=7)
+    assert receipt.admitted_rows == 10
+    assert receipt.paced_optimizer_updates == 1
+    _equal(trace[0]["rows"], rows[:2])
+    state = _service_state(_native(backend))
+    if overflow == "service_before_admit":
+        assert receipt.overflow_optimizer_updates == 2 and receipt.dropped_rows == 0
+        _equal(torch.cat([update["rows"] for update in trace]), rows[:6])
+        _equal(state["pending_observations"], rows[6:])
+    else:
+        assert receipt.overflow_optimizer_updates == 0 and receipt.dropped_rows == 4
+        _equal(state["pending_observations"], rows[6:] if overflow == "drop_oldest" else rows[2:6])
+    assert state["service_position"] == 7
+    same, same_trace = _traced(backend, _rows(0), tick=7)
+    assert same.optimizer_updates == 0 and not same_trace
+    newer, newer_trace = _traced(backend, _rows(0), tick=8)
+    assert newer.optimizer_updates == 1 and len(newer_trace) == 1
+    _learned(before, _native(backend))
+
+
+@pytest.mark.parametrize("overflow", OVERFLOW)
+def test_private_icm_full_imported_tail_overflow(overflow: str) -> None:
+    backend = _make("icm", overflow=overflow)
+    tail = _full_tail(backend)
+    before = _native(backend)
+    new = _rows(1, 90)
+    receipt, trace = _traced(backend, new)
+    assert receipt.admitted_rows == 1
+    if overflow == "service_before_admit":
+        assert receipt.mandatory_service_updates == 1 and receipt.dropped_rows == 0
+        assert len(trace) == 2
+        _equal(torch.cat([item["rows"] for item in trace]), tail)
+        _equal(_native(backend)["pending"][0]["predecessor"], new[0])
+    else:
+        assert receipt.mandatory_service_updates == 0 and receipt.dropped_rows == 1
+        assert len(trace) == 1
+        expected = tail[1:3] if overflow == "drop_oldest" else tail[:2]
+        _equal(trace[0]["rows"], expected)
+        expected_pending = torch.cat((tail[3:], new)) if overflow == "drop_oldest" else tail[2:]
+        _equal(torch.stack([row["predecessor"] for row in _native(backend)["pending"]]), expected_pending)
+    _learned(before, _native(backend))
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("unit", (PRIVATE, SHARED))
+def test_current_native_warm_adam_tail_and_next_update(kind: str, unit: str) -> None:
+    source = _make(kind, unit=unit)
+    _warm(source)
+    saved = _native(source)
+    inner = _inner(saved)
+    service = _service_state(saved)
+    assert inner["schema"] == ("icm-state-v2" if kind == "icm" else "rnd-state-v2")
+    if kind == "adaptive":
+        assert saved["schema"] == "adaptive-intrinsic-state-v2"
+    assert service["service_clock_unit"] == unit
+    assert "vector_tick" not in service and "service_tick" not in service
+    pending = inner["pending"] if kind == "icm" else service["pending_observations"]
+    assert len(pending) > 0
+    destination = _make(kind, unit=unit)
+    before, ambient = _native(destination), _ambient()
+    destination.validate_state(saved)
+    prepared = destination.prepare_state(saved)
+    _equal(before, _native(destination))
+    _equal(ambient, _ambient())
+    destination.install_state(prepared)
+    _equal(saved, _native(destination))
+    rows = _rows(3, 110)
+    receipt, trace = _traced(source, rows, tick=2)
+    resumed_receipt, resumed_trace = _traced(destination, rows, tick=2)
+    assert receipt == resumed_receipt
+    _equal(trace, resumed_trace)
+    _equal(_native(source), _native(destination))
+    _learned(saved, _native(destination))
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_owned_native_real_learning_and_rng_continuation(kind: str) -> None:
+    source = _owned(kind)
+
+    def warm_and_draw(backend: Any, sources: Any) -> None:
+        _warm(backend)
+        torch.rand(5)
+        random.random()
+        np.random.random(3)
+        sources.numpy.random(4)
+
+    ambient = _ambient()
+    source.call(warm_and_draw)
+    _equal(ambient, _ambient())
+    saved = source.snapshot()
+    destination = _owned(kind)
+    before = destination.snapshot()
+
+    def factory(rng: Any) -> Any:
+        return _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng)
+
+    prepared = destination.prepare_restore(
+        saved,
+        factory=factory,
+        validate_backend=lambda candidate, payload: candidate.validate_state(payload),
+    )
+    _equal(before, destination.snapshot())
+    _equal(ambient, _ambient())
+    destination.install(prepared)
+    _equal(saved, destination.snapshot())
+
+    def next_work(backend: Any, sources: Any) -> Any:
+        draws = (torch.rand(3), random.random(), np.random.random(2), sources.numpy.random(3))
+        receipt, trace = _traced(backend, _rows(3, 140))
+        return draws, receipt, trace, _native(backend)
+
+    _equal(source.call(next_work), destination.call(next_work))
+    _equal(source.snapshot(), destination.snapshot())
+    _equal(ambient, _ambient())
+
+
+def _corrupt(state: dict[str, Any], case: str) -> None:
+    inner, service = _inner(state), _service_state(state)
+    icm = "pending" in inner
+    counters = inner["counters"] if icm else service
+    optimizer = inner["optimizer"]
+    moments = next(iter(optimizer["state"].values()))
+    if case == "moment_nan":
+        list(optimizer["state"].values())[-1]["exp_avg"].flatten()[-1] = float("nan")
+    elif case == "missing_moment":
+        del optimizer["state"][next(iter(optimizer["state"]))]
+    elif case == "negative_variance":
+        moments["exp_avg_sq"].flatten()[-1] = -1
+    elif case == "step":
+        moments["step"] += 1
+    elif case == "lr":
+        optimizer["param_groups"][0]["lr"] = -0.01
+    elif case == "flags":
+        optimizer["param_groups"][0]["amsgrad"] = "false"
+    elif case == "tail_nan":
+        tail = inner["pending"][-1]["successor"] if icm else service["pending_observations"][-1]
+        tail[-1] = float("nan")
+    elif case == "tail_shape":
+        if icm:
+            inner["pending"][-1]["predecessor"] = torch.zeros(4)
+        else:
+            service["pending_observations"] = torch.zeros((1, 4))
+    elif case == "conservation":
+        counters["admitted_rows"] += 1
+    elif case == "position":
+        service["service_position"] += 1
+    elif case == "unit":
+        service["service_clock_unit"] = SHARED
+    elif case == "budget":
+        service["ordinary_updates_at_position"] = 2
+    elif case == "schema":
+        inner["schema"] = "icm-state-v1" if icm else "rnd-state-v1"
+    elif case == "unknown":
+        inner["unexpected"] = 0
+    elif case == "offset":
+        service["optimizer_step_offset"] += 1
+    elif case == "capacity":
+        if icm:
+            inner["pending"] = inner["pending"] * 5
+        else:
+            service["pending_observations"] = service["pending_observations"].repeat(5, 1)
+        counters["admitted_rows"] = counters["consumed_rows"] + counters["dropped_rows"] + 5
+        service["service_position"] = counters["admitted_rows"]
+    elif case == "policy":
+        inner["policy_identity"] = "wrong-policy"
+    elif case == "config":
+        inner["config"]["inverse_weight"] = 0.3
+    else:
+        raise AssertionError(case)
+
+
+INVALID_NATIVE = (
+    "moment_nan",
+    "missing_moment",
+    "negative_variance",
+    "step",
+    "lr",
+    "flags",
+    "tail_nan",
+    "tail_shape",
+    "conservation",
+    "position",
+    "unit",
+    "budget",
+    "schema",
+    "unknown",
+    "capacity",
+)
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("case", INVALID_NATIVE)
+def test_deep_native_refuses_before_any_live_install(kind: str, case: str) -> None:
+    backend = _make(kind)
+    _warm(backend)
+    saved = _native(backend)
+    damaged = deepcopy(saved)
+    _corrupt(damaged, case)
+    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
+        _must_refuse_unchanged(backend, lambda: method(damaged))
+        _equal(saved, _native(backend))
+
+
+@pytest.mark.parametrize("kind,case", (("rnd", "offset"), ("adaptive", "offset"), ("icm", "policy"), ("icm", "config")))
+def test_provider_specific_native_refusal(kind: str, case: str) -> None:
+    backend = _make(kind)
+    _warm(backend)
+    damaged = _native(backend)
+    _corrupt(damaged, case)
+    _must_refuse_unchanged(backend, lambda: backend.validate_state(damaged))
+    _must_refuse_unchanged(backend, lambda: backend.load_state(damaged))
+
+
+@pytest.mark.parametrize(
+    "case", ("missing", "history_nan", "history_negative", "history_bool", "history_long", "derived", "config", "weight", "outer_schema")
+)
+def test_adaptive_outer_failure_cannot_install_valid_changed_rnd(case: str) -> None:
+    backend = _make("adaptive")
+    _warm(backend)
+    changed = _make("adaptive")
+    changed.load_state(_native(backend))
+    _serve(changed, _rows(3, 210))
+    candidate = _native(changed)
+    assert any(
+        not torch.equal(a, candidate["rnd_state"]["predictor_network"][key])
+        for key, a in _native(backend)["rnd_state"]["predictor_network"].items()
+    )
+    if case == "missing":
+        del candidate["survival_history"]
+    elif case == "history_nan":
+        candidate["survival_history"][-1] = float("nan")
+    elif case == "history_negative":
+        candidate["survival_history"][-1] = -1
+    elif case == "history_bool":
+        candidate["survival_history"][-1] = True
+    elif case == "history_long":
+        candidate["survival_history"].append(40.0)
+    elif case == "derived":
+        candidate["min_survival_for_annealing"] += 1
+    elif case == "config":
+        candidate["decay_rate"] = 0.7
+    elif case == "weight":
+        candidate["current_intrinsic_weight"] = 2.0
+    else:
+        candidate["schema"] = "adaptive-intrinsic-state-v1"
+    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
+        _must_refuse_unchanged(backend, lambda: method(candidate))
+
+
+def _mutate_owned_tree(value: Any) -> None:
+    if isinstance(value, torch.Tensor):
+        value.add_(1)
+    elif isinstance(value, np.ndarray):
+        value[...] = 0
+    elif isinstance(value, dict):
+        for nested in value.values():
+            _mutate_owned_tree(nested)
+    elif isinstance(value, (list, tuple)):
+        for index, nested in enumerate(value):
+            _mutate_owned_tree(nested)
+            if isinstance(value, list) and isinstance(nested, (int, float)):
+                value[index] = nested + 1
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_native_snapshot_preparation_and_two_restores_own_every_leaf(kind: str) -> None:
+    source = _make(kind)
+    _warm(source)
+    payload = _native(source)
+    pristine = deepcopy(payload)
+    first, second = _make(kind), _make(kind)
+    prepared = first.prepare_state(payload)
+    second.load_state(payload)
+    _mutate_owned_tree(payload)
+    if kind == "adaptive":
+        payload["survival_history"].append(999.0)
+    _equal(pristine, _native(source))
+    _equal(pristine, _native(second))
+    first.install_state(prepared)
+    _equal(pristine, _native(first))
+    _serve(first, _rows(3, 240))
+    if kind == "adaptive":
+        first.update_on_episode_end(55.0)
+    _equal(pristine, _native(second))
+    _equal(pristine, _native(source))
+    snapshot = _native(second)
+    _mutate_owned_tree(snapshot)
+    _equal(pristine, _native(second))
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_prepared_candidate_is_destination_bound_and_single_install(kind: str) -> None:
+    source = _make(kind)
+    _warm(source)
+    first, second = _make(kind), _make(kind)
+    prepared = first.prepare_state(_native(source))
+    _must_refuse_unchanged(second, lambda: second.install_state(prepared))
+    first.install_state(prepared)
+    _equal(_native(source), _native(first))
+    _must_refuse_unchanged(first, lambda: first.install_state(prepared))
+
+
+def _watch_forwards(backend: Any, calls: list[Any]) -> list[Any]:
+    provider = _rnd(backend)
+    modules = (
+        (provider.encoder, provider.inverse_model, provider.forward_model)
+        if isinstance(provider, ICMExploration)
+        else (provider.fixed_network, provider.predictor_network)
+    )
+
+    def observe(module: Any, inputs: Any) -> None:
+        calls.append(module)
+
+    return [module.register_forward_pre_hook(observe) for module in modules]
+
+
+@pytest.mark.parametrize(
+    "kind,case",
+    [
+        (kind, case)
+        for kind in PROVIDERS
+        for case in ("late_nan", "shape", "dtype", "clock_unit", "clock_gap", "clock_regress", "clock_type", "clock_forged_bool")
+        if (kind, case) != ("icm", "late_nan")
+    ],
+)
+def test_entire_batch_and_clock_preflight_precedes_callbacks(kind: str, case: str) -> None:
+    backend = _make(kind)
+    _warm(backend)
+    rows = _rows(3, 260)
+    clock: Any = ServiceClock(PRIVATE, _position(backend) + 3)
+    if case == "late_nan":
+        rows[-1, -1] = float("nan")
+    elif case == "shape":
+        rows = torch.ones((3, 4), dtype=torch.float32)
+    elif case == "dtype":
+        rows = rows.to(torch.float64)
+    elif case == "clock_unit":
+        clock = ServiceClock(SHARED, _position(backend) + 3)
+    elif case == "clock_gap":
+        clock = ServiceClock(PRIVATE, _position(backend) + 4)
+    elif case == "clock_regress":
+        clock = ServiceClock(PRIVATE, _position(backend) - 1)
+    elif case == "clock_type":
+        clock = {"unit": PRIVATE, "position": _position(backend) + 3}
+    else:
+        if case == "clock_forged_bool":
+            clock = object.__new__(ServiceClock)
+            object.__setattr__(clock, "unit", PRIVATE)
+            object.__setattr__(clock, "position", True)
+    # Actual RP refuses nonfinite contexts itself, hence the ICM NaN pair is
+    # excluded above and covered separately with explicit context-boundary credit.
+    context = None
+    if kind == "icm":
+        context = IntrinsicTransitionContext(
+            predecessor=rows,
+            successor=rows * 0.7,
+            actions=torch.tensor([0, 1, 2]),
+            active_on_entry=torch.ones(3, dtype=torch.bool),
+            vector_tick=1,
+        )
+    calls: list[Any] = []
+    handles = _watch_forwards(backend, calls)
+    before, ambient = _native(backend), _ambient()
+    try:
+        with pytest.raises(ValueError):
+            if kind == "icm":
+                backend.admit_and_service_at(context, clock=clock)
+            else:
+                backend.admit_and_service_at(rows, clock=clock)
+        assert not calls
+        _equal(before, _native(backend))
+        _equal(ambient, _ambient())
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+def test_icm_inactive_rows_and_late_active_action_are_validated() -> None:
+    backend = _make("icm")
+    _warm(backend)
+    rows = _rows(3, 280)
+    bad = IntrinsicTransitionContext(
+        predecessor=rows,
+        successor=rows * 0.7,
+        actions=torch.tensor([0, 1, 3]),
+        active_on_entry=torch.ones(3, dtype=torch.bool),
+        vector_tick=10,
+    )
+    calls: list[Any] = []
+    handles = _watch_forwards(backend, calls)
+    try:
+        _must_refuse_unchanged(backend, lambda: backend.admit_and_service_at(bad, clock=ServiceClock(PRIVATE, _position(backend) + 3)))
+        assert not calls
+    finally:
+        for handle in handles:
+            handle.remove()
+    active = torch.tensor([True, False, True])
+    position = _position(backend)
+    receipt, trace = _traced(backend, rows, active=active, tick=99)
+    assert receipt.admitted_rows == 2 and _position(backend) == position + 2
+    assert trace
+    _conserved(backend)
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+@pytest.mark.parametrize("incomplete", (False, True))
+def test_shared_direct_buffer_validates_every_row_before_reconciliation(kind: str, incomplete: bool) -> None:
+    # Existing API: reach the actual current preflight defect independently of
+    # new-clock ABI absence, with a valid configured real provider fixture.
+    backend = _build(kind, "service_before_admit", SHARED)
+    provider = _rnd(backend)
+    provider.obs_buffer.extend(row.clone() for row in _rows(1 if incomplete else 3, 300))
+    provider.obs_buffer[-1][-1] = float("nan")
+    # External edits precede this baseline; rejection must preserve them as-is.
+    before = _native(backend)
+    counters = provider.predictor_service_counters()
+    clock = provider.step_counter
+    calls: list[Any] = []
+    handles = _watch_forwards(backend, calls)
+    try:
+        with pytest.raises(ValueError):
+            provider.update_predictor()
+        assert not calls
+        assert provider.predictor_service_counters() == counters
+        assert provider.step_counter == clock
+        _equal(before, _native(backend))
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+def test_configured_shared_update_preflights_before_step_counter_change(kind: str) -> None:
+    backend = _build(kind, "service_before_admit", SHARED)
+    provider = _rnd(backend)
+    provider.admit_and_service(_rows(3), vector_tick=50)
+    clock, before = provider.step_counter, _native(backend)
+    calls: list[Any] = []
+    handles = _watch_forwards(backend, calls)
+    rows = _rows(3, 320)
+    rows[-1, -1] = float("nan")
+    try:
+        with pytest.raises(ValueError):
+            backend.update({"observations": rows})
+        assert not calls and provider.step_counter == clock
+        _equal(before, _native(backend))
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+def test_shared_direct_training_and_native_lr_offset_remain_real(kind: str) -> None:
+    backend = _make(kind, unit=SHARED)
+    before = _native(backend)
+    backend.update({"observations": _rows(5)})
+    _learned(before, _native(backend))
+    provider = _rnd(backend)
+    provider.optimizer.param_groups[0]["lr"] = 0.007
+    provider.optimizer.zero_grad()
+    loss = sum(parameter.square().mean() for parameter in provider.predictor_network.parameters())
+    loss.backward()
+    provider.optimizer.step()
+    saved = _native(backend)
+    assert _service_state(saved)["optimizer_step_offset"] == 1
+    destination = _make(kind, unit=SHARED)
+    destination.load_state(saved)
+    _equal(saved, _native(destination))
+    backend.update({"observations": _rows(3, 340)})
+    destination.update({"observations": _rows(3, 340)})
+    _equal(_native(backend), _native(destination))
+    # Unconfigured direct training remains a current substantive operation.
+    with torch.random.fork_rng(devices=[]):
+        torch.manual_seed(19)
+        direct = (
+            AdaptiveIntrinsicExploration(
+                obs_dim=3, embed_dim=3, rnd_learning_rate=0.01, rnd_training_batch_size=2, rng=None, service_clock_unit=SHARED
+            )
+            if kind == "adaptive"
+            else RNDExploration(obs_dim=3, embed_dim=3, learning_rate=0.01, training_batch_size=2, rng=None, service_clock_unit=SHARED)
+        )
+    _require_api(direct)
+    start = _native(direct)
+    direct.update({"observations": _rows(5)})
+    _learned(start, _native(direct))
+    assert len(_rnd(direct).obs_buffer) == 3
+    _rnd(direct).update_predictor()
+    assert len(_rnd(direct).obs_buffer) == 1
+    _conserved(direct)
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+def test_private_direct_training_and_old_native_import_refuse(kind: str) -> None:
+    backend = _make(kind)
+    _warm(backend)
+    _must_refuse_unchanged(backend, lambda: backend.update({"observations": _rows(3)}))
+    _must_refuse_unchanged(backend, lambda: _rnd(backend).update_predictor())
+    _must_refuse_unchanged(backend, lambda: _rnd(backend).admit_and_service(_rows(1), vector_tick=99))
+    old = _native(backend)
+    del _inner(old)["predictor_service"]
+    _must_refuse_unchanged(backend, lambda: backend.validate_state(old))
+    _must_refuse_unchanged(backend, lambda: backend.load_state(old))
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_selected_unit_is_immutable_and_shared_calls_are_explicit(kind: str) -> None:
+    backend = _make(kind)
+    before = _native(backend)
+    with pytest.raises((AttributeError, ValueError)):
+        backend.service_clock_unit = SHARED
+    _equal(before, _native(backend))
+    if kind == "icm":
+        _must_refuse_unchanged(backend, lambda: backend.admit_and_service(_context(_rows(1), 99)))
+    shared = _make(kind, unit=SHARED)
+    if kind == "icm":
+        context = _context(_rows(3), 4)
+        _must_refuse_unchanged(shared, lambda: shared.admit_and_service_at(context, clock=ServiceClock(SHARED, 5)))
+        receipt = shared.admit_and_service(context)
+    else:
+        receipt = shared.admit_and_service(_rows(3), vector_tick=4)
+    assert receipt.admitted_rows == 3 and receipt.optimizer_updates == 1
+    _conserved(shared)
+
+
+@pytest.mark.parametrize("bad", (float("nan"), float("inf"), -1.0, True, 1e100))
+def test_adaptive_completion_preflights_history_before_append(bad: Any) -> None:
+    backend = _make("adaptive")
+    _warm(backend)
+    _must_refuse_unchanged(backend, lambda: backend.update_on_episode_end(bad))
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+def test_rnd_reward_input_and_empty_statistics_are_preflighted(kind: str) -> None:
+    backend = _make(kind)
+    _warm(backend)
+    before = _native(backend)
+    assert backend.compute_intrinsic_rewards(_rows(0), update_stats=True).shape == (0,)
+    _equal(before, _native(backend))
+    rows = _rows(3)
+    rows[-1, -1] = float("nan")
+    calls: list[Any] = []
+    handles = _watch_forwards(backend, calls)
+    try:
+        _must_refuse_unchanged(backend, lambda: backend.compute_intrinsic_rewards(rows, update_stats=True))
+        _must_refuse_unchanged(backend, lambda: backend.compute_intrinsic_rewards(_rows(3), update_stats=1))
+        assert not calls
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("component", ("model_init", "target", "predictor", "service"))
+def test_real_constructor_component_hooks_and_unused_streams(kind: str, component: str) -> None:
+    first_rng, second_rng = _rng(kind), _rng(kind)
+    ambient = _ambient()
+    with second_rng.activate(component):
+        torch.rand(7)
+    _equal(ambient, _ambient())
+    original_rng = first_rng.snapshot()
+    first = _make(kind, rng=first_rng)
+    second = _make(kind, rng=second_rng)
+    _equal(ambient, _ambient())
+    first_state, second_state = _inner(_native(first)), _inner(_native(second))
+    modules = ("encoder", "inverse_model", "forward_model") if kind == "icm" else ("fixed_network", "predictor_network")
+    expected_changes = {
+        "model_init": {"encoder", "inverse_model"} if kind == "icm" else set(),
+        "target": set() if kind == "icm" else {"fixed_network"},
+        "predictor": {"forward_model"} if kind == "icm" else {"predictor_network"},
+        "service": set(),
+    }[component]
+    for module in modules:
+        changed = any(not torch.equal(value, second_state[module][key]) for key, value in first_state[module].items())
+        assert changed == (module in expected_changes), (kind, component, module)
+    after_rng = first_rng.snapshot()
+    unused = ("target", "service") if kind == "icm" else ("model_init", "service")
+    for name in unused:
+        _equal(original_rng["components"][name], after_rng["components"][name])
+    used = ("model_init", "predictor") if kind == "icm" else ("target", "predictor")
+    for name in used:
+        assert not torch.equal(original_rng["components"][name]["torch_cpu"], after_rng["components"][name]["torch_cpu"])
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_shared_constructor_preserves_original_ambient_draw_order(kind: str) -> None:
+    # Reference allocations only: these objects never implement provider learning.
+    # Use the actual RNDNetwork, and the exact declared ICM Linear/ReLU sequence.
+    from townlet.exploration.rnd import RNDNetwork
+
+    _make(kind, unit=SHARED)
+    ambient = _ambient()
+    with torch.random.fork_rng(devices=[]):
+        torch.manual_seed(812)
+        if kind == "icm":
+            expected = {
+                "encoder": torch.nn.Sequential(torch.nn.Linear(3, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
+                "inverse_model": torch.nn.Sequential(torch.nn.Linear(6, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
+                "forward_model": torch.nn.Sequential(torch.nn.Linear(6, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
+            }
+        else:
+            expected = {"fixed_network": RNDNetwork(3, 3), "predictor_network": RNDNetwork(3, 3)}
+        expected_state = {name: module.state_dict() for name, module in expected.items()}
+        expected_rng = torch.get_rng_state().clone()
+        torch.manual_seed(812)
+        backend = _build(kind, "service_before_admit", SHARED, service_clock_unit=SHARED, rng=None)
+        actual = _inner(_native(backend))
+        for name in expected_state:
+            _equal(expected_state[name], actual[name])
+        _equal(expected_rng, torch.get_rng_state())
+    _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_owned_malformed_backend_refuses_before_rng_or_live_install(kind: str) -> None:
+    owner = _owned(kind)
+    owner.call(lambda backend, sources: _warm(backend))
+    saved = owner.snapshot()
+    damaged = deepcopy(saved)
+    _corrupt(damaged["backend"], "moment_nan")
+    if kind == "adaptive":
+        damaged["backend"]["survival_history"][-1] = float("nan")
+    ambient = _ambient()
+    with pytest.raises(ValueError):
+        owner.prepare_restore(
+            damaged,
+            factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
+            validate_backend=lambda candidate, payload: candidate.validate_state(payload),
+        )
+    _equal(saved, owner.snapshot())
+    _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_private_world_construction_and_owned_pressure_preserve_world1(kind: str) -> None:
+    world1 = _owned(kind)
+    world1.call(lambda backend, sources: _warm(backend))
+    saved = world1.snapshot()
+    replay = _owned(kind)
+    prepared = replay.prepare_restore(
+        saved,
+        factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
+        validate_backend=lambda candidate, payload: candidate.validate_state(payload),
+    )
+    replay.install(prepared)
+    world0 = OwnedWorldBackend.construct(
+        rng=_rng(kind, "world-b"),
+        factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
+    )
+    before0 = world0.snapshot()
+    ambient = _ambient()
+
+    def work(backend: Any, sources: Any) -> Any:
+        # Transparent extra domain draws cover the currently deterministic backend.
+        draws = (torch.rand(2), random.random(), np.random.random(), sources.numpy.random())
+        receipt, trace = _traced(backend, _rows(3, 370))
+        return draws, receipt, trace, _native(backend)
+
+    expected = world1.call(work)
+    for _ in range(4):
+        world0.call(work)
+    actual = replay.call(work)
+    _equal(expected, actual)
+    _equal(world1.snapshot(), replay.snapshot())
+    _learned(before0["backend"], world0.snapshot()["backend"])
+    _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("unit", ("wrong-unit", None, True))
+def test_constructor_unit_refusal_precedes_rng_or_model_allocation(kind: str, unit: Any) -> None:
+    _make(kind)
+    rng = _rng(kind)
+    before_rng, ambient = rng.snapshot(), _ambient()
+    with pytest.raises(ValueError):
+        _build(kind, "service_before_admit", PRIVATE, service_clock_unit=unit, rng=rng)
+    _equal(before_rng, rng.snapshot())
+    _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+def test_constructor_rng_refusal_precedes_model_allocation(kind: str) -> None:
+    _make(kind)
+    ambient = _ambient()
+    with pytest.raises(ValueError):
+        _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=object())
+    _equal(ambient, _ambient())
+
+
+def _current_adaptive_with_learning() -> AdaptiveIntrinsicExploration:
+    """Valid current API fixture, deliberately independent of missing new APIs."""
+    backend = _build("adaptive", "service_before_admit", SHARED)
+    initial = deepcopy(backend.checkpoint_state())
+    backend.update({"observations": _rows(3)})
+    _learned(initial, backend.checkpoint_state())
+    for _ in range(12):
+        backend.update_on_episode_end(40.0)
+    return backend
+
+
+def test_current_adaptive_snapshot_history_is_not_a_live_alias() -> None:
+    backend = _current_adaptive_with_learning()
+    pristine = deepcopy(backend.checkpoint_state())
+    snapshot = backend.checkpoint_state()
+    snapshot["survival_history"][-1] = 999.0
+    snapshot["survival_history"].append(888.0)
+    _equal(pristine, backend.checkpoint_state())
+
+
+def test_current_adaptive_restore_history_does_not_alias_payload() -> None:
+    source = _current_adaptive_with_learning()
+    payload = source.checkpoint_state()
+    pristine = deepcopy(payload)
+    destination = _build("adaptive", "service_before_admit", SHARED)
+    destination.load_state(payload)
+    payload["survival_history"][-1] = 777.0
+    payload["survival_history"].append(666.0)
+    _equal(pristine, destination.checkpoint_state())
+
+
+def test_current_adaptive_late_outer_refusal_preserves_nested_learning() -> None:
+    backend = _current_adaptive_with_learning()
+    before = deepcopy(backend.checkpoint_state())
+    donor = _build("adaptive", "service_before_admit", SHARED)
+    donor.load_state(deepcopy(before))
+    donor.update({"observations": _rows(3, 420)})
+    candidate = donor.checkpoint_state()
+    _learned(before, candidate)
+    del candidate["survival_history"]
+    with pytest.raises((KeyError, ValueError)):
+        backend.load_state(candidate)
+    _equal(before, backend.checkpoint_state())
+
+
+def test_icm_nonfinite_context_refusal_is_context_boundary_only() -> None:
+    backend = _build("icm", "service_before_admit", PRIVATE)
+    before = backend.checkpoint_state()
+    rows = _rows(3)
+    rows[-1, -1] = float("nan")
+    with pytest.raises(ValueError):
+        _context(rows, 1)
+    # This deliberately makes no claim of executing ICM's provider preflight.
+    _equal(before, backend.checkpoint_state())
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("overflow", OVERFLOW)
+@pytest.mark.parametrize("unit", (PRIVATE, SHARED))
+def test_current_provider_fixture_preflight(kind: str, overflow: str, unit: str) -> None:
+    """Positive current-interface preflight, not private-clock qualification."""
+    backend = _build(kind, overflow, unit)
+    state = backend.checkpoint_state()
+    assert isinstance(state, dict) and state
+    inner = _inner(state)
+    assert isinstance(inner["optimizer"], dict)
+    assert not inner["optimizer"]["state"]
+    assert all(float(group["lr"]) > 0 for group in inner["optimizer"]["param_groups"])
+    rows = _rows(3)
+    context = _context(rows, 7)
+    _equal(context.predecessor, rows)
+    assert context.vector_tick == 7
+    assert context.actions.tolist() == [0, 1, 2]
+    assert context.active_on_entry.tolist() == [True, True, True]
+    if kind == "icm":
+        assert backend.policy.policy_identity == _policy(kind, overflow, unit).policy_identity
+        rewards = backend.compute_transition_novelty(context, update_stats=False)
+    else:
+        options = _rnd(backend).service_options
+        assert options is not None and options.overflow_policy == overflow
+        assert options.max_pending_rows == 4 and options.max_updates_per_tick == 1
+        rewards = backend.compute_intrinsic_rewards(rows, update_stats=False)
+    assert rewards.shape == (3,) and bool(torch.isfinite(rewards).all())
+    _equal(state, backend.checkpoint_state())
+    if unit == PRIVATE:
+        descriptor = WorldCuriosityDescriptor.from_policy(
+            _policy(kind, overflow, unit),
+            world_ids=("world-a", "world-b"),
+            observation_dim=3,
+            action_dim=3,
+            training_seed=17,
+        )
+        ambient = _ambient()
+        rng = WorldRNGState.create(descriptor=descriptor, world_id="world-a", cuda_devices=())
+        snapshot = rng.snapshot()
+        assert snapshot["schema"] == "world-curiosity-rng-v1"
+        assert snapshot["world_id"] == "world-a" and len(snapshot["cuda_devices"]) == 0
+        assert set(snapshot["components"]) == {"model_init", "target", "predictor", "service"}
+        assert all(component["torch_cpu"].dtype == torch.uint8 for component in snapshot["components"].values())
+        _equal(ambient, _ambient())

```
