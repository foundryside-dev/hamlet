# T03 fresh independent SPEC + QUALITY review

**SPEC: PASS (scoped). QUALITY: PASS (scoped). No P1, P2 or P3 findings.**

Reviewed fixed candidate tree `4175e78397be42fcdf0f126c5f5b85cd6ee1fe0d` in `/tmp/bac-verify-T03-4175e78397`, with base HEAD `049e305df42392373a52c9eb76552abbd74a5b2b`. HEAD alone is not the candidate. Review date: 2026-11-01. This is independent review of the assigned Sol-implemented packet, not worker self-approval or whole-BAC acceptance.

## Authority, identity and inventory

Read the extracted T03 brief FIRST, then the candidate JSON, patch, review package, worker report and snapshot AGENTS. The explicit user preservation rule overrides AGENTS' blanket backward-compatibility deletion instructions. P1 and the current EF400/RP selected-context/cache1.40 requirements govern this review; historical PREPARED notices do not override the coordinator's active dispatch.

Source inventory is exactly five files, charged in full even where inspection was selective:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/effective_run.py | 332 | 30c888a79e739f45a6ea6333afc7d10498e212a3eeca628e89f218d1daa64af8 |
| src/townlet/universe/compiler.py | 976 | 521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92 |
| src/townlet/universe/compiled.py | 1615 | 494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710 |
| src/townlet/config/exploration_policy.py | 653 | 496b988555bc0f23f1a6e335386102acbc1450df1d064d87cfd616a0d953299a |
| tests/test_townlet/regressions/bac/test_effective_run.py | 330 | 4529f9074600233081014073a32aa737da10e31e5a148fe91745faf38595eda8 |

Source total **3906**. All inline Python executions, conservatively counting repeated attempts in full: preflight21 + matrix103 + matrix103 + matrix103 + corrected matrix105 + historical47 + public82 = **564** lines. Combined conservative inventory **4470 < 5000**. No sixth implementation/test/helper source was opened, no executable probe file was created, and no project source/index/Git state was mutated. Brain/OP/training/drive/network APIs were consumed through runtime objects, public schema/signature introspection and the accepted interface receipt, without opening those modules. YAML and native caches/manifests are data; probe copies and resaves were under fresh temporary directories.

Every completed successful probe records before/after HEAD, exact snapshot townlet import, Torch thread count1 and all five SHA256 values. Each boundary also runs both `git diff --exit-code <candidate_tree>` and `git diff --cached --exit-code <candidate_tree>`, so both worktree and staged tree equal the fixed candidate. All boundary checks passed. Imported path was exactly `/tmp/bac-verify-T03-4175e78397/src/townlet/__init__.py`.

## Evidence and assessment

1. **Independent projection matrix: exit0, 26 contrasts passed.** Four accepted network families preserve inactive family presets, distinct authored identity and equal execution identity/seeded selected state dictionaries. Zero-width feedforward and dueling networks constructed and produced finite correctly shaped outputs. Mean recurrent and attention token-set construction both succeeded. Active token widths, recurrent sequence length/objective and PER alpha move execution identity; the PER-only uniform adapter preset does not. Adam/AdamW/SGD/RMSprop selected parameters and constant/step/cosine/exponential schedule cases behaved as their finite projection requires. Every contrasted DTO independently reconstructed through `EffectiveRunConfig.from_dict`. Caller model edits and returned-model edits did not mutate an existing resolved view; frozen option assignments refused.
2. **Independent historical public chain: exit0, three original primary cache cases passed.** Original uniform/per/sequence-trained L1 caches were digest-checked, loaded as genuine1.40, emitted as1.41 dictionaries, reconstructed, saved to new MessagePack files and loaded again. All resulting dictionaries matched, stored brain_hash/pack_brain_hash and every level's stored training_hash remained unchanged, and capture_origin retained “current derivation from known compiled schema 1.40; not historically captured”. Original native bytes remained unchanged. This extends the worker's native-load coverage with a real migration/resave/reload chain. It does not repeat all15 old-cache loads.
3. **Independent current public chain: exit0, 12 named checks plus accompanying assertions passed.** Real YAML compilation of selected drive batch8/pending8 retained original Q-training batch32; batch8/pending7 refused. Typed ICM batch4 beat raw8, raw feature7 derived hidden14, original inactive raw8 stayed retained with inactive role, and predictor kind was transition. Current serialized mismatches in outer brain, outer training, outer drive, resolved option, role and unknown1.42 version refused. The original object was unchanged after refusals. Clone-owned nested model edits did not affect the original. An inactive nested raw float NaN plus inactive typed capacity preset survived real MessagePack; float NaN differed from string “NaN” and null, and active epsilon NaN refused.
4. **Worker evidence checked, not rerun:** read `/tmp/bac-T03/green-owner-r5.log` and `green-owner-r5-identity.json`. Actual terminal summary is **170 passed in 228.81s**, comprising17 owned plus153 existing owner controls. Before/after hashes match this fixed snapshot; worker imports are honestly recorded as the main checkout. The mandatory exact five overrides after full level replacement, inherited/pack hash controls, authored preset hash and cache transport distinctions, and all five strategy controls are present in the owned test/source review and matching worker run. No new concern justified duplicating those170 tests.
5. **Source assessment:** compiler preserves its existing `compute_brain_hash(apply_training_overrides(...))` calls and selected unoverridden public brain. EF independently validates/copies authoring, calls RP with partial authored options FIRST, materializes selected context afterward, and does not feed defaults back to RP as authored declarations. The selected-view reconstruction validates complete transported content, including roles and provenance, and ties it to outer selected brain/training/drive. Explicit1.40 dispatch preserves native access; unknown schemas refuse. Canonical full-view comparison addresses inactive NaN without weakening active numeric validation.

Probe development had three **harness corrections, not product findings**: the first matrix proposed a mean aggregator with num_heads, which the existing DTO rejects; the next proposed PER parameters with prioritized=False, also rejected by existing DTO validation; the third reached all matrix contrasts but attempted to mutate already-frozen BaCOptions without expecting its refusal. The final matrix removes the two invalid accepted-input assumptions and asserts frozen option refusal. These aborted runs are not reported as passing runs; their complete line counts are included above. No validation bypass was introduced.

## Findings and limits

- P1: none identified.
- P2: none identified.
- P3: none identified.

This verdict is for T03's effective view, identities, provenance, ownership and current/known1.40 persistence component. It does not claim runtime consumers have switched to EF, provider factories are repaired, historical checkpoint identity/archive work is complete, or learning/serving/full-resume behavior is qualified. Existing compiled outer DTOs remain an inherited mutable-model surface; ownership checks here establish isolation of resolved snapshots and clones, not a newly promised immutable whole-universe editing API.

The reviewer did not run broad pytest, whole-repository static guards or coverage, and did not claim repository green. Coordinator collection/import/original-fixture checks, all six standing guards, the triggered exact-candidate full suite and final source identity must pass before commit/dependent release. The worker's reported red controls and static checks remain attributed to its receipt. Root's original114 data/three-artifact verification remains coordinator evidence, while this reviewer independently checks the manifest digest and the three specific original cache digests.

## Reproducible inline evidence

All scripts below were supplied to stdin, not saved as executable files. Command prefix, from the fixed snapshot directory:

```sh
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/bac-verify-T03-4175e78397/src /workspace/hamlet/.venv/bin/python - <<'PY'
# exact script below
PY
```

The code is retained for reviewability; temporary resaves never overwrite protected fixtures.

### Preflight and public introspection (exit0)

```python
import hashlib,json,subprocess,torch,townlet,yaml,inspect
from pathlib import Path
from townlet.config.brain_config import BrainConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.agent.network_factory import NetworkFactory
root=Path.cwd()
manifest=json.loads(Path("/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T03-candidate.json").read_text())
def identity():
    data={"head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"import":townlet.__file__,"torch_threads":torch.get_num_threads(),"hashes":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in manifest["source_files"]}}
    assert data["head"]==manifest["base_commit"] and data["hashes"]==manifest["source_files"]
    assert str(root/"src") in data["import"] and data["torch_threads"]==1
    subprocess.run(["git","diff","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["git","diff","--cached","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    return data
print(json.dumps(identity()))
print("Brain schema definitions",json.dumps(BrainConfig.model_json_schema()["$defs"]))
print("factory API",[(n,str(inspect.signature(getattr(NetworkFactory,n)))) for n in dir(NetworkFactory) if n.startswith("build")])
print("manifest",json.dumps(json.loads((root/"tests/test_townlet/fixtures/bac_historical/portable-manifest.json").read_text())["canonical_artifacts"],indent=2))
print(json.dumps(identity()))
```

### Corrected matrix (exit0; MATRIX26)

```python
import hashlib,json,subprocess,torch,townlet,yaml,inspect
from pathlib import Path
from townlet.config.brain_config import BrainConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.agent.network_factory import NetworkFactory
root=Path.cwd()
manifest=json.loads(Path("/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T03-candidate.json").read_text())
def identity():
    data={"head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"import":townlet.__file__,"torch_threads":torch.get_num_threads(),"hashes":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in manifest["source_files"]}}
    assert data["head"]==manifest["base_commit"] and data["hashes"]==manifest["source_files"]
    assert str(root/"src") in data["import"] and data["torch_threads"]==1
    subprocess.run(["git","diff","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["git","diff","--cached","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    return data
print(json.dumps(identity()))

from copy import deepcopy
from townlet.config.effective_run import resolve_effective_run,EffectiveRunConfig
from townlet.config.bac_options import BaCOptions
from townlet.universe.compiler import UniverseCompiler
u=UniverseCompiler().compile(root/"configs/test/token_set_smoke",primary_level="L0_test",use_cache=False)
r=u.effective_run
b=r.base_brain.model_dump(); t=r.training.model_dump(); d=u.get_level("L0_test").drive.intrinsic.model_dump()
def resolve(bi,ti,di):
    return resolve_effective_run(BrainConfig.model_validate(bi),TrainingV2Config.model_validate(ti),primary_level=r.primary_level,origins=r.origins,drive_intrinsic=IntrinsicStrategyConfig.model_validate(di))
def changed(path,val,bi=b,ti=t,di=d):
    bi,ti,di=deepcopy((bi,ti,di)); cur={"b":bi,"t":ti,"d":di}
    parts=path.split(".")
    for p in parts[:-1]: cur=cur[p]
    cur[parts[-1]]=val
    return resolve(bi,ti,di)
cases=[]
def contrast(name,left,right,diff):
    actual=left.execution_hash != right.execution_hash
    assert actual==diff,(name,actual,diff)
    assert left.authored_identity != right.authored_identity,name
    assert EffectiveRunConfig.from_dict(right.to_dict()).to_dict()==right.to_dict(),name
    cases.append(name)

contrast("adam ignores rmsprop eps",r,changed("b.optimizer.rmsprop_eps",1e-6),False)
contrast("constant ignores step gamma",r,changed("b.optimizer.schedule.gamma",0.7),False)

contrast("nonrecurrent ignores sequence length",r,changed("t.training_loop.sequence_length",16),False)
contrast("active train frequency",r,changed("t.training_loop.train_frequency",6),True)
families={
"feedforward":{"hidden_layers":[0],"activation":"tanh","dropout":0.0,"layer_norm":False},
"dueling":{"shared_layers":[0],"activation":"relu","dropout":0.0,"layer_norm":False,"value_stream":{"hidden_layers":[0],"activation":"tanh"},"advantage_stream":{"hidden_layers":[0],"activation":"tanh"}},
"token_set":{"token_embed_dim":16,"q_head_hidden_dim":32,"aggregator":{"type":"attention","num_heads":2}},
"recurrent":{"token_embed_dim":16,"q_head_hidden_dim":32,"aggregator":{"type":"mean"},"lstm":{"hidden_size":8,"num_layers":1,"dropout":0.0}}}
for family,config in families.items():
    fb=deepcopy(b); fb["architecture"]={"type":family,**deepcopy(families)}
    first=resolve(fb,t,d)
    inactive="feedforward" if family!="feedforward" else "dueling"
    other=deepcopy(fb); other["architecture"][inactive]["activation"]="gelu"
    second=resolve(other,t,d)
    contrast(family+" inactive family",first,second,False)
    def network(run):
        torch.manual_seed(93)
        conf=getattr(run.effective_brain.architecture,family)
        fn=getattr(NetworkFactory,"build_"+family)
        if family in ("feedforward","dueling"): return fn(conf,u.metadata.observation_dim,u.metadata.action_count)
        return fn(conf,u.metadata.action_count,u.get_level("L0_test").token_spec)
    n1,n2=network(first),network(second)
    assert n1.state_dict().keys()==n2.state_dict().keys()
    assert all(torch.equal(v,n2.state_dict()[k]) for k,v in n1.state_dict().items())
    if family in ("feedforward","dueling"):
        x=torch.randn(2,u.metadata.observation_dim); out=n1(x)
        assert out.shape==(2,u.metadata.action_count) and torch.isfinite(out).all()
    else:
        changedb=deepcopy(fb); changedb["architecture"][family]["token_embed_dim"]=32
        contrast(family+" active width",first,resolve(changedb,t,d),True)
    if family=="recurrent":
        contrast("recurrent active sequence length",first,changed("t.training_loop.sequence_length",16,fb),True)
        rt=deepcopy(t); rt["bac_options"]={"replay":{"sequence_objective":"anchor_transition"}}
        contrast("recurrent selected objective",first,resolve(fb,rt,d),True)
        plain=deepcopy(fb); plain["replay"].update(prioritized=True,priority_alpha=.6,priority_beta=.4,priority_beta_annealing=True)
        left=resolve(plain,t,d); right=changed("b.replay.priority_alpha",.9,plain)
        contrast("PER active alpha",left,right,True)
        rt["bac_options"]={"replay":{"uniform_sequence_adapter":"uniform_windows_with_replacement"}}
        contrast("PER ignores uniform adapter",left,resolve(plain,rt,d),False)
for opt,active,inactive in (("adam","adam_eps","sgd_momentum"),("adamw","adam_eps","sgd_momentum"),("sgd","sgd_momentum","adam_eps"),("rmsprop","rmsprop_eps","adam_eps")):
    ob=deepcopy(b); ob["optimizer"].update(type=opt,sgd_momentum=.5,sgd_nesterov=True,rmsprop_alpha=.9,rmsprop_eps=1e-8)
    left=resolve(ob,t,d)
    contrast(opt+" active parameter",left,changed("b.optimizer."+active,.6 if active=="sgd_momentum" else 1e-6,ob),True)
    contrast(opt+" inactive parameter",left,changed("b.optimizer."+inactive,.7 if inactive=="sgd_momentum" else 1e-5,ob),False)
for schedule,key,value in (("constant","gamma",.8),("step_decay","gamma",.8),("cosine","t_max",77),("exponential","gamma",.8)):
    sb=deepcopy(b); sb["optimizer"]["schedule"]={"type":schedule,"gamma":.9,"step_size":5,"t_max":50,"eta_min":0}
    left=resolve(sb,t,d); right=changed("b.optimizer.schedule."+key,value,sb)
    contrast(schedule+" projection",left,right,schedule!="constant")
# Original caller objects and every model accessor are independent.
base=BrainConfig.model_validate(b); train=TrainingV2Config.model_validate(t); drive=IntrinsicStrategyConfig.model_validate(d)
own=resolve_effective_run(base,train,primary_level="L0_test",origins={"brain":"owned"},drive_intrinsic=drive); saved=own.to_dict()
base.description="caller mutation"; train.seed=999; drive.strategy="none"
for field in ("base_brain","effective_brain","training","authored_options","options"):
    obj=getattr(own,field)
    if hasattr(obj,"description"): obj.description="return mutation"
    elif hasattr(obj,"seed"): obj.seed=123
    else:
        try: obj.provider_parameter_source="drive"
        except ValueError as exc: assert "frozen" in str(exc)
assert own.to_dict()==saved
print("MATRIX",len(cases),cases)
print(json.dumps(identity()))
```

### Original cache chain (exit0; HISTORICAL3)

```python
import hashlib,json,subprocess,torch,townlet,yaml,inspect
from pathlib import Path
from townlet.config.brain_config import BrainConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.agent.network_factory import NetworkFactory
root=Path.cwd()
manifest=json.loads(Path("/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T03-candidate.json").read_text())
def identity():
    data={"head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"import":townlet.__file__,"torch_threads":torch.get_num_threads(),"hashes":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in manifest["source_files"]}}
    assert data["head"]==manifest["base_commit"] and data["hashes"]==manifest["source_files"]
    assert str(root/"src") in data["import"] and data["torch_threads"]==1
    subprocess.run(["git","diff","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["git","diff","--cached","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    return data
print(json.dumps(identity()))

import msgpack,tempfile
from townlet.universe.compiled import CompiledUniverse
history=root/"tests/test_townlet/fixtures/bac_historical"
mf=json.loads((history/"portable-manifest.json").read_text())
assert hashlib.sha256((history/"portable-manifest.json").read_bytes()).hexdigest()=="d1582c8a3b84eff4dca06c7fdf17e12c7b1adfcbf65f8c7b1c1979f1f87bbfe1"
checked=[]
for artifact in mf["canonical_artifacts"]:
    if artifact["label"] not in ("uniform","per","sequence-trained"): continue
    entries=[(p,h) for p,h in artifact["config_files"].items() if p.endswith("/.compiled/universe-L1_full_observability.msgpack")]
    assert len(entries)==1
    relative,expected=entries[0]; path=history/relative; original=path.read_bytes()
    assert hashlib.sha256(original).hexdigest()==expected
    old=msgpack.unpackb(original,raw=False,strict_map_key=False)
    assert old["compiled_schema_version"]=="1.40"
    loaded=CompiledUniverse.load_from_cache(path)
    new=loaded.to_dict()
    assert new["compiled_schema_version"]=="1.41"
    assert "not historically captured" in new["effective_run"]["derivations"]["capture_origin"]
    for key in ("brain_hash","pack_brain_hash"): assert new[key]==old[key]
    for level in old["all_levels"]: assert new["all_levels"][level]["training_hash"]==old["all_levels"][level]["training_hash"]
    dictionary=CompiledUniverse.from_dict(new)
    with tempfile.TemporaryDirectory(prefix="T03-review-") as tmp:
        save=Path(tmp)/"resaved.msgpack"; dictionary.save_to_cache(save)
        reloaded=CompiledUniverse.load_from_cache(save)
        assert reloaded.to_dict()==new
    assert path.read_bytes()==original
    checked.append(relative); print("HISTORICAL_CHAIN_PASS",relative,flush=True)
print("HISTORICAL",len(checked))
print(json.dumps(identity()))
```

### Selected-context and corruption chain (exit0; PUBLIC_CHAIN12)

```python
import hashlib,json,subprocess,torch,townlet,yaml,inspect
from pathlib import Path
from townlet.config.brain_config import BrainConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.agent.network_factory import NetworkFactory
root=Path.cwd()
manifest=json.loads(Path("/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T03-candidate.json").read_text())
def identity():
    data={"head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"import":townlet.__file__,"torch_threads":torch.get_num_threads(),"hashes":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in manifest["source_files"]}}
    assert data["head"]==manifest["base_commit"] and data["hashes"]==manifest["source_files"]
    assert str(root/"src") in data["import"] and data["torch_threads"]==1
    subprocess.run(["git","diff","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["git","diff","--cached","--exit-code",manifest["candidate_tree"]],check=True,stdout=subprocess.DEVNULL)
    return data
print(json.dumps(identity()))

from copy import deepcopy
import shutil,tempfile,math,msgpack
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compiled import CompiledUniverse
checks=[]
with tempfile.TemporaryDirectory(prefix="T03-review-public-") as tmp:
    pack=Path(tmp)/"pack"; shutil.copytree(root/"configs/test/token_set_smoke",pack,ignore=shutil.ignore_patterns(".compiled"))
    tp=pack/"levels/L0_test/training.yaml"; dp=pack/"levels/L0_test/drive.yaml"
    orig_t=yaml.safe_load(tp.read_text()); orig_d=yaml.safe_load(dp.read_text())
    def compile_case(strategy,raw,opts):
        td=deepcopy(orig_t); dd=deepcopy(orig_d)
        td["training"]["bac_options"]=opts
        dd["drive"]["intrinsic"].update(strategy=strategy,**raw)
        tp.write_text(yaml.safe_dump(td)); dp.write_text(yaml.safe_dump(dd))
        return UniverseCompiler().compile(pack,primary_level="L0_test",use_cache=False)
    u=compile_case("rnd",{"rnd_config":{"batch_size":8}},{"provider_parameter_source":"drive","rnd":{"max_pending_rows":8}})
    r=u.effective_run
    assert (r.training.replay_buffer.batch_size,r.exploration.predictor_batch_size,r.options.rnd.max_pending_rows)==(32,8,8)
    assert r.authored_options.model_dump(exclude_none=True)=={"provider_parameter_source":"drive","rnd":{"max_pending_rows":8}}
    assert CompiledUniverse.from_dict(u.to_dict()).execution_hash==u.execution_hash
    checks.append("drive8/pending8 accepted through compile+dict")
    try: compile_case("rnd",{"rnd_config":{"batch_size":8}},{"provider_parameter_source":"drive","rnd":{"max_pending_rows":7}})
    except ValueError as exc: assert "max_pending_rows" in str(exc); checks.append("drive8/pending7 refused")
    else: raise AssertionError("capacity accepted")
    u=compile_case("icm",{"icm_config":{"training_batch_size":8,"feature_dim":7,"future":{"nested":[2,3]}}},{"providers":{"icm":{"training_batch_size":4}}})
    r=u.effective_run
    assert (r.options.providers.icm.feature_dim,r.options.providers.icm.hidden_dim,r.options.providers.icm.training_batch_size)==(7,14,4)
    assert r.exploration.predictor_input_kind=="transition" and r.training.replay_buffer.batch_size==32
    assert r.exploration.raw_provider_parameters["icm_config"]["training_batch_size"]==8
    assert r.field_roles["drive.intrinsic.icm_config.training_batch_size"].status=="inactive_preset"
    original=u.to_dict()
    changes=[
        ("outer_brain",["brain","description"],"changed outside"),
        ("outer_training",["all_levels","L0_test","training","seed"],191),
        ("outer_drive",["all_levels","L0_test","drive","intrinsic","base_weight"],.37),
        ("new_view",["effective_run","options","providers","icm","hidden_dim"],21),
        ("role",["effective_run","field_roles","brain.architecture.type","status"],"inactive_preset"),
        ("schema",["compiled_schema_version"],"1.42")]
    for name,keys,val in changes:
        damaged=deepcopy(original); cur=damaged
        for key in keys[:-1]: cur=cur[key]
        cur[keys[-1]]=val
        try: CompiledUniverse.from_dict(damaged)
        except ValueError: checks.append(name+" refused")
        else: raise AssertionError(name+" accepted")
        assert u.to_dict()==original
    clone=u.clone(); clone.brain.description="clone only"; clone.get_level("L0_test").training.seed=10
    assert u.to_dict()==original and clone.effective_run.to_dict()==r.to_dict()
    checks.append("clone does not alias original")
    u=compile_case("none",{"rnd_config":{"future":{"v":float("nan")}}},{"providers":{"icm":{"training_batch_size":100,"max_pending_transitions":1}}})
    save=Path(tmp)/"nan.msgpack"; u.save_to_cache(save); restored=CompiledUniverse.load_from_cache(save)
    assert math.isnan(restored.effective_run.exploration.raw_provider_parameters["rnd_config"]["future"]["v"])
    assert restored.execution_hash==u.execution_hash and restored.authored_identity==u.authored_identity
    for value in ("NaN",None):
        data=u.to_dict(); data["effective_run"]["exploration"]["raw_provider_parameters"]["rnd_config"]["future"]["v"]=value
        try: CompiledUniverse.from_dict(data)
        except ValueError: checks.append("NaN replacement "+repr(value)+" refused")
        else: raise AssertionError("NaN replacement accepted")
    data=u.to_dict(); data["effective_run"]["exploration"]["epsilon_start"]=float("nan")
    try: CompiledUniverse.from_dict(data)
    except ValueError as exc: assert "finite" in str(exc); checks.append("active NaN refused")
    else: raise AssertionError("active NaN accepted")
print("PUBLIC_CHAIN",len(checks),checks)
print(json.dumps(identity()))
```

### Exact earlier matrix deltas

All three earlier matrix executions are reconstructible from the corrected matrix above, with no omitted helper code:

- First103-line attempt: remove the two-line try/except frozen-assignment handling (replace with the single `else: obj.provider_parameter_source="drive"`); insert `contrast("mean ignores attention heads",r,changed("b.architecture.token_set.aggregator.num_heads",4),False)` in the first blank line after the contrast function, and `contrast("nonPER ignores alpha",r,changed("b.replay.priority_alpha",0.9),False)` in the blank line before the nonrecurrent contrast. Exit1 at invalid mean/num_heads authoring.
- Second103-line attempt: replace only the mean contrast with a blank line. Exit1 at invalid prioritized=False/PER-alpha authoring.
- Third103-line attempt: also replace the nonPER contrast with a blank line. All26 contrast assertions completed, then exit1 at the unhandled frozen BaCOptions assignment.
- Corrected105-line final: expect the frozen assignment ValueError as shown above. Exit0 with all26 contrasts and complete before/after identity.

No candidate source changed across these attempts.

