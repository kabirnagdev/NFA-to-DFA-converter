"""
Unit tests for Automata Simulator (core/simulator.py).
"""

import itertools
import pytest

from core.nfa import NFA
from core.conversion import SubsetConstructionEngine
from core.simulator import AutomataSimulator


@pytest.fixture
def builtin_automata():
    """Create the built-in course example NFA and converted DFA."""
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
    res = engine.convert()
    return nfa, res.dfa


def test_builtin_example_strings(builtin_automata):
    """
    Verify specified test strings from course requirements:
      01  -> Accepted
      101 -> Accepted
      001 -> Accepted
      10  -> Rejected
      111 -> Rejected
      010 -> Rejected
      ""  -> Rejected
    """
    nfa, dfa = builtin_automata

    test_cases = [
        ("01", True),
        ("101", True),
        ("001", True),
        ("10", False),
        ("111", False),
        ("010", False),
        ("", False),
    ]

    for test_str, expected in test_cases:
        cmp_res = AutomataSimulator.compare(nfa, dfa, test_str)
        assert cmp_res.is_equivalent is True, f"Mismatch on string '{test_str}'"
        assert cmp_res.nfa_result.is_accepted == expected, f"NFA failed on '{test_str}'"
        assert cmp_res.dfa_result.is_accepted == expected, f"DFA failed on '{test_str}'"


def test_invalid_symbol_rejection(builtin_automata):
    """String with symbol outside alphabet must be rejected with validation message."""
    nfa, _ = builtin_automata
    valid, err = AutomataSimulator.validate_string(nfa.alphabet, "0102")
    assert valid is False
    assert "not in alphabet" in err
    assert "'2'" in err


def test_empty_string_acceptance():
    """Verify that an automaton with initial state as final accepts the empty string."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        initial_state="q0",
        final_states=["q0"],  # q0 is final
        transitions={
            ("q0", "a"): {"q1"},
            ("q1", "b"): {"q0"},
        },
    )
    engine = SubsetConstructionEngine(nfa)
    dfa = engine.convert().dfa

    cmp_res = AutomataSimulator.compare(nfa, dfa, "")
    assert cmp_res.is_equivalent is True
    assert cmp_res.nfa_result.is_accepted is True
    assert cmp_res.dfa_result.is_accepted is True


def test_exhaustive_language_equivalence(builtin_automata):
    """
    Generate all binary strings up to length 6 (2^0 + ... + 2^6 = 127 strings).
    Verify that NFA and DFA decisions match on 100% of tested strings.
    """
    nfa, dfa = builtin_automata

    all_strings = [""]
    for length in range(1, 7):
        for combo in itertools.product(["0", "1"], repeat=length):
            all_strings.append("".join(combo))

    assert len(all_strings) == 127

    for test_str in all_strings:
        cmp_res = AutomataSimulator.compare(nfa, dfa, test_str)
        assert cmp_res.is_equivalent is True, f"NFA/DFA mismatch on string: {test_str}"
        # If it ends with '01', it must be accepted; otherwise rejected
        expected = test_str.endswith("01")
        assert cmp_res.dfa_result.is_accepted == expected
