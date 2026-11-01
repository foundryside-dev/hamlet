# PW01 final independent SPEC/QUALITY review (R4)

Scoped verdict: PASS. No material defect found in the bounded PW01 scope,
identity, seed and serialization contract. This is not whole-candidate acceptance
or certification of the later private runtime bank/optimizer independence.

Final candidate tree: d2b46a1bd74eb187ecbe7c1cdd5e9723d351e5c4.
Base HEAD: 1f9d831a8fe76ab00e06774ef6888985f6c2aec2.
Manifest: /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave03/final-r4-candidate.json.
Existing initial report and evidence were preserved.

| Complete source path | Lines | SHA256 |
| --- | ---: | --- |
| /workspace/hamlet/src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| /workspace/hamlet/src/townlet/config/effective_run.py | 365 | 9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c |
| /workspace/hamlet/src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| /workspace/hamlet/src/townlet/exploration/world_curiosity_state.py | 223 | 295314b7f891cdbf33646a73df6a57c39d9fd407d61675ee6fee80bd9053d9ae |
| /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_scope_contract.py | 261 | d467ede1f0d2a841f62d51c70812f10b2dc6cb2ada28fa288ca32f14bcd8e150 |

Five complete files/1911 lines. Current probe110 lines, no sixth helper source
or separate executable file. Cumulative conservative probe charge260 lines
(initial150 plus final110), total2171/5000. Per-file ceilings respected.

The seven post-lint changes were independently compared against the prior reviewed
candidate; they replace seven default expressions with equivalent explicit
branches. The full original spec remains the review baseline, including retained
historical shared identities and default numerics. Actual final-source runtime
verification below confirms behavior rather than relying on equivalence alone.

The independent inline process returned exit0 with171 expected corruption or
mutation rejections, plus positive assertions for every provider selector,
private identity under population changes, exact dot/slash/case/Unicode IDs,
stable seed streams under reordered IDs/spectators, explicit drive-selected
batch/capacity handling and ICM capacity derivation. It rechecked both genuine
native artifact byte hashes and historical effective execution/training/authored
identities. Partial current/new ownership payloads and contradictory old-shaped
private declarations refused. Descriptor schema/types/geometry/provider/hash/
origin/guarantee/binding/stream corruption refused; nested maps and fields were
immutable, and portable output had no mutable alias.

HEAD/index/no unstaged tracked changes/own source hashes were asserted before
and after the runtime process. Local townlet import was verified under
/workspace/hamlet/src; torch threads1, OMP/MKL/OpenBLAS1 and CUDA empty.
No production/test/index edits, checkouts, source copies or delegation.

Root's authorized reusable post-lint two-node suite log was independently read:
/workspace/bac-review-2026-11-01/qualification/wave03-check-r2/PW01.log,
2 passed in33.03s. Those nodes cover genuine native cache load/recache and new
compiler/cache roundtrips. Root also reports137 config-consumer passes,187 mypy
files passing and ratchet614 with no PW violations; these are attributed root
results, not independently rerun by this reviewer. Remaining broad guards/full
suite are root-owned and are not claimed complete here.

Exact stdout (trailing newline included in SHA256
0c7b9839b4328b6c911d218c67115bb46621f3b2a2da8da68f9695fcb54961d6):

```json
{"result": "PASS", "rejected_corruptions": 171, "candidate": "d2b46a1bd74eb187ecbe7c1cdd5e9723d351e5c4", "local_import": "/workspace/hamlet/src/townlet/__init__.py", "threads": 1}
```

Exact command, executed in /workspace/hamlet (inline probe110 lines):

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' .venv/bin/python - <<'PY'
import hashlib, json, subprocess, copy, dataclasses
from pathlib import Path
root=Path('/workspace/hamlet')
manifest=json.loads((root/'.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave03/final-r4-candidate.json').read_text())
paths=['src/townlet/config/bac_options.py','src/townlet/config/effective_run.py','src/townlet/config/exploration_policy.py','src/townlet/exploration/world_curiosity_state.py','tests/test_townlet/regressions/bac/test_pw_scope_contract.py']
def identity():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==manifest['base_commit']
    assert subprocess.check_output(['git','write-tree'],text=True).strip()==manifest['candidate_tree']
    subprocess.run(['git','diff','--quiet'],check=True)
    for p in paths:
        assert hashlib.sha256((root/p).read_bytes()).hexdigest()==manifest['source_files'][p]
identity()
import torch, townlet
assert Path(townlet.__file__).resolve()==root/'src/townlet/__init__.py'
torch.set_num_threads(1)
from townlet.config.bac_options import BaCOptions
from townlet.config.exploration_policy import ResolvedExplorationPolicy as RP, resolve_exploration_policy, SCOPE_FIELDS
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.effective_run import EffectiveRunConfig
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor as WD
native=json.loads((root/'tests/test_townlet/fixtures/bac_curiosity_pre_scope/manifest.json').read_text())
count=0
def refuse(fn):
    global count
    try: fn()
    except (ValueError,TypeError,dataclasses.FrozenInstanceError): count+=1
    else: raise AssertionError('corruption accepted')
def policy(strategy, population=17, batch=3, drive_batch=None, extra=None):
    t=copy.deepcopy(native['artifacts'][0]['effective_run']['training'])
    t['population']['size']=population
    t['replay_buffer']['batch_size']=batch
    opts={'curiosity_scope':{'scope':'per_world'}}
    if extra: opts.update(extra)
    d=copy.deepcopy(native['artifacts'][0]['effective_run']['exploration']['authored_parameters']['drive_intrinsic'])
    d['strategy']=strategy
    if drive_batch is not None:
        opts['provider_parameter_source']='drive'
        d['rnd_config']={'predictor_batch_size':drive_batch}
        d['adaptive_config']=None
    t['bac_options']=opts
    training=TrainingV2Config.model_validate(t)
    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(d),training,BaCOptions.model_validate(opts))
for strategy in ('none','rnd','adaptive_rnd','count_based','icm'):
    p=policy(strategy)
    assert p.policy_identity==policy(strategy,population=999).policy_identity
    assert p.max_pending_rows==3
    assert RP.from_dict(p.to_dict()).to_dict()==p.to_dict()
    for field in SCOPE_FIELDS:
        bad=p.to_dict(); bad.pop(field)
        refuse(lambda: RP.from_dict(bad))
    bad=p.to_dict()
    for field in SCOPE_FIELDS: bad.pop(field)
    refuse(lambda: RP.from_dict(bad))
    bad=p.to_dict(); bad['parameter_units']['max_updates_per_tick']='predictor_minibatches/vector_tick'
    refuse(lambda: RP.from_dict(bad))
    for field,value in [('curiosity_scope','shared'),('scope_origin','bac-options-v1'),('seed_policy','legacy_shared_v1'),('scope_guarantee','shared_population_state')]:
        bad=p.to_dict(); bad[field]=value
        refuse(lambda: RP.from_dict(bad))
for strategy in ('rnd','adaptive_rnd'):
    p=policy(strategy,drive_batch=7)
    assert p.predictor_batch_size==7 and p.max_pending_rows==7
    assert p.policy_identity==policy(strategy,population=999,drive_batch=7).policy_identity
    assert policy(strategy,drive_batch=7,extra={'rnd':{'max_pending_rows':19}}).max_pending_rows==19
    refuse(lambda: policy(strategy,drive_batch=7,extra={'rnd':{'max_pending_rows':6}}))
assert policy('icm',extra={'providers':{'icm':{'training_batch_size':11}}}).max_pending_rows==11
assert policy('icm',extra={'providers':{'icm':{'training_batch_size':11,'max_pending_transitions':23}}}).max_pending_rows==23
ids=('a.b','a/b','A.B','世界','é','e\u0301')
def describe(p,worlds=ids):
    return WD.from_policy(p,world_ids=worlds,observation_dim=7,action_dim=4,training_seed=42)
for strategy in ('none','rnd','adaptive_rnd','count_based','icm'):
    p=policy(strategy); d=describe(p); payload=d.to_dict()
    assert WD.from_dict(payload).to_dict()==payload
    other=describe(policy(strategy,population=97),('spectator',*reversed(ids)))
    assert d.world_binding_hash!=other.world_binding_hash
    for w in ids:
        for stream in ('model_init','target','predictor','service'):
            assert d.seed_for(w,stream)==other.seed_for(w,stream)
    for field,value in [('schema_version',True),('schema_version',2),('observation_dim',-1),('observation_dim',True),('action_dim',0),('action_dim',1.5),('training_seed',True),('provider_kind','invalid'),('provider_parameter_hash','x'*64),('origin','bac-options-v1'),('guarantee','shared_population_state'),('world_binding_hash','0'*64),('canonical_world_ids',list(reversed(sorted(ids))))]:
        bad=copy.deepcopy(payload); bad[field]=value
        refuse(lambda: WD.from_dict(bad))
    for worlds in ((),('',),('a','a'),('ok',None)):
        refuse(lambda: describe(p,worlds))
    bad=copy.deepcopy(payload); bad['seeds'][ids[0]]['service']+=1
    refuse(lambda: WD.from_dict(bad))
    bad=copy.deepcopy(payload); bad['seeds'][ids[0]].pop('target')
    refuse(lambda: WD.from_dict(bad))
    bad=copy.deepcopy(payload); bad['seeds']['alien']=bad['seeds'].pop(ids[0])
    refuse(lambda: WD.from_dict(bad))
    try: d.seeds[ids[0]]['service']=0
    except TypeError: count+=1
    else: raise AssertionError('mutable streams')
    refuse(lambda: setattr(d,'world_ids',('changed',)))
    payload['seeds'][ids[0]]['service']+=1
    assert d.to_dict()!=payload
for item in native['artifacts']:
    artifact=root/'tests/test_townlet/fixtures/bac_curiosity_pre_scope'/item['artifact']
    assert hashlib.sha256(artifact.read_bytes()).hexdigest()==item['sha256']
    old=item['effective_run']; rp=RP.from_dict(old['exploration'])
    assert rp.curiosity_scope=='shared' and rp.scope_origin=='bac-options-v1'
    current=EffectiveRunConfig.from_dict(old)
    assert current.execution_hash==item['execution_hash'] and current.training_hash==item['training_hash']
    assert current.authored_identity==old['authored_identity']
    bad=current.to_dict(); bad['exploration'].pop('curiosity_scope')
    refuse(lambda: EffectiveRunConfig.from_dict(bad))
    bad=copy.deepcopy(old['exploration'])
    bad['authored_parameters']['bac_options']['curiosity_scope']={'scope':'per_world'}
    refuse(lambda: RP.from_dict(bad))
identity()
print(json.dumps({'result':'PASS','rejected_corruptions':count,'candidate':manifest['candidate_tree'],'local_import':townlet.__file__,'threads':torch.get_num_threads()}))
PY
```

