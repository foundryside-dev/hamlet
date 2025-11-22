# P2-SUCCESS-1: Error Messages Lack Fuzzy Matching for Typos

**Priority:** P2 (Minor - UX Enhancement)
**Category:** Success Criteria (Error Handling)
**Estimated Effort:** 2-3 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

Compiler error messages use basic `difflib.get_close_matches()` for typo suggestions, which has limitations. More sophisticated fuzzy matching (Levenshtein distance) would improve UX.

**Current Implementation:**
```python
# src/townlet/universe/compiler.py
suggestions = difflib.get_close_matches(invalid_name, valid_names, n=3, cutoff=0.6)
```

**Limitations:**
- Only suggests exact substring matches
- Cutoff threshold may miss obvious typos
- No distance ranking (suggestions not ordered by similarity)

**Example:**
```yaml
# User types: agent.bar.helth
CompilationError: Unknown variable: agent.bar.helth
  Did you mean: agent.bar.health?
```

**Better suggestion (with Levenshtein):**
```
CompilationError: Unknown variable: agent.bar.helth
  Did you mean:
    - agent.bar.health (distance: 1)
    - agent.bar.wealth (distance: 2)
```

**Impact:**
- **Low priority:** Current suggestions work for simple typos
- **Nice-to-have:** Better UX for users unfamiliar with schema

**Evidence:**
- Agent 9 (Success Criteria) report, section SUCCESS-1
- Current implementation at `src/townlet/universe/compiler.py`

---

## How to Fix

### Step 1: Add Levenshtein Distance Utility (30 minutes)

**File:** `src/townlet/utils/fuzzy_match.py` (NEW)

```python
"""Fuzzy matching utilities for error messages."""

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (insertions, deletions, substitutions)

    Example:
        >>> levenshtein_distance("helth", "health")
        1
        >>> levenshtein_distance("satation", "satiation")
        2
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    # Dynamic programming table
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def find_closest_matches(
    target: str,
    candidates: list[str],
    max_suggestions: int = 3,
    max_distance: int = 3
) -> list[tuple[str, int]]:
    """Find closest matching strings using Levenshtein distance.

    Args:
        target: The misspelled string
        candidates: List of valid strings to match against
        max_suggestions: Maximum number of suggestions to return
        max_distance: Maximum edit distance to consider (filter out distant matches)

    Returns:
        List of (candidate, distance) tuples, sorted by distance

    Example:
        >>> candidates = ["health", "energy", "wealth", "stealth"]
        >>> find_closest_matches("helth", candidates)
        [("health", 1), ("wealth", 2), ("stealth", 3)]
    """
    # Compute distances for all candidates
    distances = [(candidate, levenshtein_distance(target, candidate)) for candidate in candidates]

    # Filter by max distance
    distances = [(c, d) for c, d in distances if d <= max_distance]

    # Sort by distance (closest first)
    distances.sort(key=lambda x: x[1])

    # Return top N suggestions
    return distances[:max_suggestions]


def format_suggestion_message(invalid: str, suggestions: list[tuple[str, int]]) -> str:
    """Format typo suggestions into error message.

    Args:
        invalid: The invalid string user provided
        suggestions: List of (candidate, distance) tuples

    Returns:
        Formatted error message with suggestions

    Example:
        >>> suggestions = [("health", 1), ("wealth", 2)]
        >>> format_suggestion_message("helth", suggestions)
        "Unknown: 'helth'\\nDid you mean:\\n  - health (distance: 1)\\n  - wealth (distance: 2)"
    """
    if not suggestions:
        return f"Unknown: '{invalid}'"

    lines = [f"Unknown: '{invalid}'", "Did you mean:"]
    for candidate, distance in suggestions:
        lines.append(f"  - {candidate} (distance: {distance})")

    return "\n".join(lines)
```

### Step 2: Update Compiler Error Messages (1 hour)

**File:** `src/townlet/universe/compiler.py`

**Replace difflib usage with Levenshtein:**

```python
from townlet.utils.fuzzy_match import find_closest_matches, format_suggestion_message

class Stage3_CrossValidation:
    def validate_variable_reference(self, path: str):
        """Validate VFS variable path exists."""
        # ... existing validation logic ...

        if not self.is_valid_path(path):
            # OLD:
            # suggestions = difflib.get_close_matches(path, valid_paths, n=3, cutoff=0.6)
            # msg = f"Unknown variable: {path}\nDid you mean: {suggestions[0]}?"

            # NEW:
            suggestions = find_closest_matches(
                target=path,
                candidates=valid_paths,
                max_suggestions=3,
                max_distance=3
            )
            msg = format_suggestion_message(path, suggestions)
            raise CompilationError(msg, location=self.current_location)
```

**Apply to all error sites:**
- Variable path validation
- Effect name validation
- Item type validation
- VFS profile validation
- Command type validation

### Step 3: Add Tests (1 hour)

**File:** `tests/test_townlet/unit/utils/test_fuzzy_match.py` (NEW)

```python
"""Tests for fuzzy matching utilities."""

import pytest
from townlet.utils.fuzzy_match import (
    levenshtein_distance,
    find_closest_matches,
    format_suggestion_message
)


def test_levenshtein_distance_identical():
    """Identical strings have distance 0."""
    assert levenshtein_distance("hello", "hello") == 0


def test_levenshtein_distance_single_substitution():
    """Single character substitution."""
    assert levenshtein_distance("helth", "health") == 1


def test_levenshtein_distance_multiple_edits():
    """Multiple insertions/deletions."""
    assert levenshtein_distance("satation", "satiation") == 2


def test_find_closest_matches_exact_match():
    """Exact match returns distance 0."""
    candidates = ["health", "energy", "wealth"]
    matches = find_closest_matches("health", candidates)
    assert matches[0] == ("health", 0)


def test_find_closest_matches_typo():
    """Close typo returns low distance."""
    candidates = ["health", "energy", "wealth", "stealth"]
    matches = find_closest_matches("helth", candidates)

    assert len(matches) >= 1
    assert matches[0][0] == "health"
    assert matches[0][1] == 1  # Distance 1


def test_find_closest_matches_max_distance_filter():
    """Distant matches filtered out."""
    candidates = ["health", "energy", "zzzzzz"]
    matches = find_closest_matches("helth", candidates, max_distance=2)

    # "zzzzzz" should be filtered (distance > 2)
    assert all(d <= 2 for _, d in matches)


def test_find_closest_matches_sorted_by_distance():
    """Matches sorted by increasing distance."""
    candidates = ["health", "wealth", "stealth"]
    matches = find_closest_matches("helth", candidates)

    # Should be sorted: health (1), wealth (2), stealth (3)
    distances = [d for _, d in matches]
    assert distances == sorted(distances)


def test_format_suggestion_message_single():
    """Format message with single suggestion."""
    suggestions = [("health", 1)]
    msg = format_suggestion_message("helth", suggestions)

    assert "Unknown: 'helth'" in msg
    assert "Did you mean:" in msg
    assert "health (distance: 1)" in msg


def test_format_suggestion_message_multiple():
    """Format message with multiple suggestions."""
    suggestions = [("health", 1), ("wealth", 2)]
    msg = format_suggestion_message("helth", suggestions)

    assert "health (distance: 1)" in msg
    assert "wealth (distance: 2)" in msg


def test_format_suggestion_message_empty():
    """Format message with no suggestions."""
    msg = format_suggestion_message("zzz", [])
    assert msg == "Unknown: 'zzz'"
```

### Step 4: Integration Test (30 minutes)

**File:** `tests/test_townlet/unit/universe/test_error_messages.py`

Add test verifying compiler error messages use fuzzy matching:

```python
def test_compiler_suggests_close_variable_typo():
    """Verify compiler suggests corrections for variable typos."""
    config = {
        "vfs_profiles": {
            "agent_profile": {
                "health": {"type": "float", "default": 100.0}
            }
        }
    }

    # Create expression with typo: "helth" instead of "health"
    expr_with_typo = "agent.vfs.helth + 10.0"

    with pytest.raises(CompilationError) as exc_info:
        compile_expression(expr_with_typo, config)

    error_msg = str(exc_info.value)

    # Should suggest "health" with distance
    assert "Unknown: 'agent.vfs.helth'" in error_msg
    assert "Did you mean:" in error_msg
    assert "health (distance: 1)" in error_msg
```

---

## Acceptance Criteria

- [ ] Levenshtein distance utility implemented
- [ ] Compiler uses fuzzy matching for all error messages
- [ ] Suggestions include edit distance
- [ ] Suggestions sorted by increasing distance
- [ ] Max distance filter prevents irrelevant suggestions
- [ ] Tests verify fuzzy matching logic
- [ ] Integration test confirms compiler error messages improved

---

## Files to Modify/Create

1. `src/townlet/utils/fuzzy_match.py` (NEW) - Levenshtein distance utilities
2. `src/townlet/universe/compiler.py` - Replace difflib with fuzzy matching
3. `tests/test_townlet/unit/utils/test_fuzzy_match.py` (NEW) - Unit tests
4. `tests/test_townlet/unit/universe/test_error_messages.py` - Integration test

---

## Related Issues

- Related: P2-DOC-9 (edge case policies - document error message quality)
- Blocks: None (UX enhancement)

---

## Notes

- **Low priority:** Current difflib suggestions work for simple typos
- **Quick win:** Levenshtein implementation is ~50 lines
- **Alternative:** Could use external library like `python-Levenshtein` for C-optimized implementation
- **Future enhancement:** Could add context-aware suggestions (suggest variables from current scope first)
- Consider making max_distance configurable (stricter for production, looser for dev)
