# PW04 finite external construction receipt

Rootsource-verified actualpublicAPIs. Backendowner may import/call these APIs in its countedtest but must notopen their implementation as5th/6thsource. This is staticconstructionreceipt, not an executedfixture PASS; rootwill collectandexecute stationaryfixturesbeforecostlyqualification. No imports/runtime performed tocreate thisreceipt.

RNDOptions lives townlet.config.bac_options. Exactlyfour fields service_mode Literal occupancy_fifo/paced_fifo, max_updates_per_tick positiveint, max_pending_rows positiveint, overflow_policy service_before_admit/drop_oldest/drop_newest. For fullyresolvedservicepolicy use RNDOptions(service_mode="paced_fifo",max_updates_per_tick=1,max_pending_rows=4,overflow_policy=selected). Allfour explicitly supplied; capacity>=B2. occupancy_fifo is a substantive currentalternative, not a compatibilitymode. Theoptional-authoredmodel permitsNone but providerconfigure requiresresolvedvalues. Do not use an incompleteRNDOptions asREDfixture.

Actualpublicpolicyresolver recipe (configuration YAML is DATA, not an extraimplementationfile):
```python
from pathlib import Path
from copy import deepcopy
import yaml
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.bac_options import BaCOptions, RNDOptions, resolve_bac_options
from townlet.config.exploration_policy import resolve_exploration_policy, IntrinsicTransitionContext
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor, WorldRNGState, ServiceClock

level = Path("/workspace/hamlet/configs/test/token_set_smoke/levels/L0_test")
raw_training = yaml.safe_load((level / "training.yaml").read_text())["training"]
raw_training["population"]["size"] = 2
raw_training["replay_buffer"]["batch_size"] = 2
raw_training["intrinsic"]["rnd"]["feature_dim"] = 3
raw_training["intrinsic"]["rnd"]["learning_rate"] = 0.01
training = TrainingV2Config.model_validate(raw_training)
raw_drive = yaml.safe_load((level / "drive.yaml").read_text())["drive"]["intrinsic"]
raw_drive["strategy"] = selected_kind  # rnd/adaptive_rnd/icm; presets retained inactive
options = BaCOptions.model_validate({
    "curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"},
    "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1,
            "max_pending_rows": 4, "overflow_policy": selected_overflow},
    "providers": {"icm": {"feature_dim": 3, "hidden_dim": 7,
        "learning_rate": 0.01, "inverse_weight": 0.8, "forward_weight": 0.2,
        "training_batch_size": 2, "max_pending_transitions": 4}},
})
policy = resolve_exploration_policy(
    IntrinsicStrategyConfig.model_validate(raw_drive), training, options
)
# Use the authoredoptions above, not a manuallyfabricated ResolvedExplorationPolicy record.
# RND service options can be constructed fullyresolved directly as above, or:
resolved_rnd = resolve_bac_options(options, training=training).options.rnd
```
The selected policy has ownedprovider_parameters, realstrategy/mode/scope/clock/source fields; publicresolver owns allrequiredfield_roles/raw/authoredprovenance. ICMparameters use typedoptions, RND/AIfeature/learning/batch readmodifiedtraining. Do nothandassemble the large from_dict record; active rawdrive presets cannot override training-owned selectedparameters unless source explicitly changed. Forcurrent sharedmode chooseexplicit scope="shared",seed_policy="legacy_shared_v1" in the sameoptionsrecipe. This is the retainedcurrent sharedalternative label, not an oldnative decoder. No need to import/inspectcount/epsilon implementation.

Actual transition constructor signature (allkeywordsrequired):
`IntrinsicTransitionContext(*, predecessor:Tensor,actions:Tensor,successor:Tensor,active_on_entry:Tensor,vector_tick:int)`.
Use float32 finite predecessor/successor[N,D], int64 actions[N] within[0,action_dim), bool active_on_entry[N], alldeviceCPU, exactnonnegativePythonint vector_tick. Arraysareowned/detachedbyactualconstructor; accessreturnsclones. ForICM chooseobs_dim3/action_dim3andnontrivialactions0,1,2/successors. Currentcontext hasNOstamp/worldID fields; globalvector_tick isonlyprovenance forfutureprivate at(clock), neverlocalserviceauthority. Laterbank/contextmigration remainsrequired.

Actual descriptor/RNG construction:
```python
descriptor = WorldCuriosityDescriptor.from_policy(
    policy, world_ids=("world-a", "world-b"), observation_dim=3,
    action_dim=3, training_seed=17,
)
rng_a = WorldRNGState.create(descriptor=descriptor,world_id="world-a",cuda_devices=())
rng_b = WorldRNGState.create(descriptor=descriptor,world_id="world-b",cuda_devices=())
```
Policy must be per_world with explicitauthoredorigin; worldIDs exactunique nonempty, widthsconsistent withactualconstructedprovider. `.create` requires explicitcuda_devices tuple; CPU () doesnotquery/initCUDA. Descriptor derives exactly four streams model_init,target,predictor,service fromexactID/seed/provider. `.activate(component)` iscontextmanager, sameownernesting supported; returned sources include privatePython/NumPy, Torchusesactivatedglobaldomain. `.snapshot()` and `.from_snapshot(state,*,descriptor,world_id,cuda_devices)` preserveconsumedstreams. PublicOwnedWorldBackend.construct(*,rng,factory) callback receivescandidateWorldRNGState whilemodel_initactivated, callsactualcomponenthooks, then owns backend. Call/snapshot/prepare_restore semantics are in priorPW02capsuleandnewPW04brief. NoWSsourceopeningneeded.

Fixturepreflight must reach validactualcurrentconstructor/configure_service/checkpoint_state before asserting newAPIabsence. Allconfigknobs/testhelpers remainin countedtest<=1500; do notaddafifthhelperforrecipe. If realconstructor throws beforetheintendedassertion, reportexactcause/rootrepairsreceipt ratherthanlabelingitRED or broadlyrerunning. Genuine hardwarecases unrun/skippedwhenCUDAunavailable; CPUneverpromoted.


Additional actualsnapshot/context spelling receipt: OwnedWorldBackend.snapshot() exactenvelope schema="owned-world-backend-v1",healthy,backend,rng; backend is ownedrawprovider.checkpoint_state() payload. WorldRNGState.snapshot() exactschema="world-curiosity-rng-v1",descriptor,world_id,cuda_devices,components; components[component]["torch_cpu"] is savedCPUuint8state. Each componenthasseed,torch_cpu,cuda,python,numpy_pcg64,numpy_legacy. Snapshotsareowneddata.

Contextcausalboundary: IntrinsicTransitionContext itself refusesNaN/Inf observations and mismatchedfloatingdtype; matchingfloat64 isaccepted. Itdoesnotknowproviderwidth oractiondim; finitewrongwidth, activeout-of-rangeint64actions andmatchingfloat64 arecontextvalid inputsforactualICMproviderpreflight tests. Do notcreditcontextNaNrefusal asprovideratomicity. Existing AIhistoryalias/configuredstep/directbuffer tests shoulduseactualcurrent_buildpathswherepossible soAPIabsenceisnotmistakenformultipleindependentbugwitnesses.
