Title: NetworkFactory.build_recurrent hardcodes enable_temporal_features=False

Severity: medium
Status: fixed

Subsystem: agent/network-factory
Affected Version/Branch: main

Affected Files:
- `src/townlet/agent/network_factory.py:73`

Description:
- When building the recurrent network from BrainConfig, the factory always passed `enable_temporal_features=False`.
- The environment may include temporal features in the observation (time_sin, time_cos, progress), and code elsewhere passes the env flag when constructing networks directly.

Reproduction:
- Use brain_config path; env with temporal features; network constructed via factory will ignore them.

Expected Behavior:
- Factory should accept `enable_temporal_features: bool` or infer from env metadata and pass through.

Actual Behavior:
- Flag was hardcoded to False.

Root Cause:
- Phase 2 shortcut left in code.

Fix Applied:
- Modified `build_recurrent` to detect temporal features from `observation_spec` parameter
- Checks for presence of "obs_temporal" field in observation_spec
- Defaults to False when observation_spec is None
- See commit in RC-Prep branch

Implementation:
- `src/townlet/agent/network_factory.py:125-132` - Added temporal feature detection logic
- Improved docstring to document automatic detection behavior
- Added comprehensive test coverage in `tests/test_townlet/unit/agent/test_network_factory.py::test_build_recurrent_temporal_features_detection`

Test Coverage:
- Network with temporal features (enable_temporal_features=True)
- Network without temporal features (enable_temporal_features=False)
- Network with None observation_spec (defaults to False)
- All tests pass, network_factory.py achieves 100% coverage

Migration Impact:
- No breaking changes - observation_spec parameter was already optional
- Automatic detection improves ergonomics without requiring callers to change

Owner: agent
