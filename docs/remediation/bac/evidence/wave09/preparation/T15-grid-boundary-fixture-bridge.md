# Coordinator source-verified grid fixture bridge

Root read complete selected producers:2files/679lines at HEAD75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7. No imports/runtime, source/index edits, or extra read by main author.

- `src/townlet/substrate/grid2d.py`: 473lines, SHA256 `d17bcd2870be1168ce27aa23f153fdf1b97134e0d6e0b124135557dce696475b`.
- `src/townlet/environment/action_mask_builder.py`: 206lines, SHA256 `5d02f08f94c68bbd63b4491a5ed00a432a3fbadbec6b9a02572d544bfbcb7174`.

Grid2DSubstrate coordinates are `[x,y]`, top-left `[0,0]`, x right/y down, extents `0<=x<width`, `0<=y<height` with positive width/height. Public `position_dim` is2 and `position_dtype` is torch.long. Public initializer signature is `initialize_positions(self,num_agents:int,device:torch.device,*,generator:torch.Generator|None)->torch.Tensor`; it returns long[N,2] using independent x/y randint ranges. Thus zeros[N,2] is a valid deterministic reachable corner spawn for any declared positive grid extents.

For a controlled test fixture that needs reset-consistent observations, temporarily replace the selected grid instance's public `initialize_positions` method before population construction/reset with a test-local callable of `(num_agents,device,*,generator)` returning `torch.zeros((num_agents,2),dtype=torch.long,device=device)`. This is a labelled deterministic public-initializer fixture, not a claimed authored YAML spawn option and not a replay-mask fabrication. Keep actual ENV reset/step and ActionMaskBuilder. It avoids inventing a public observation-refresh method or editing live position after an observation was captured. ENV supplier receipt separately owns the actual reset call, which main already consumes as prose.

ActionMaskBuilder.build receives current positions. With rectangular extents, y==0 disables every movement action whose delta_y<0; x==0 disables delta_x<0; height-1/width-1 similarly disable positive directions. It starts from the composed base mask and applies these current-state constraints, then terminal dones mask all actions last. Use the real action record.id/delta and actual env.get_action_masks(), not guessed names/ordinals. On the authored clamp-grid fixture this proves top-left negative-axis moves are state-illegal while a separately authored globally disabled action remains a different control. No broader boundary-mode claim is made.
