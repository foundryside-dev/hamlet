# Source-verified history query/export and raw load API

Root inspected the relevant complete public bodies and charged two whole sources/1452lines at HEAD75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7; no project imports/runtime or source/index changes. Main consumes prose without a sixth source.

- `src/townlet/training/historical_checkpoint.py`: 675lines, SHA256 `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`.
- `src/townlet/training/checkpoint_utils.py`: 777lines, SHA256 `591040896a3e83df23912b2167e6d885abd0b949debfd754ddd23193da9937df`.

HistoricalReplayArchive.query_rows(*,offset:int,limit:int) returns cloned Mapping[str,Tensor] inspection rows. The canonical total key is exactly `rewards` (alongside observations/actions/next_observations/dones). Components use rewards_extrinsic/intrinsic/shaping and their *_present bool masks; absent components are not reconstructed total rewards. Empty archives can return {}.

`archive.export(destination:Path)->ArchiveExportReceipt` accepts the Path positionally. Parent must already exist; existing destination/symlink refuses. It writes/fsyncs temporary native artifact, reloads/verifies canonical state digest, atomically links without clobber, fsyncs parent. Receipt fields are destination, source_digest, row_count, output_digest. `.source_digest` equals archive.source_digest (canonical state identity), distinct from `.output_digest` artifact bytes.

Exact loader import: `from townlet.training.checkpoint_utils import safe_torch_load`. Signature `safe_torch_load(checkpoint_path:Path|str,*,map_location:torch.device|str|None=None,allow_unsafe_pickle:bool=False)->Any`. For already trusted project-native fixtures use explicit `safe_torch_load(path,map_location="cpu",allow_unsafe_pickle=True)`. It directly returns torch.load(...,weights_only=False); it does not wrap/populate a new envelope or unwrap population_state. A native-dict fixture therefore returns that original dict; the function itself does not guarantee a mapping for arbitrary input. Preserve existing artifact bytes/source identity and use the actual native nesting.
