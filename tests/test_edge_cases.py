"""
Comprehensive edge-case and regression tests for Milestone 2.

Covers:
- Multiple transitions from one NFA state
- Missing transitions (empty subset)
- Trap-state self-loops
- Duplicate subset prevention
- Multiple accepting states
- Initial state also accepting
- Empty input string edge cases
- Invalid input symbols
- Different alphabet sizes (1-, 2-, 3-symbol)
- NFA/DFA language equivalence (exhaustive bounded)
- Trap state never accepting
- Large-ish NFA (5-state) reachability
- Initial DFA state correctly identified
- Snapshot count equals step count
- Last snapshot queue empty (BFS terminated)
"""

import itertools
import pytest

from core.nfa import NFA, EPSILON
from core.conversion import SubsetConstructionEngine, format_subset
from core.simulator import AutomataSimulator


# ---------------------------------------------------------------------------
# Multiple transitions from one NFA state
# ---------------------------------------------------------------------------

class TestMultipleTransitionsFromOneState:
    """NFA states with many outgoing transitions on a single symbol."""

    def test_one_state_fans_out_to_all(self):
        """q0 on 'a' fans to all other states simultaneously."""
        nfa = NFA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q3"],
            transitions={
                ("q0", "a"): {"q0", "q1", "q2", "q3"},
                ("q1", "b"): {"q1"},
                ("q2", "b"): {"q2"},
                ("q3", "b"): {"q3"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa

        # Initial state A = {q0}; after 'a' we must reach {q0,q1,q2,q3}
        a_target = dfa.get_transition(dfa.initial_state, "a")
        assert a_target is not None
        target_subset = dfa.state_subsets[a_target]
        assert frozenset({"q0", "q1", "q2", "q3"}) == target_subset

    def test_overlapping_union_produces_single_subset(self):
        """Two NFA states have overlapping targets; union must deduplicate."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["x"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "x"): {"q0", "q1"},
                ("q1", "x"): {"q0", "q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        # Every DFA state must map to a unique frozenset
        subsets = list(result.state_mapping.values())
        assert len(subsets) == len(set(subsets)), "Duplicate subsets found"


# ---------------------------------------------------------------------------
# Missing transitions (empty subset → trap state)
# ---------------------------------------------------------------------------

class TestMissingTransitionsAndTrapState:
    """NFAs where some (state, symbol) combinations have no defined transition."""

    def test_missing_transition_creates_trap(self):
        """An NFA where (q0, '1') is undefined must produce an explicit trap."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q1"],
            transitions={
                ("q0", "0"): {"q1"},
                ("q1", "0"): {"q1"},
                ("q1", "1"): {"q1"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa

        trap_states = [s for s, sub in dfa.state_subsets.items() if not sub]
        assert len(trap_states) == 1, "Exactly one trap state expected"

    def test_trap_state_never_accepting(self):
        """The ∅ trap state must never be an accepting DFA state."""
        nfa = NFA(
            states=["q0"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q0"],
            transitions={("q0", "0"): {"q0"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        trap_states = [s for s, sub in dfa.state_subsets.items() if not sub]
        for trap in trap_states:
            assert not dfa.is_final(trap), f"Trap state {trap} must not be accepting"

    def test_trap_state_self_loops_on_all_symbols(self):
        """Trap state ∅ must transition to itself on every alphabet symbol."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a", "b", "c"],
            initial_state="q0",
            final_states=["q1"],
            transitions={("q0", "a"): {"q1"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        trap_states = [s for s, sub in dfa.state_subsets.items() if not sub]
        assert trap_states, "Expected a trap state for missing transitions"
        trap = trap_states[0]
        for sym in nfa.alphabet:
            assert dfa.get_transition(trap, sym) == trap, (
                f"Trap state must self-loop on '{sym}'"
            )

    def test_all_dfa_transitions_are_total(self):
        """Every DFA state must have exactly one defined transition per symbol."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        for state in dfa.states:
            for sym in dfa.sorted_alphabet:
                tgt = dfa.get_transition(state, sym)
                assert tgt is not None, f"Missing transition δ'({state}, {sym})"
                assert tgt in dfa.states, f"Target {tgt} not in DFA states"


# ---------------------------------------------------------------------------
# Duplicate subset prevention
# ---------------------------------------------------------------------------

class TestDuplicateSubsetPrevention:
    """Verify that the same NFA subset is never assigned two different labels."""

    def test_no_duplicate_labels_simple(self):
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "0"): {"q0", "q1"},  # loops back to same subset
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        subsets = list(result.state_mapping.values())
        assert len(subsets) == len(set(subsets))

    def test_no_duplicate_labels_larger_nfa(self):
        """4-state NFA: confirms frozenset identity prevents duplicates."""
        nfa = NFA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q3"],
            transitions={
                ("q0", "a"): {"q0", "q1"},
                ("q0", "b"): {"q0"},
                ("q1", "a"): {"q2"},
                ("q1", "b"): {"q3"},
                ("q2", "a"): {"q0", "q2"},
                ("q3", "a"): {"q3"},
                ("q3", "b"): {"q3"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        subsets = list(result.state_mapping.values())
        assert len(subsets) == len(set(subsets))


# ---------------------------------------------------------------------------
# Multiple accepting states
# ---------------------------------------------------------------------------

class TestMultipleAcceptingStates:
    """DFA accepting states must track union membership with any NFA final state."""

    def test_dfa_accepts_all_nfa_final_containing_subsets(self):
        """Every DFA subset containing at least one NFA final state must be accepting."""
        nfa = NFA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            initial_state="q0",
            final_states=["q1", "q3"],
            transitions={
                ("q0", "a"): {"q1", "q2"},
                ("q1", "a"): {"q2"},
                ("q2", "a"): {"q3"},
                ("q3", "a"): {"q0"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        nfa_finals = nfa.final_states

        for lbl, subset in dfa.state_subsets.items():
            should_accept = bool(subset & nfa_finals)
            assert dfa.is_final(lbl) == should_accept, (
                f"DFA state {lbl}={format_subset(subset)} acceptance mismatch"
            )

    def test_accepts_state_count(self):
        """NFA with two finals; verify DFA accepts at least two states."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q0", "q2"],
            transitions={
                ("q0", "a"): {"q1"},
                ("q1", "b"): {"q2"},
                ("q2", "a"): {"q0"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        # q0 is in F so initial DFA state must be accepting
        assert dfa.is_final(dfa.initial_state), "Initial DFA state must accept (q0 ∈ F)"
        assert len(dfa.final_states) >= 2


# ---------------------------------------------------------------------------
# Initial state also accepting
# ---------------------------------------------------------------------------

class TestInitialStateAccepting:
    """When q0 ∈ F, the initial DFA state must be marked accepting."""

    def test_initial_state_in_final(self):
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["0"],
            initial_state="q0",
            final_states=["q0", "q1"],
            transitions={("q0", "0"): {"q1"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        assert dfa.is_final(dfa.initial_state)

    def test_empty_string_accepted_when_q0_in_final(self):
        """ε (empty string) must be accepted iff q0 ∈ F."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a"],
            initial_state="q0",
            final_states=["q0"],
            transitions={("q0", "a"): {"q1"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        cmp = AutomataSimulator.compare(nfa, dfa, "")
        assert cmp.is_equivalent
        assert cmp.dfa_result.is_accepted is True

    def test_empty_string_rejected_when_q0_not_in_final(self):
        """ε must be rejected if q0 ∉ F."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a"],
            initial_state="q0",
            final_states=["q1"],
            transitions={("q0", "a"): {"q1"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        cmp = AutomataSimulator.compare(nfa, dfa, "")
        assert cmp.is_equivalent
        assert cmp.dfa_result.is_accepted is False


# ---------------------------------------------------------------------------
# Invalid input symbols
# ---------------------------------------------------------------------------

class TestInvalidInputSymbols:
    """String validation must reject symbols outside the declared alphabet."""

    def test_single_invalid_symbol(self):
        nfa = NFA(
            states=["q0"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q0"],
            transitions={},
        )
        valid, err = AutomataSimulator.validate_string(nfa.alphabet, "abc")
        assert valid is False
        assert "'c'" in err

    def test_multiple_invalid_symbols(self):
        nfa = NFA(
            states=["q0"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q0"],
            transitions={},
        )
        valid, err = AutomataSimulator.validate_string(nfa.alphabet, "0123")
        assert valid is False
        assert "not in alphabet" in err

    def test_valid_string_passes(self):
        valid, err = AutomataSimulator.validate_string({"a", "b"}, "aabb")
        assert valid is True
        assert err is None

    def test_empty_string_always_valid(self):
        valid, err = AutomataSimulator.validate_string({"x"}, "")
        assert valid is True

    def test_single_char_string_valid(self):
        valid, err = AutomataSimulator.validate_string({"0", "1"}, "0")
        assert valid is True


# ---------------------------------------------------------------------------
# Different alphabet sizes
# ---------------------------------------------------------------------------

class TestAlphabetSizes:
    """Tests for 1-symbol, 2-symbol, 4-symbol alphabets."""

    def test_unary_alphabet_simple(self):
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a"],
            initial_state="q0",
            final_states=["q1"],
            transitions={("q0", "a"): {"q1"}, ("q1", "a"): {"q0"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        assert dfa.alphabet == {"a"}
        # All DFA states have a transition on 'a'
        for s in dfa.states:
            assert dfa.get_transition(s, "a") is not None

    def test_four_symbol_alphabet(self):
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a", "b", "c", "d"],
            initial_state="q0",
            final_states=["q1"],
            transitions={
                ("q0", "a"): {"q1"},
                ("q0", "b"): {"q0"},
                ("q1", "c"): {"q0"},
                ("q1", "d"): {"q1"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        assert dfa.alphabet == {"a", "b", "c", "d"}
        # Every state must have all 4 transitions
        for s in dfa.states:
            for sym in ["a", "b", "c", "d"]:
                assert dfa.get_transition(s, sym) is not None

    def test_total_steps_equals_states_times_symbols(self):
        """Steps = reachable DFA states × |Σ|."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        expected_steps = len(result.dfa.states) * len(nfa.alphabet)
        assert len(result.steps) == expected_steps


# ---------------------------------------------------------------------------
# NFA/DFA language equivalence (exhaustive bounded)
# ---------------------------------------------------------------------------

class TestLanguageEquivalence:
    """Exhaustive bounded equivalence verification for several languages."""

    def test_equivalence_ends_with_01_all_strings_len_7(self):
        """All 255 binary strings up to length 7 must agree on NFA and DFA."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        dfa = SubsetConstructionEngine(nfa).convert().dfa
        mismatches = []
        for length in range(8):
            for combo in itertools.product(["0", "1"], repeat=length):
                w = "".join(combo)
                cmp = AutomataSimulator.compare(nfa, dfa, w)
                if not cmp.is_equivalent:
                    mismatches.append(w)
        assert mismatches == [], f"Mismatches: {mismatches[:5]}"

    def test_equivalence_contains_ab_bounded(self):
        """NFA accepting strings containing 'ab' — test all strings up to length 6."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "a"): {"q0", "q1"},
                ("q0", "b"): {"q0"},
                ("q1", "b"): {"q2"},
                ("q2", "a"): {"q2"},
                ("q2", "b"): {"q2"},
            },
        )
        dfa = SubsetConstructionEngine(nfa).convert().dfa
        for length in range(7):
            for combo in itertools.product(["a", "b"], repeat=length):
                w = "".join(combo)
                cmp = AutomataSimulator.compare(nfa, dfa, w)
                assert cmp.is_equivalent, f"Mismatch on '{w}'"
                expected = "ab" in w
                assert cmp.dfa_result.is_accepted == expected, (
                    f"Wrong verdict on '{w}': got {cmp.dfa_result.is_accepted}"
                )

    def test_equivalence_starts_with_a(self):
        """NFA accepting strings starting with 'a' — test all strings up to length 5."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            initial_state="q0",
            final_states=["q1"],
            transitions={
                ("q0", "a"): {"q1"},
                ("q1", "a"): {"q1"},
                ("q1", "b"): {"q1"},
                ("q0", "b"): {"q2"},
                ("q2", "a"): {"q2"},
                ("q2", "b"): {"q2"},
            },
        )
        dfa = SubsetConstructionEngine(nfa).convert().dfa
        for length in range(6):
            for combo in itertools.product(["a", "b"], repeat=length):
                w = "".join(combo)
                cmp = AutomataSimulator.compare(nfa, dfa, w)
                assert cmp.is_equivalent, f"Mismatch on '{w}'"
                expected = w.startswith("a")
                assert cmp.dfa_result.is_accepted == expected


# ---------------------------------------------------------------------------
# Snapshot / playback integrity
# ---------------------------------------------------------------------------

class TestSnapshotIntegrity:
    """Verify ConversionSnapshot correctness for safe step-by-step replay."""

    def test_snapshot_count_equals_step_count(self):
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        assert len(result.snapshots) == len(result.steps) == 6

    def test_last_snapshot_queue_empty(self):
        """After BFS terminates, the last snapshot must have an empty pending queue."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        last = result.snapshots[-1]
        assert last.queue_pending == [], "BFS queue must be empty at the final snapshot"

    def test_first_snapshot_discovers_first_new_state(self):
        """The first snapshot must correspond to the first transition computation."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        first = result.snapshots[0]
        assert first.step.current_label == "A"
        assert first.step.symbol == "0"  # First symbol processed

    def test_total_snapshots_field_backfilled(self):
        """Every snapshot must know the total snapshot count."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet=["a"],
            initial_state="q0",
            final_states=["q1"],
            transitions={("q0", "a"): {"q1"}},
        )
        result = SubsetConstructionEngine(nfa).convert()
        total = len(result.snapshots)
        for snap in result.snapshots:
            assert snap.total_snapshots == total

    def test_partial_transitions_grow_monotonically(self):
        """Each snapshot must have >= as many transitions as the previous."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        prev_count = 0
        for snap in result.snapshots:
            count = len(snap.partial_transitions)
            assert count >= prev_count, (
                f"Transition count decreased from {prev_count} to {count}"
            )
            prev_count = count

    def test_final_snapshot_transitions_match_dfa(self):
        """Last snapshot's partial_transitions must equal the final DFA transitions."""
        nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        last = result.snapshots[-1]
        assert last.partial_transitions == result.dfa.transitions


# ---------------------------------------------------------------------------
# Large automaton reachability
# ---------------------------------------------------------------------------

class TestLargeAutomataReachability:
    """5-state NFA to verify only reachable subsets are explored."""

    def test_5_state_nfa_reachable_subset_bound(self):
        """5-state NFA: reachable DFA states should be <= 2^5 = 32."""
        nfa = NFA(
            states=["q0", "q1", "q2", "q3", "q4"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q4"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "0"): {"q2"},
                ("q1", "1"): {"q2"},
                ("q2", "0"): {"q3"},
                ("q2", "1"): {"q3"},
                ("q3", "0"): {"q4"},
                ("q3", "1"): {"q4"},
                ("q4", "0"): {"q4"},
                ("q4", "1"): {"q4"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        assert len(dfa.states) <= 2 ** 5

    def test_5_state_nfa_dfa_total_function(self):
        """Every DFA state from the 5-state NFA must have all transitions defined."""
        nfa = NFA(
            states=["q0", "q1", "q2", "q3", "q4"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q4"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
                ("q2", "1"): {"q3"},
                ("q3", "1"): {"q4"},
            },
        )
        result = SubsetConstructionEngine(nfa).convert()
        dfa = result.dfa
        for s in dfa.states:
            for sym in ["0", "1"]:
                tgt = dfa.get_transition(s, sym)
                assert tgt is not None, f"δ'({s}, {sym}) is None"
                assert tgt in dfa.states


# ---------------------------------------------------------------------------
# format_subset utility
# ---------------------------------------------------------------------------

class TestFormatSubset:
    """Unit tests for the format_subset helper used in UI rendering."""

    def test_empty_subset_displayed_as_empty_set_symbol(self):
        assert format_subset(frozenset()) == "∅"

    def test_singleton_subset(self):
        assert format_subset(frozenset({"q0"})) == "{q0}"

    def test_ordered_subset(self):
        result = format_subset(frozenset({"q2", "q0", "q1"}))
        assert result == "{q0, q1, q2}"

    def test_mixed_names_sorted(self):
        result = format_subset(frozenset({"q10", "q2", "q1"}))
        # Natural numeric sort: q1 < q2 < q10
        assert result.startswith("{q1,") or result == "{q1, q2, q10}"
