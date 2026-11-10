Previous5d866cc7fe7af528fcbc2119b1ba9ddefb03062e
Current4a69520c1616ebb2c3bbd7c4868b207e80a3952d
Childcustody only, no production changes; source5inventory3446<=4250.
diff --git a/tests/test_townlet/regressions/bac/test_pw_rng_domains.py b/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
index 414308e6..43a493e0 100644
--- a/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
+++ b/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
@@ -657,36 +657,98 @@ def test_used_cuda_domain_restoration_when_hardware_available():
                 raise RuntimeError("device callback")
         _equal(before, _globals(devices))
     finally:
         for device, state in before[3].items():
             torch.cuda.set_rng_state(state, device)
 
 
 def test_restoration_failure_poisoning_isolated_from_pytest():
-    _api()  # Missing production ABI remains the intended RED, before spawning a child.
+    _api()
     source = Path(ws.__file__).resolve()
     root = source.parents[3]
     expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()
     expected_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
+    parent_profile = {
+        "python_executable": sys.executable,
+        "python_version": sys.version,
+        "torch_version": torch.__version__,
+        "torch_threads": torch.get_num_threads(),
+        "torch_interop_threads": torch.get_num_interop_threads(),
+    }
     script = r"""
 import hashlib
+import json
+import os
+import fcntl
 import random
 import subprocess
 import sys
 from pathlib import Path
 import numpy as np
 import torch
 
-source, expected_hash, expected_head, root = sys.argv[1:]
+source, expected_hash, expected_head, root, encoded_profile = sys.argv[1:]
+expected_profile = json.loads(encoded_profile)
+torch.set_num_threads(expected_profile["torch_threads"])
+torch.set_num_interop_threads(expected_profile["torch_interop_threads"])
+actual_profile = {
+    "python_executable": sys.executable,
+    "python_version": sys.version,
+    "torch_version": torch.__version__,
+    "torch_threads": torch.get_num_threads(),
+    "torch_interop_threads": torch.get_num_interop_threads(),
+}
+assert actual_profile == expected_profile
 sys.path.insert(0, str(Path(root) / "src"))
 from townlet.exploration import world_curiosity_state as ws
 assert Path(ws.__file__).resolve() == Path(source)
 assert hashlib.sha256(Path(ws.__file__).read_bytes()).hexdigest() == expected_hash
 assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == expected_head
+qualification_names = ("BAC_QUAL_MANIFEST", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_ROOT", "BAC_QUAL_OUTPUT")
+qualified = any(name in os.environ for name in qualification_names)
+def custody():
+    assert all(os.environ.get(name) for name in qualification_names), "incomplete qualification environment"
+    assert Path(os.environ["BAC_QUAL_ROOT"]).resolve() == Path(root).resolve()
+    assert actual_profile["torch_threads"] == 1
+    manifest_bytes = Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()
+    manifest = json.loads(manifest_bytes)
+    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
+    assert sha == expected_head == os.environ["BAC_QUAL_SHA"] == manifest["base_commit"]
+    with (Path(root) / ".superpowers/bac-qualification-index.lock").open("a+") as lock:
+        fcntl.flock(lock, fcntl.LOCK_EX)
+        try:
+            tree = subprocess.check_output(["git", "write-tree"], cwd=root, text=True).strip()
+        finally:
+            fcntl.flock(lock, fcntl.LOCK_UN)
+    assert tree == os.environ["BAC_QUAL_TREE"] == manifest["candidate_tree"]
+    source_hashes = {}
+    for relative, expected in manifest["source_files"].items():
+        path = Path(root) / relative
+        assert path.resolve() == path and path.is_file(), relative
+        source_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
+        assert source_hashes[relative] == expected, relative
+    import_paths = {}
+    for name, module in list(sys.modules.items()):
+        if name == "townlet" or name.startswith("townlet."):
+            filename = getattr(module, "__file__", None)
+            if filename is not None:
+                path = Path(filename).resolve()
+                relative = str(path.relative_to(Path(root)))
+                assert relative in source_hashes, (name, relative)
+                assert path == Path(root) / "src" / Path(*name.split(".")).with_suffix(".py") or (
+                    path == Path(root) / "src" / Path(*name.split(".")) / "__init__.py"
+                ), (name, path)
+                import_paths[name] = str(path)
+    assert import_paths["townlet.exploration.world_curiosity_state"] == source
+    return {"pid": os.getpid(), "sha": sha, "candidate_tree": tree, **actual_profile,
+            "import_path": str(Path(ws.__file__).resolve()), "import_paths": import_paths,
+            "source_hashes": source_hashes, "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()}
+if qualified:
+    initial_custody = custody()
 seeds = {world: {component: ws.derive_world_seed(training_seed=29, world_id=world, provider_kind="rnd", component=component)
                  for component in ws.WORLD_SEED_COMPONENTS} for world in ("a", "b")}
 descriptor = ws.WorldCuriosityDescriptor(
     schema_version=1, scope="per_world", provider_kind="rnd", provider_parameter_hash="a" * 64,
     observation_dim=3, action_dim=2, world_ids=("a", "b"), seed_policy="world_id_derived_v1",
     service_clock_unit="world_eligible_admission", origin="authored", guarantee="world_id_owned_state",
     training_seed=29, seeds=seeds)
 first = ws.WorldRNGState.create(descriptor=descriptor, world_id="a", cuda_devices=())
@@ -733,20 +795,30 @@ assert actual_numpy[0] == saved_numpy[0] and np.array_equal(actual_numpy[1], sav
 assert actual_numpy[2:] == saved_numpy[2:]
 before_refusal = list(swaps)
 try:
     with second.activate("service"):
         raise AssertionError("unusable coordinator permitted activation")
 except (RuntimeError, ValueError) as error:
     assert any(word in str(error).lower() for word in ("unusable", "poison", "failed", "restoration")), str(error)
 assert swaps == before_refusal, "refused activation still swapped global streams"
+if qualified:
+    final_custody = custody()
+    assert final_custody == initial_custody
+    output = Path(os.environ["BAC_QUAL_OUTPUT"])
+    assert output.is_absolute() and output.is_dir()
+    receipt = output / f"subprocess-custody-poisoning-{os.getpid()}.json"
+    with receipt.open("x") as stream:
+        json.dump({**final_custody, "poisoning_assertions_passed": True}, stream, sort_keys=True, indent=2)
+        stream.flush()
+        os.fsync(stream.fileno())
 print("isolated restoration custody and coordinator refusal verified")
 """
     result = subprocess.run(
-        [sys.executable, "-c", script, str(source), expected_hash, expected_head, str(root)],
+        [sys.executable, "-c", script, str(source), expected_hash, expected_head, str(root), json.dumps(parent_profile)],
         cwd=root,
         capture_output=True,
         text=True,
         timeout=60,
     )
     assert result.returncode == 0, result.stdout + result.stderr
     assert "isolated restoration custody and coordinator refusal verified" in result.stdout
 
