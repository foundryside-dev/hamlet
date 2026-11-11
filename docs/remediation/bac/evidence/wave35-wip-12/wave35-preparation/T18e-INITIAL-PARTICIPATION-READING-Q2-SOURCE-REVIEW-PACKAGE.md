 src/townlet/environment/vectorized_env.py | 13 +++++++++++++
 1 file changed, 13 insertions(+)
diff --git a/src/townlet/environment/vectorized_env.py b/src/townlet/environment/vectorized_env.py
index f9fe8bd2..346bc770 100644
--- a/src/townlet/environment/vectorized_env.py
+++ b/src/townlet/environment/vectorized_env.py
@@ -2589,20 +2589,33 @@ class VectorizedHamletEnv:
                 raise ValueError("a genuine step contradicted sealed retirement")
             state = self._participation_state()
             reading = observation.detach().clone()
             committed["state"], committed["observation"], committed["revision"] = state, reading, self._world_revision
 
     def validate_initial_participation(
         self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
     ) -> None:
         """Authenticate current sealed activity/physical reading before parent effects."""
         self._require_phase("active")
+        self._validate_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)
+
+    def validate_initial_participation_reading(
+        self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
+    ) -> None:
+        """Validate retained observation custody for a query, without opening physics."""
+        self._require_phase("active-awaiting-activation", "active", "closed-awaiting-release", "released-completed")
+        self._validate_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)
+
+    def _validate_participation_reading(
+        self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
+    ) -> None:
+        """Shared non-issuing read; public wrappers retain their fixed phase policies."""
         self._accepted(accepted)
         self._valid_record(participation, "initial_participation")
         committed = self._participation_committed
         if committed is None or committed["result"] is not participation or committed["accepted"] is not accepted:
             raise ValueError("initial participation requires the exact committed decision")
         self._participation_reading(predecessor, width=self.observation_dim, dtype=torch.float32)
         self._participation_busy = True
         try:
             self._check_committed_participation()
             if not same_value(committed["observation"], predecessor):
# Q2 actual ENV reading implementation

BaseR29d5481fce58bf63de8071ba24ba26dc6dfe0b18ad
Candidate1f86a18c49747607e6b8a10e2fc8719aa15a0cc9
ENV2889 e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409. Other4ownedbodiesunchanged/test12410a90bb7e.

