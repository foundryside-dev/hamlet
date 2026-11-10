# Actual current-only scope fixture delta R2→R4

BaseR2 808e9975155d089dd4c62996dbb996359d774fc6; currenttree 0918ce2f973b15e987fd943898ae92d39c1801c8. Fifthwholefile<=500 in5/4900existingcontext. Rootbyteverified currentpositive tailunchanged atR3, R4onlycorrectsnewoldEFexceptionclass to exactKeyErrorstatic_policy; runtimeoldnativeparentValueErrorcontrolretained.

```diff
diff --git a/tests/test_townlet/regressions/bac/test_pw_scope_contract.py b/tests/test_townlet/regressions/bac/test_pw_scope_contract.py
index ac16ce8a..a70783d0 100644
--- a/tests/test_townlet/regressions/bac/test_pw_scope_contract.py
+++ b/tests/test_townlet/regressions/bac/test_pw_scope_contract.py
@@ -107,32 +107,21 @@ def test_scope_defaults_and_identity_roundtrip(tmp_path: Path) -> None:
         artifact = NATIVE / item["artifact"]
         assert item["producer_sha"] == PRODUCER and item["schema_version"] == "1.41"
         assert hashlib.sha256(artifact.read_bytes()).hexdigest() == item["sha256"] == NATIVE_DIGESTS[item["label"]]
-        legacy = CompiledUniverse.load_from_cache(artifact)
-        assert legacy is not None
-        view = legacy.effective_run
-        assert view is not None
-        assert legacy.execution_hash == view.execution_hash == item["execution_hash"]
-        assert legacy.brain_hash == item["brain_hash"] and legacy.pack_brain_hash == item["pack_brain_hash"]
-        assert view.training_hash == item["training_hash"]
-        assert view.authored_identity == item["effective_run"]["authored_identity"]
-        assert view.exploration.policy_identity == _legacy_policy_identity(item["effective_run"]["exploration"])
-        view.validate_payload(item["effective_run"])
-        reconstructed = EffectiveRunConfig.from_dict(item["effective_run"])
-        assert reconstructed.execution_hash == view.execution_hash
-        assert reconstructed.training_hash == view.training_hash
-        for field in ("rnd_feature_dim", "rnd_learning_rate", "predictor_batch_size", "max_pending_rows", "max_updates_per_tick"):
-            assert getattr(view.exploration, field) == item["effective_run"]["exploration"][field]
+        # Historical bytes/metadata remain DATA; current native1.42 refuses1.41.
+        historical = item["effective_run"]
+        assert historical["execution_hash"] == item["execution_hash"]
+        assert historical["training_hash"] == item["training_hash"]
+        assert historical["authored_identity"]
+        assert "curiosity_scope" not in historical["exploration"]
         if item["label"] == "options-authored":
-            assert view.authored_options.serving.policy_mode == "mc_dropout"
-            assert view.authored_options.replay.sampling_mode == "independent_with_replacement"
-            assert view.authored_options.checkpoint.save_initial is True
-        recached = tmp_path / f"{item['label']}.msgpack"
-        legacy.save_to_cache(recached)
-        for restored in (CompiledUniverse.from_dict(legacy.to_dict()), CompiledUniverse.load_from_cache(recached)):
-            assert restored is not None and restored.execution_hash == item["execution_hash"]
-            assert restored.effective_run.training_hash == item["training_hash"]
-            assert restored.effective_run.authored_identity == item["effective_run"]["authored_identity"]
-            _assert_scope(restored.effective_run.exploration, "shared", "bac-options-v1")
+            assert historical["authored_options"]["serving"]["policy_mode"] == "mc_dropout"
+            assert historical["authored_options"]["replay"]["sampling_mode"] == "independent_with_replacement"
+            assert historical["authored_options"]["checkpoint"]["save_initial"] is True
+        with pytest.raises(ValueError):
+            CompiledUniverse.load_from_cache(artifact)
+        with pytest.raises(KeyError, match="static_policy"):
+            EffectiveRunConfig.from_dict(historical)
+        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == NATIVE_DIGESTS[item["label"]]
 
     training, _ = _authoring(None, 17, 3)
     defaults = resolve_bac_options(None, training=training)

```
