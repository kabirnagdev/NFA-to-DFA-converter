"""
Unit tests for Subset Construction Algorithm (core/conversion.py).
"""

import pytest
from core.nfa import NFA
from core.conversion import SubsetConstructionEngine, generate_state_label


def test_state_label_generation():
    """Verify state labeling adheres to A, B, C... convention."""
    assert generate_state_label(0) == "A"
    assert generate_state_label(1) == "B"
    assert generate_state_label(25) == "Z"
    assert generate_state_label(26) == "AA"
    assert generate_state_label(27) == "AB"


def test_builtin_example_conversion():
    """
    Test the standard course example: binary strings ending in '01'.
    NFA:
      Q = {q0, q1, q2}
      Sigma = {0, 1}
      q0 = q0
      F = {q2}
      delta(q0, 0) = {q0, q1}
      delta(q0, 1) = {q0}
      delta(q1, 1) = {q2}
      others = empty
    Expected DFA:
      A = {q0} (Initial)
      B = {q0, q1}
      C = {q0, q2} (Accepting)
      delta'(A, 0) = B, delta'(A, 1) = A
      delta'(B, 0) = B, delta'(B, 1) = C
      delta'(C, 0) = B, delta'(C, 1) = A
    """
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

    engine = SubsetConstructionEngine(nfa)
    result = engine.convert()
    dfa = result.dfa

    # Check state count
    assert len(dfa.states) == 3
    assert dfa.initial_state == "A"

    # Check state subsets
    assert dfa.state_subsets["A"] == frozenset({"q0"})
    assert dfa.state_subsets["B"] == frozenset({"q0", "q1"})
    assert dfa.state_subsets["C"] == frozenset({"q0", "q2"})

    # Check transitions
    assert dfa.get_transition("A", "0") == "B"
    assert dfa.get_transition("A", "1") == "A"
    assert dfa.get_transition("B", "0") == "B"
    assert dfa.get_transition("B", "1") == "C"
    assert dfa.get_transition("C", "0") == "B"
    assert dfa.get_transition("C", "1") == "A"

    # Check final states
    assert dfa.final_states == {"C"}
    assert dfa.is_final("C") is True
    assert dfa.is_final("A") is False
    assert dfa.is_final("B") is False

    # Check step trace
    assert len(result.steps) == 6  # 3 states x 2 symbols
    assert result.steps[0].current_label == "A"
    assert result.steps[0].symbol == "0"
    assert result.steps[0].target_label == "B"
    assert result.steps[0].is_new_state is True


def test_conversion_with_empty_subset_trap_state():
    """
    Verify that an NFA reaching an empty set generates an explicit
    trap state in the DFA, and that trap state loops to itself on all symbols.
    """
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "0"): {"q1"},
            # ("q0", "1") is empty
            ("q1", "0"): {"q1"},
            ("q1", "1"): {"q1"},
        },
    )

    engine = SubsetConstructionEngine(nfa)
    result = engine.convert()
    dfa = result.dfa

    # Must contain a trap state with empty frozenset
    trap_states = [st for st, subset in dfa.state_subsets.items() if len(subset) == 0]
    assert len(trap_states) == 1
    trap = trap_states[0]

    # Trap state must transition to itself on all alphabet symbols
    for sym in nfa.alphabet:
        assert dfa.get_transition(trap, sym) == trap

    # Trap state must not be accepting
    assert not dfa.is_final(trap)


def test_conversion_unreachable_nfa_states():
    """
    Verify that unreachable NFA states are not included in reachable DFA states.
    """
    nfa = NFA(
        states=["q0", "q1", "q_unreachable"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1", "q_unreachable"],
        transitions={
            ("q0", "0"): {"q1"},
            ("q0", "1"): {"q0"},
            ("q1", "0"): {"q1"},
            ("q1", "1"): {"q1"},
            ("q_unreachable", "0"): {"q_unreachable"},
        },
    )

    engine = SubsetConstructionEngine(nfa)
    result = engine.convert()
    dfa = result.dfa

    # No DFA state subset should contain q_unreachable
    for subset in dfa.state_subsets.values():
        assert "q_unreachable" not in subset


def test_multi_branch_nfa_conversion():
    """
    Test NFA with multiple branch paths from a state.
    """
    nfa = NFA(
        states=["q0", "q1", "q2", "q3"],
        alphabet=["a", "b"],
        initial_state="q0",
        final_states=["q3"],
        transitions={
            ("q0", "a"): {"q0", "q1", "q2"},
            ("q0", "b"): {"q0"},
            ("q1", "b"): {"q3"},
            ("q2", "a"): {"q3"},
        },
    )

    engine = SubsetConstructionEngine(nfa)
    result = engine.convert()
    dfa = result.dfa

    # Verify DFA is deterministic: every state has a target for 'a' and 'b'
    for st in dfa.states:
        for sym in ["a", "b"]:
            tgt = dfa.get_transition(st, sym)
            assert tgt is not None
            assert tgt in dfa.states
