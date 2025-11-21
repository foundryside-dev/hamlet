# [COMP-13] Typo Suggestions in Error Messages

**Priority:** P2 (Minor)
**Category:** Compiler
**Status:** MISSING
**Effort:** 4 hours

## Description

Compiler validation errors don't suggest corrections for typos. When user misspells a bar name, affordance name, or VFS variable, error message just says "not found" without suggesting similar names. This creates poor developer experience for simple typos.

## Current State

**Current error messages:**
```
ValidationError: Bar 'helth' not found in bars configuration.
```

**Desired error messages:**
```
ValidationError: Bar 'helth' not found in bars configuration.
  Available bars: energy, health, satiation, hygiene, money, mood, social, fitness
  Did you mean: 'health'?
```

**Affected validation points:**
- Bar name references (cascades, affordances, DAC config)
- Affordance name references (cues, spawn positions)
- VFS variable references (expressions, effects commands)
- Item type references (spawn rules, interactions)
- VFS profile references (item definitions) - partially covered in COMP-17

## Required Implementation

### 1. Levenshtein Distance Implementation (1-2 hours)

**File:** `src/townlet/universe/validation.py` (new utility module)

**Implementation:**
```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def suggest_typo_fixes(
    typo: str,
    candidates: Iterable[str],
    max_distance: int = 2,
    max_suggestions: int = 3
) -> List[str]:
    """Find closest matches for a typo using Levenshtein distance."""
    distances = [
        (candidate, levenshtein_distance(typo.lower(), candidate.lower()))
        for candidate in candidates
    ]

    # Filter by max distance and sort by distance
    matches = [
        candidate for candidate, distance in distances
        if distance <= max_distance
    ]
    matches.sort(key=lambda c: levenshtein_distance(typo.lower(), c.lower()))

    return matches[:max_suggestions]
```

### 2. Enhanced Error Messages (2-3 hours)

**File:** `src/townlet/universe/compiler.py`

**Integrate typo suggestions into validation errors:**

```python
from townlet.universe.validation import suggest_typo_fixes

def _validate_bar_references(self):
    """Validate all bar references with typo suggestions."""
    available_bars = set(self.bars_config.bars.keys())

    # Check cascade references
    for cascade in self.cascades_config.cascades:
        if cascade.trigger_bar not in available_bars:
            suggestions = suggest_typo_fixes(cascade.trigger_bar, available_bars)
            error_msg = f"Cascade references undefined bar '{cascade.trigger_bar}'\n"
            error_msg += f"  Available bars: {', '.join(sorted(available_bars))}"
            if suggestions:
                error_msg += f"\n  Did you mean: {', '.join(suggestions)}?"
            raise ValidationError(error_msg)

        if cascade.affected_bar not in available_bars:
            # Similar error handling...
            pass

def _validate_affordance_references(self):
    """Validate affordance references with typo suggestions."""
    available_affordances = set(self.affordances_config.affordances.keys())

    # Similar pattern for affordance validation...

def _validate_vfs_variable_references(self):
    """Validate VFS variable references with typo suggestions."""
    available_variables = set()
    if self.compiled_vfs_profiles:
        if self.compiled_vfs_profiles.global_profile:
            available_variables.update(
                self.compiled_vfs_profiles.global_profile.variables.keys()
            )
        # Collect agent and item profile variables...

    # Check expression variable references (when AST exists)...
```

### 3. Testing (1-2 hours)

**File:** `tests/test_townlet/unit/universe/test_typo_suggestions.py` (new)

**Test cases:**
```python
def test_levenshtein_distance():
    """Test Levenshtein distance computation."""
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("health", "helth") == 1
    assert levenshtein_distance("energy", "enrgy") == 1

def test_suggest_typo_fixes():
    """Test typo suggestion generation."""
    candidates = ["health", "energy", "satiation", "hygiene"]
    suggestions = suggest_typo_fixes("helth", candidates)
    assert "health" in suggestions  # Edit distance = 1

    suggestions = suggest_typo_fixes("enrgy", candidates)
    assert "energy" in suggestions  # Edit distance = 1

def test_bar_reference_typo_error_message():
    """Test enhanced error message for bar reference typo."""
    config = create_invalid_config_with_bar_typo()  # References "helth"

    with pytest.raises(ValidationError) as exc_info:
        UniverseCompiler.compile(config)

    error_msg = str(exc_info.value)
    assert "helth" in error_msg
    assert "Did you mean" in error_msg
    assert "health" in error_msg

def test_typo_suggestions_case_insensitive():
    """Test typo suggestions ignore case."""
    candidates = ["Health", "Energy"]
    suggestions = suggest_typo_fixes("HELTH", candidates)
    assert "Health" in suggestions

def test_no_suggestions_for_very_different_names():
    """Test no suggestions when typo too different."""
    candidates = ["health", "energy"]
    suggestions = suggest_typo_fixes("foobar", candidates, max_distance=2)
    assert len(suggestions) == 0
```

## Acceptance Criteria

- [ ] Levenshtein distance function implemented and tested
- [ ] `suggest_typo_fixes()` utility function implemented
- [ ] Bar reference validation includes typo suggestions
- [ ] Affordance reference validation includes typo suggestions
- [ ] VFS variable reference validation includes typo suggestions (when AST exists)
- [ ] Item type reference validation includes typo suggestions
- [ ] Profile reference validation includes typo suggestions (COMP-17)
- [ ] Error messages list available options and suggest corrections
- [ ] Suggestions are case-insensitive
- [ ] Max 3 suggestions shown per error
- [ ] Only suggest if edit distance ≤ 2
- [ ] 15+ tests covering distance computation, suggestion generation, and error messages

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-compiler.md
**Related Requirements:** COMP-17 (profile validation uses typo suggestions)

## Implementation Notes

**Why P2 (not P1/P0):** Developer experience enhancement, not a functional bug. Current error messages work, just not as helpful as they could be.

**Levenshtein Distance:**
- Classic edit distance algorithm (insertions, deletions, substitutions)
- O(n×m) time complexity (n, m = string lengths)
- Standard implementation, well-tested in other projects

**Suggestion Strategy:**
- Max edit distance = 2 (catches most typos: transpositions, missing letters, extra letters)
- Case-insensitive matching (user shouldn't care about case when fixing typo)
- Max 3 suggestions (avoid overwhelming user with too many options)
- Sort by distance (closest matches first)

**Integration Points:**
1. **Compiler validation errors** (primary use case):
   - Bar references in cascades, affordances, DAC config
   - Affordance references in cues, spawn rules
   - VFS variable references in expressions
   - Item type references in spawn rules
   - Profile references in item definitions

2. **Runtime errors** (future enhancement):
   - Effects command path resolution errors
   - VFS variable lookup errors
   - Could add suggestions to runtime errors too

**Error Message Format:**
```
ValidationError: {Type} '{wrong_name}' not found in {context}.
  Available {type}s: {list of valid names}
  Did you mean: {suggestion1}, {suggestion2}, {suggestion3}?
```

**Example:**
```
ValidationError: Bar 'helth' not found in bars configuration.
  Available bars: energy, health, satiation, hygiene, money, mood, social, fitness
  Did you mean: 'health'?
```

**Edge Cases:**
- Empty candidates list (no suggestions possible)
- Typo matches multiple candidates equally (show all matches)
- No close matches (show available options, no "Did you mean" line)
- Very long candidate lists (limit to top 3 suggestions)

## References

- Utility module: `src/townlet/universe/validation.py` (to be created)
- Compiler integration: `src/townlet/universe/compiler.py` (enhance validation errors)
- Test file: `tests/test_townlet/unit/universe/test_typo_suggestions.py` (to be created)
- Related: COMP-17 (profile validation), general validation error UX
