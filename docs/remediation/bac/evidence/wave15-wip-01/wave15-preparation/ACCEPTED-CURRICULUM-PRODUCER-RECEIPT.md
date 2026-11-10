# Accepted current curriculum API supplied by root

T20sourceacceptedR11/public02d1f614; T21+DTOacceptedR4/publicf22d77af. Consumeprosewithoutfifthimplementationread. ManagerAPI:

- initialize_population(num_agents:int)->None; factorydoesnotcallit.
- get_batch_decisions(agent_states:BatchedAgentState|None,agent_ids:list[str])->list[CurriculumDecision]; Nonevalidforpureread, listlengthmatchesinitializedN; no learning/commitduringdecisionread. Decisions have difficulty_level,active_meters,depletion_multiplier,reward_mode,reason.
- commit_episode_outcomes(outcomes:Sequence[LaneOutcome])->None, onecurrentcompletionprotocol. prepare_episode_outcomes(outcomes)->PreparedCurriculumOutcomes, commit_prepared_episode_outcomes(prepared)->None alsoavailable. Equalcanonicalretryidempotent, changedduplicate/wholemalformedbatchrefusesbeforeeffects.
- checkpoint_state()->dict[str,Any] ownedcurrentnativeversion2 exacttopkeys version,strategy,completion. validate_checkpoint_state(state)->None,pure. load_state(state)->None validatesbeforeinstall/newpreparedowner. get_stage_info(agent_idx:int)->dict[str,Any],puremetadata; avoidguessingkeys ifnotneeded. Decisiondifficultyfieldis difficulty_level.

Existing public types imported from townlet.training.episode:
EpisodeCompletion(agent_idx:int,reason:CompletionReason,survival_time:int,final_observation:torch.Tensor,final_meters:torch.Tensor), frozenrequiredall. Reasons authored_terminal|retirement|cap|budget|shutdown|checkpoint; completedparticipatingsurvival>=1,idx>=0,densereadingsfinite.
LaneOutcome(outcome:EpisodeCompletion,batch_episode:int,planned_horizon:int,reward_total:float,reward_extrinsic:float,reward_intrinsic:float,reward_shaping:float,policy_entropy:float,world_id:str,world_episode_seq:int), frozenrequiredall and defensiveCPUclones. batch>=0,horizon>=1,seq>=0; nonblankconcreteworld ID,finite nonbooleancomponents/entropy. Rewardcomponents shouldsumtototal. AdeclaredTESTworldidentityisfine forconfiguration/factorywitness, notanactualENVworldrosterqualification. Real runtime IDs remainseparateworldidentityowner, no rowderivedruntimeIDclaims.

Meaningful authoredselectedadversarialrate witness: min/max[0,1],min_steps_at_stage1, thresholdsadvance.8/retreat.2,entropy_gate.5; fullcompletion10/horizon10 withentropy0 commitsfromstage1to2,target.25. rate_limited .01 => difficulty.1; .1 => difficulty.25. stage_bandignorestheselectedrate; singleton[.6,.6]always.6. Authortheseactualvalues in temporaryYAMLfixture beforeREALcompilation, notfakecompiledobjects. Preserveallotherauthoredchoices. Nativecurrentstate/futureuninterrupted comparisons aftercommitusebothgenuinecompiledmanagers, loadownednativeintofreshsameauthoredconfig initializedN. Nohistorical/mid-episode/stochasticclaim.

Root hasverified actualsignatures by currentCB/EP/CS sourceandacceptedT20/T21tests; exactreferencehashes inpublicpreviousreceipts. No additionalimplementation/helperreadsare authorized. Temporarydatafixturecopy mustcopyYAML/authoreddataonly, no repositoryPython/source checkout ororiginalprotectedcachemutation. Currentcompile auto-cachebehavior kept; originalhistoricalcompiledbytes directread-onlyonly.
