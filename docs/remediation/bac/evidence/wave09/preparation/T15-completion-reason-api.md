# Source-verified runner completion literal

Root read complete `src/townlet/training/episode.py`:20lines, SHA256 `d9f93e2b0551f04ac882ffc7e4a775d34352626af3e868679c00a962f52c00a7`, at HEAD75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7. No imports/runtime or source/index changes. Main author consumes this prose without opening a sixth source.

The exact declared type is `RunnerCompletionReason = Literal["cap", "budget", "shutdown", "checkpoint"]` at line9. The external episode-cap literal is therefore `"cap"`; use `population.flush_episode(reason="cap")` according to the public signature already verified in POP. Internal `CompletionReason` additionally includes `authored_terminal` and `retirement`; these are not declared runner reasons. This20-line alias source alone does not prove dynamic validation or flush/done behavior; the main author already owns POP source for those semantics.
